from sport.multi_payload import MspHeaderBits
from util.buffer import WriteBuffer, ReadBuffer
from util.loop import loop


class MspResponseEncoder:
    _BUFFER_LEN = 64  # TODO: see how long responses typically are.

    def __init__(self):
        self._sequence = loop(0x10)
        self._command = 0
        self._is_error = False

        buffer = memoryview(bytearray(self._BUFFER_LEN))
        self._response = ReadBuffer()
        self._response.set_buffer(buffer)
        self._write_view = WriteBuffer()
        self._write_view.set_buffer(buffer)

    def _reset(self, command, is_error):
        self._command = command
        self._is_error = is_error
        self._response.reset_offset()
        self._write_view.reset_offset()

    def set_error(self, error, command):
        self._reset(command, is_error=True)
        self._response.write_u8(error)

    def set_command(self, command):
        self._reset(command, is_error=False)
        return self._write_view

    def encode(self, frame_payload):
        header = next(self._sequence)
        response_remaining = self._response.remaining()

        if self._response.get_offet() == 0:
            # Unlike the request, there's no version included in the header byte.
            # And the command isn't included as the third byte (but it is factored into the checksum).
            header |= MspHeaderBits.START_FLAG
            if self._is_error:
                header |= MspHeaderBits.ERROR_FLAG
            frame_payload.write_u8(header)
            frame_payload.write_u8(response_remaining)
        else:
            frame_payload.write_u8(header)

        frame_remaining = frame_payload.remaining()
        count = min(frame_remaining, response_remaining)

        frame_payload.write(self._response.read(count))

        if response_remaining >= frame_remaining:
            return False

        checksum = self._calculate_checksum(self._command, self._response.get_buffer())

        frame_payload.write_u8(checksum)

        # TODO: should I zero remaining frame_payload bytes? If not get rid on `bzero`.

        return True

    def _calculate_checksum(self, command, buf):
        checksum = command ^ len(buf)

        for b in self._response:
            checksum ^= b

        return checksum
