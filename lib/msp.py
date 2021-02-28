from msp_request import MspPackage


class MspResponse:
    def __init__(self, command, payload=None, is_error=False):
        self.command = command
        self.payload = payload if payload is not None else []
        self.is_error = is_error
        self.offset = 0

    def write(self, seq_number, frame_buf):
        header = seq_number
        payload_remaining = len(self.payload) - self.offset

        # TODO: move MspPackage.START_FLAG out into MspFlag or whatever.
        if self.offset == 0:
            # Unlike the request, there's no version included in the header byte.
            # And the command isn't included as the third byte (but it is factored into the checksum).
            header |= MspPackage.START_FLAG
            if self.is_error:
                header |= MspPackage.ERROR_FLAG
            frame_buf[0] = header
            frame_buf[1] = payload_remaining
            frame_offset = 2
        else:
            frame_buf[0] = header
            frame_offset = 1

        frame_remaining = len(frame_buf) - frame_offset
        count = min(frame_remaining, payload_remaining)

        # CircuitPython can't handle a zero length slice - CPython can.
        if count > 0:
            frame_buf[frame_offset:(frame_offset + count)] = self.payload[self.offset:(self.offset + count)]
        self.offset += count

        if payload_remaining >= frame_remaining:
            return False

        checksum = len(self.payload) ^ self.command

        for b in self.payload:
            checksum ^= b

        end = frame_offset + count
        frame_buf[end] = checksum
        bzero(frame_buf, end + 1)  # Zeroing unused bytes isn't necessary but makes tests and debugging simpler.

        return True


# No allocation memory zeroing similar to C `bzero`.
def bzero(buf, offset, length=-1):
    if length == -1:
        length = len(buf)
    i = offset
    while i < length:
        buf[i] = 0
        i += 1


class MspErrorResponse(MspResponse):
    def __init__(self, error, command):
        super().__init__(command, bytes([error]), is_error=True)
