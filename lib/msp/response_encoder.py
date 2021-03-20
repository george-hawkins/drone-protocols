from msp.request_decoder import MspHeaderBits
from sport.frame import FrameId
from util.buffer import WriteBuffer, ReadBuffer
from util.loop import loop


# Encode an MSP response into one or more Sport frames.
class MspResponseEncoder:
    _BUFFER_LEN = 64  # TODO: see how long responses typically are.

    def __init__(self):
        self._sequence = loop(0x10)
        self._command = 0
        self._is_error = False

        buffer = memoryview(bytearray(self._BUFFER_LEN))
        self._response = ReadBuffer()
        self._write_view = WriteBuffer()
        self._write_view.set_buffer(buffer)
        self._error_buffer = memoryview(bytearray(1))

        self._frame_payload = WriteBuffer()

    def _reset(self, command, is_error):
        self._command = command
        self._is_error = is_error
        self._response.reset_offset()

    def set_error(self, error, command):
        self._reset(command, is_error=True)
        self._error_buffer[0] = error
        self._response.set_buffer(self._error_buffer)

    def set_command(self, command, response_writer):
        self._reset(command, is_error=False)

        # Get the caller to fill in the response data.
        view = self._write_view
        view.reset_offset()
        response_writer(view)
        self._response.set_buffer(view.get_buffer())

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
