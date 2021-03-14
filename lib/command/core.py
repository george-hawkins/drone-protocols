import sys


class MspCommand:
    def __init__(self, command_id):
        self.id = command_id

    def handle_request(self, request, response):
        raise NotImplementedError("write_response")

    @staticmethod
    def _write_string(response, s):
        # TODO: should all the strings, e.g. in `config`, be encoded up front?
        b = s.encode()
        response.write_u8(len(b))
        response.write(b)


class MspApiVersionCommand(MspCommand):
    COMMAND_API_VERSION = 1

    # See https://github.com/betaflight/betaflight/blame/master/src/main/msp/msp_protocol.h
    PROTOCOL_VERSION = 0  # This is distinct from the version encoded in the header byte of MSP frames.
    VERSION_MAJOR = 1
    VERSION_MINOR = 43

    def __init__(self):
        super().__init__(self.COMMAND_API_VERSION)

    def handle_request(self, _, response):
        response.write_u8(self.PROTOCOL_VERSION)
        response.write_u8(self.VERSION_MAJOR)
        response.write_u8(self.VERSION_MINOR)


class MspSaveAllCommand(MspCommand):
    COMMAND_SAVE_ALL = 250

    def __init__(self, configs):
        super().__init__(self.COMMAND_SAVE_ALL)
        self.configs = configs

    def handle_request(self, *_):
        try:
            for c in self.configs:
                c.save()
        except OSError as e:
            # File-system probably needs to be remounted - see `boot.py`.
            sys.print_exception(e)
