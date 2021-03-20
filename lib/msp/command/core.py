import sys


class MspCommand:
    def __init__(self, command_id):
        self.id = command_id

    def handle_request(self, request, response):
        raise NotImplementedError("write_response")

    @staticmethod
    def _write_with_length(response, b):
        response.write_u8(len(b))
        response.write(b)


class MspApiVersionCommand(MspCommand):
    COMMAND_API_VERSION = 1

    # This is distinct from the version encoded in the header byte of MSP frames.
    _PROTOCOL_VERSION = 0

    # The minor version is updated fairly regularly as the Betaflight developers add additional commands.
    # See https://github.com/betaflight/betaflight/blame/master/src/main/msp/msp_protocol.h
    _VERSION_MAJOR = 1
    _VERSION_MINOR = 43

    def __init__(self):
        super().__init__(self.COMMAND_API_VERSION)

    def handle_request(self, _, response):
        response.write_u8(self._PROTOCOL_VERSION)
        response.write_u8(self._VERSION_MAJOR)
        response.write_u8(self._VERSION_MINOR)


class MspSaveAllCommand(MspCommand):
    COMMAND_SAVE_ALL = 250

    def __init__(self, configs):
        super().__init__(self.COMMAND_SAVE_ALL)
        self._configs = configs

    def handle_request(self, *_):
        try:
            for c in self._configs:
                c.save()
        except OSError as e:
            # File-system probably needs to be remounted - see `boot.py`.
            sys.print_exception(e)
