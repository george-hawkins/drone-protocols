import logging

_logger = logging.getLogger("payload")


class Payload:
    def __init__(self, data):
        self.frame_id = None
        self.data = data


class PayloadReader:
    _PAYLOAD_LEN = 7

    _ESCAPE = 0x7D
    _ESCAPE_XOR = 0x20

    def __init__(self):
        buffer = memoryview(bytearray(self._PAYLOAD_LEN))
        payload = Payload(buffer[1:self._PAYLOAD_LEN])

        self._payload = payload
        self._buffer = buffer
        self._offset = 0
        self._checksum = 0
        self._escaping = False

    def reset(self):
        self._offset = 0
        self._checksum = 0
        self._escaping = False

    def consume(self, b):
        if b == self._ESCAPE:
            self._escaping = True
            return False
        elif self._escaping:
            b ^= self._ESCAPE_XOR
            self._escaping = False

        self._checksum += b

        if self._finished():
            return True

        self._buffer[self._offset] = b
        self._offset += 1

        return False

    def _finished(self):
        return self._offset == self._PAYLOAD_LEN

    def get_payload(self):
        assert self._finished()

        if not self._validate_checksum():
            _logger.error("invalid payload checksum")
            return None

        self._payload.frame_id = self._buffer[0]

        return self._payload

    def _validate_checksum(self):
        check = self._checksum & 0xFFFF
        hi = check >> 8
        lo = check & 0xFF
        check = hi + lo

        return check == 0xFF
