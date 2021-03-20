import logging
from sport.control_code import SportControlCode as Code
from util.buffer import WriteBuffer

_logger = logging.getLogger("frame")


class FrameId:
    MSP_CLIENT = 0x30
    MSP_SERVER = 0x32
    SENSOR = 0x10


class Frame:
    _FRAME_LEN = 7  # 1 byte frame ID and 6 bytes of payload.

    def __init__(self):
        self.buffer = memoryview(bytearray(self._FRAME_LEN))
        self.payload = self.buffer[1 : self._FRAME_LEN]  # First byte is the frame_id.

    def get_id(self):
        return self.buffer[0]

    def set_id(self, frame_id):
        self.buffer[0] = frame_id


class FrameDecoder:
    INVALID_FRAME = object()

    def __init__(self):
        self._frame = Frame()
        self._decoded = WriteBuffer(buffer=self._frame.buffer)
        self._checksum_total = 0
        self._escaping = False

    def reset(self):
        self._decoded.reset_offset()
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

        if self._decoded.has_remaining():
            self._decoded.write_u8(b)
            return None

        # We've received the complete frame so validate and return it.

        if not Checksum.validate(self._checksum_total):
            _logger.error("invalid checksum")
            return self.INVALID_FRAME

        return self._frame


class FrameEncoder:
    _BUFFER_LEN = 16  # Worst case: frame ID + payload + checksum = 8 and every byte is doubled by escaping.

    def __init__(self):
        self._frame = Frame()
        self._encoded = WriteBuffer(length=self._BUFFER_LEN)

    def get_frame(self):
        return self._frame

    def _append(self, b):
        if b == Code.ESCAPE or b == Code.START:
            self._encoded.write_u8(Code.ESCAPE)
            b ^= Code.ESCAPE_XOR
        self._encoded.write_u8(b)

    def encode(self):
        self._encoded.reset_offset()

        for b in self._frame.buffer:
            self._append(b)

        total = sum(self._frame.buffer)
        self._append(Checksum.calculate(total))

        return self._encoded.get_buffer()


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
