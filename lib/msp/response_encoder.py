from msp.request_decoder import MspHeaderBits
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

    def _reset(self, command, is_error):
        self._command = command
        self._is_error = is_error
        self._response.reset_offset()

    def set_error(self, error, command):
        self._reset(command, is_error=True)
        self._response.write_u8(error)

    def set_command(self, command, response_writer):
        self._reset(command, is_error=False)

        # Get the caller to fill in the response data.
        view = self._write_view
        view.reset_offset()
        response_writer(view)
        self._response.set_buffer(view.get_buffer())

    def encode(self, frame_payload):
        header = next(self._sequence)
        response_remaining = self._response.remaining()
        print("command {}, remaining {}".format(self._command, response_remaining))

        if self._response.get_offset() == 0:
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
            return True

        checksum = self._calculate_checksum(self._command, self._response.get_buffer())

        frame_payload.write_u8(checksum)

        # Pad out the rest of the frame - the value doesn't matter but 0 looks nicer when debugging.
        while frame_payload.has_remaining():
            frame_payload.write_u8(0)

        return False  # No more to come.

    @staticmethod
    def _calculate_checksum(command, buf):
        checksum = command ^ len(buf)

        for b in buf:
            checksum ^= b

        return checksum
