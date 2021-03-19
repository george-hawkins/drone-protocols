import logging
from sport.control_code import SportControlCode as Code
from util.buffer import WriteBuffer

_logger = logging.getLogger("frame")


class FrameId:
    MSP_CLIENT = 0x30
    MSP_SERVER = 0x32
    SENSOR = 0x10


class Frame:
    def __init__(self, payload):
        self.id = 0
        self.payload = payload


class FrameDecoder:
    _FRAME_LEN = 7  # 1 byte frame ID and 6 bytes of payload.

    INVALID_FRAME = object()

    def __init__(self):
        # TODO: consider rewriting using a WriteBuffer.
        self._buffer = memoryview(bytearray(self._FRAME_LEN))
        self._frame = Frame(self._buffer[1:self._FRAME_LEN])  # First byte is the frame_id.
        self._offset = 0
        self._checksum_total = 0
        self._escaping = False

    def reset(self):
        self._offset = 0
        self._checksum_total = 0
        self._escaping = False

    def decode(self, b):
        if b == Code.ESCAPE:
            self._escaping = True
            return None
        elif self._escaping:
            self._escaping = False
            b ^= Code.ESCAPE_XOR

        self._checksum_total += b

        if self._offset < self._FRAME_LEN:
            self._buffer[self._offset] = b
            self._offset += 1
            return None

        # We've received the complete frame so validate and return it.

        if not Checksum.validate(self._checksum_total):
            _logger.error("invalid checksum")
            return self.INVALID_FRAME

        self._frame.id = self._buffer[0]

        return self._frame


class FrameEncoder:
    _PAYLOAD_LEN = 6
    _BUFFER_LEN = 16  # Worst case: frame ID + payload + checksum = 8 and every byte is doubled by escaping.

    def __init__(self):
        self._frame = WriteBuffer()
        self._frame.set_buffer(memoryview(bytearray(self._BUFFER_LEN)))

    def _append(self, b):
        if b == Code.ESCAPE or b == Code.START:
            self._frame.write_u8(Code.ESCAPE)
            b ^= Code.ESCAPE_XOR
        self._frame.write_u8(b)

    def encode(self, frame_id, payload):
        assert len(payload) == self._PAYLOAD_LEN

        self._frame.reset_offset()
        self._append(frame_id)

        for b in payload:
            self._append(b)

        total = frame_id + sum(payload)
        self._append(Checksum.calculate(total))

        return self._frame.get_buffer()


class Checksum:
    @staticmethod
    def calculate(total):
        checksum = total & 0xFFFF
        while checksum > 0xFF:
            checksum = Checksum._reduce(checksum)
        return 0xFF - checksum

    @staticmethod
    def validate(total):
        checksum = total & 0xFFFF
        checksum = Checksum._reduce(checksum)
        return checksum == 0xFF

    @staticmethod
    def _reduce(checksum):
        hi = checksum >> 8
        lo = checksum & 0xFF
        return hi + lo
