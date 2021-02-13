from msp_request import MspPackage


class MspResponse:
    def __init__(self, command, payload, is_error=False):
        self.command = command
        self.payload = payload
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

        frame_buf[frame_offset:(frame_offset + count)] = self.payload[self.offset:(self.offset + count)]
        self.offset += count

        if payload_remaining >= frame_remaining:
            return False

        checksum = len(self.payload) ^ self.command

        for b in self.payload:
            checksum ^= b

        frame_buf[frame_offset + count] = checksum

        return True


class MspErrorResponse(MspResponse):
    def __init__(self, error, command):
        super().__init__(command, bytes([error]), is_error=True)


# TODO: this name clashes with the enum in `msp_request.py`.
class MspCommand:
    def __init__(self, command):
        self.command = command
        pass

    def get_response(self, payload):
        raise NotImplementedError("get_response")

    def _create_response(self, payload):
        return MspResponse(self.command, payload)


class MspApiVersionCommand(MspCommand):
    COMMAND_API_VERSION = 1

    # See https://github.com/betaflight/betaflight/blame/master/src/main/msp/msp_protocol.h
    PROTOCOL_VERSION = 0  # This is distinct from the version encoded in the header byte of MSP frames.
    VERSION_MAJOR = 1
    VERSION_MINOR = 43

    def __init__(self):
        super().__init__(self.COMMAND_API_VERSION)

    def get_response(self, payload):
        return self._create_response(bytes([self.PROTOCOL_VERSION, self.VERSION_MAJOR, self.VERSION_MINOR]))
