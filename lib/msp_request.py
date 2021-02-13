
class Sbuf:
    # Important: `length` is _not_ the length of `buffer`, instead it's simply used with `bytes_remaining` to keep track
    # of how many bytes more you intend to write or, after calling `switch_to_reader`, how many are available to read.
    def __init__(self, buffer_length):
        self.buffer = bytearray(buffer_length)
        self.offset = 0
        self.length = 0

    def write_u8(self, b):
        self.buffer[self.offset] = b
        self.offset += 1

    # TODO: optimize and use slices.
    def write_data(self, data):
        for b in data:
            self.write_u8(b)

    def read_u8(self):
        b = self.buffer[self.offset]
        self.offset += 1
        return b

    # TODO: this looks wonky - it _doesn't_ advance self.offset but is always used in combination with `advance`, which does.
    # TODO: optimize to use slices.
    def read_data(self, data, length):
        for i in range(0, length):
            data[i] = self.buffer[self.offset + i]

    # TODO: roll `advance` into `read_data`.
    def advance(self, skip):
        self.offset += skip

    # TODO: is this needed?
    def reset(self):
        self.offset = 0
        self.length = 0

    # TODO: I suspect `reset_offset` and `set_length` are always used in combination.
    def reset_offset(self):
        self.offset = 0

    def set_length(self, length):
        assert length <= len(self.buffer)
        self.length = length

    def bytes_remaining(self):
        return self.length - self.offset

    def switch_to_reader(self):
        self.length = self.offset
        self.offset = 0


# TODO: are there sensible defaults for `cmd` etc. instead of `None`?
class MspPacket:
    def __init__(self, buffer_size):
        self.buf = Sbuf(buffer_size)
        self.cmd = None
        self.flags = None
        self.error = False
        self.direction = None


class MspError:
    VER_MISMATCH = 0
    CRC_ERROR = 1
    ERROR = 2


# There are a huge number of commands but for the moment these are the only ones we need to know.
class MspCommand:
    API_VERSION = 1
    MULTIPLE_MSP = 230


# TODO: come up with more consistent naming. Does it makes sense to have a separate `MspError`.
class MspResult:
    def __init__(self, command=0, payload=None, error=None):
        self.command = command
        self.payload = payload
        self.error = error


class MspPackage:
    _RX_BUF_SIZE = 64
    _TX_BUF_SIZE = 256

    _VERSION = 1
    _VER_SHIFT = 5
    _VER_MASK = 0x07
    ERROR_FLAG = 0x20
    START_FLAG = 0x10
    _SEQ_MASK = 0x0F

    def __init__(self):
        self.request_packet = MspPacket(self._RX_BUF_SIZE)
        self.response_packet = MspPacket(self._TX_BUF_SIZE)
        self.checksum = 0
        self.msp_started = False
        self.last_seq = 0

    def process_command(self):
        command = self.request_packet.cmd

        # For `MULTIPLE_MSP` one can't simply set the response `cmd` from the request `cmd`.
        assert command != MspCommand.MULTIPLE_MSP

        self.response_packet.cmd = command
        self.response_packet.error = False
        self.response_packet.buf.reset()

        success = False  # TODO: do something with request.

        if not success:
            self.send_error_response(MspError.ERROR, command)
            return

        self.response_packet.buf.switch_to_reader()

    def send_error_response(self, error, cmd):
        self.response_packet.cmd = cmd
        # TODO: should `error` be in `MspPacket` - ditto for other fields - are they all used for both request and response?
        self.response_packet.error = True
        self.response_packet.buf.reset()

        self.response_packet.buf.write_u8(error)
        self.response_packet.buf.switch_to_reader()

    def handle_frame(self, frame_buf):
        # TODO: I don't think `msp_started` needs to be set here. But perhaps it should warn that a new request
        #  has been started while we're still in the process of sending the response to the last command.
        if self.response_packet.buf.bytes_remaining() > 0:
            self.msp_started = False

        # All frames start with a header byte.
        # The header is 8 bits - vvvsnnnn - 3 version bit, 1 start bit and 4 sequence number bits.
        # * If the start bit is set then the header is followed by:
        #   * A payload length byte.
        #   * A command byte, i.e. a byte indicating the purpose of the complete message.
        #   The remainder of the frame is payload bytes (if payload length is greater than 0).
        # * If the start bit is not set then the rest of the frame is further payload data.
        # The very last byte (after payload length bytes have been accumulated) is a checksum byte.
        # If the message is very short then everything including the checksum may fit in a single frame.
        # A minimal message would be e.g. 0x30 0x00 0x01 0x01
        #                              header^ len^ cmd^ ^checksum
        # If len were greater than 0 then there would be payload bytes between cmd and checksum.
        header = frame_buf[0]
        version = (header >> self._VER_SHIFT) & self._VER_MASK

        if version != self._VERSION:
            return MspResult(error=MspError.VER_MISMATCH)

        seq_number = header & self._SEQ_MASK
        is_start = header & self.START_FLAG

        frame_offset = 1  # We've already taken off `header` so we start from 1.

        if is_start:
            msp_payload_size = frame_buf[1]
            command = frame_buf[2]
            frame_offset += 2

            self.request_packet.cmd = command
            self.request_packet.buf.reset_offset()
            self.request_packet.buf.set_length(msp_payload_size)

            # TODO: I don't think `checksum` needs to be a `self` field, you can get payload size and command below for the final calculation.
            self.checksum = msp_payload_size ^ command
            self.msp_started = True
        elif not self.msp_started:
            return None
        elif seq_number != (self.last_seq + 1) & self._SEQ_MASK:
            # Packet loss detected.
            self.msp_started = False
            return None

        self.last_seq = seq_number

        # If the source of `frame_buf` is S.BUS telemetry then its length is always 6.
        frame_remaining = len(frame_buf) - frame_offset
        request_buf_remaining = self.request_packet.buf.bytes_remaining()
        stop = frame_offset + min(frame_remaining, request_buf_remaining)
        # TODO: use `memoryview` for slicing.
        self.request_packet.buf.write_data(frame_buf[frame_offset:stop])

        # Further frames are required.
        if request_buf_remaining >= frame_remaining:
            return None

        self.msp_started = False

        # TODO: do I really need `switch_to_reader` - I suspect I'm never really working out `length` from `offset`.
        #  And this reset to start, full iterate and reset to start again is surely better done as a `for` over a slice.
        self.request_packet.buf.switch_to_reader()
        while self.request_packet.buf.bytes_remaining() > 0:
            self.checksum ^= self.request_packet.buf.read_u8()
        self.request_packet.buf.reset_offset()

        if self.checksum != frame_buf[stop]:
            return MspResult(self.request_packet.cmd, error=MspError.CRC_ERROR)

        length = self.request_packet.buf.length
        payload = self.request_packet.buf.buffer[0:length] if length > 0 else None

        # TODO: don't create new instances of `MspResult` and don't create `payload` from non-memoryview slice.
        return MspResult(self.request_packet.cmd, payload)
