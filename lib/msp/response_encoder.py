from msp.request_decoder import MspHeaderBits
from sport.frame import FrameId
from util.buffer import WriteBuffer, ReadBuffer
from util.util import loop


# Encode an MSP response into one or more Sport frames.
class MspResponseEncoder:
    _BUFFER_LEN = 64  # TODO: see how long responses typically are.

    def __init__(self):
        self._sequence = loop(0x10)
        self._command = 0
        self._is_error = False

        self._response = ReadBuffer()
        self._error_buffer = memoryview(bytearray(1))

        self._frame_payload = WriteBuffer()

    @staticmethod
    def create_response_buffer():
        buffer = WriteBuffer()
        buffer.set_buffer(memoryview(bytearray(MspResponseEncoder._BUFFER_LEN)))
        return buffer

    def _reset(self, command, buffer, is_error):
        self._command = command
        self._is_error = is_error
        self._response.set_buffer(buffer)

    def set_error(self, error, command):
        self._error_buffer[0] = error
        self._reset(command, self._error_buffer, is_error=True)

    def set_command(self, command, buffer):
        self._reset(command, buffer, is_error=False)

    def encode(self, frame):
        frame.set_id(FrameId.MSP_SERVER)
        self._frame_payload.set_buffer(frame.payload)

        header = next(self._sequence)
        response_remaining = self._response.remaining()

        # Write the start header if this is the frame of a given response.
        if self._response.get_offset() == 0:
            # Unlike the request, there's no version included in the header byte.
            # And the command isn't included as the third byte (but it is factored into the checksum).
            header |= MspHeaderBits.START_FLAG
            if self._is_error:
                header |= MspHeaderBits.ERROR_FLAG
            self._frame_payload.write_u8(header)
            self._frame_payload.write_u8(response_remaining)
        else:
            self._frame_payload.write_u8(header)

        frame_remaining = self._frame_payload.remaining()
        remaining = min(frame_remaining, response_remaining)

        self._frame_payload.write(self._response.read(remaining))

        if response_remaining >= frame_remaining:
            return True

        checksum = self._calculate_checksum(self._command, self._response.get_buffer())

        self._frame_payload.write_u8(checksum)

        # Pad out the rest of the frame - the value doesn't matter but 0 looks nicer when debugging.
        while self._frame_payload.has_remaining():
            self._frame_payload.write_u8(0)

        return False  # No more to come.

    @staticmethod
    def _calculate_checksum(command, buf):
        checksum = command ^ len(buf)

        for b in buf:
            checksum ^= b

        return checksum
