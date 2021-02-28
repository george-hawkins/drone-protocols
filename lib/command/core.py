import sys


# TODO: this name clashes with the enum in `msp_request.py`.
class MspCommand:
    def __init__(self, command):
        self.command = command

    def get_response(self, payload):
        raise NotImplementedError("get_response")

    def _create_response(self, payload=None):
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


class MspSaveAllCommand(MspCommand):
    COMMAND_SAVE_ALL = 250

    def __init__(self, configs):
        super().__init__(self.COMMAND_SAVE_ALL)
        self.configs = configs

    def get_response(self, payload):
        try:
            for c in self.configs:
                c.save()
        except OSError as e:
            # File-system probably needs to be remounted - see `boot.py`.
            sys.print_exception(e)
        return self._create_response()
