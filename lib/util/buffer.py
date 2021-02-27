class Buffer:
    LITTLE_ENDIAN = "little"
    BIG_ENDIAN = "big"

    def __init__(self, byte_order=LITTLE_ENDIAN):
        self._buffer = None
        self._length = 0
        self._offset = 0
        self._byte_order = byte_order

    def set_buffer(self, buffer, length=-1):
        assert isinstance(buffer, memoryview)

        self._buffer = buffer
        self._length = len(buffer) if length == -1 else length
        self._offset = 0

    def get_buffer(self, use_offset=True):
        return self._buffer[:self._offset] if use_offset else self._buffer

    def reset_offset(self):
        self._offset = 0

    def set_length(self, length):
        assert length <= len(self._buffer)
        self._length = length

    def remaining(self):
        return self._length - self._offset

    def has_remaining(self, count=1):
        return self.remaining() >= count


class ReadBuffer(Buffer):
    def read_u8(self):
        v = self._buffer[self._offset]
        self._offset += 1
        return v

    def read_u16(self):
        return int.from_bytes(self.read(2), self._byte_order)

    def read(self, length=-1):
        if length == -1:
            length = self.remaining()
        start = self._offset
        self._offset += length
        return self._buffer[start:self._offset]


class WriteBuffer(Buffer):
    def write_u8(self, v):
        self._buffer[self._offset] = v
        self._offset += 1

    def write_u16(self, v):
        self.write(v.to_bytes(2, self._byte_order))

    def write(self, buffer, offset=0, length=-1):
        if length == -1:
            length = len(buffer)
        start = self._offset
        self._offset += length
        end = offset + length
        self._buffer[start:self._offset] = buffer[offset:end]