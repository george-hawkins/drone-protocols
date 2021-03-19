import logging

from util.buffer import ReadBuffer, WriteBuffer
from util.ffs import ffs

_logger = logging.getLogger("response_encoder")


class MspHeaderBits:
    START_FLAG = 0x10
    ERROR_FLAG = 0x20  # Used in outgoing messages only.
    VERSION_MASK = 0xE0  # Used in incoming messages only.
    SEQUENCE_MASK = 0x0F  # Used in incoming messages only.


class MspError:
    VER_MISMATCH = 0
    CRC_ERROR = 1
    ERROR = 2  # Catch all error for commands.


class MspResult:
    _EMPTY_PAYLOAD = memoryview(b'')

    def __init__(self):
        self.command_id = 0
        self.payload = ReadBuffer()
        self.error = None

    def set(self, command=0, payload=None, error=None):
        self.command_id = command
        self.payload.set_buffer(payload if payload else self._EMPTY_PAYLOAD)
        self.error = error
        return self


# Decode one or more Sport frames into an MSP request.
class MspRequestDecoder:
    _BUFFER_LEN = 64

    _VERSION = 1
    _VER_SHIFT = ffs(MspHeaderBits.VERSION_MASK)

    def __init__(self):
        self._frame = ReadBuffer()
        self._request = WriteBuffer()
        self._request.set_buffer(memoryview(bytearray(self._BUFFER_LEN)))
        self._result = MspResult()
        self._command = -1
        self._started = False
        self._last_seq = -1

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
    def decode(self, buffer):
        # TODO: `buffer` here is actually the `payload` of `Frame.payload` so maybe `_frame` is a confusing name to use here.
        self._frame.set_buffer(buffer)

        header = self._frame.read_u8()
        version = (header & MspHeaderBits.VERSION_MASK) >> self._VER_SHIFT

        if version != self._VERSION:
            return self._result.set(error=MspError.VER_MISMATCH)

        seq_number = header & MspHeaderBits.SEQUENCE_MASK
        is_start = header & MspHeaderBits.START_FLAG

        if is_start:
            self._request.reset_offset()
            self._request.set_length(self._frame.read_u8())
            self._command = self._frame.read_u8()

            self._started = True
        elif not self._started:
            _logger.warning("ignoring frame %s", buffer)
            return None
        elif seq_number != (self._last_seq + 1) & MspHeaderBits.SEQUENCE_MASK:
            _logger.error("packet loss between %d and %d", self._last_seq, seq_number)
            self._started = False
            return None

        self._last_seq = seq_number

        frame_remaining = self._frame.remaining()
        request_remaining = self._request.remaining()
        remaining = min(frame_remaining, request_remaining)
        self._request.write(self._frame.read(remaining))

        # Either the frame was totally consumed (and we need more of them) or it has the final checksum byte.
        if not self._frame.has_remaining():
            return None

        self._started = False

        buffer = self._request.get_buffer()
        checksum = len(buffer) ^ self._command

        for b in buffer:
            checksum ^= b

        if checksum != self._frame.read_u8():
            return self._result.set(self._command, error=MspError.CRC_ERROR)

        return self._result.set(self._command, payload=buffer)
