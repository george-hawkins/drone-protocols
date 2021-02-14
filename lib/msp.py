import json
import struct
import sys

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
def bzero(buf, offset, length=None):
    if length is None:
        length = len(buf)
    i = offset
    while i < length:
        buf[i] = 0
        i += 1


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


class VtxConfig:
    # From `vtxDevType_e` in src/main/drivers/vtx_common.h
    VTX_DEV_SMARTAUDIO = 3

    def __init__(self, filename="vtx_table.json"):
        self.filename = filename

        # String creation is optimized - if you try to create a string that already exists
        # you get a reference to the existing string. So parsing JSON is reasonably space
        # efficient, e.g. you don't end up with multiple strings for repeated keys.
        with open(filename) as f:
            table = json.load(f)["vtx_table"]
        self.bands_list = table["bands_list"]
        self.levels_list = table["powerlevels_list"]

        self.use_vtx_table = True

        self.band_count = len(self.bands_list)
        self.channel_count = max([len(x["frequencies"]) for x in self.bands_list])
        self.level_count = len(self.levels_list)

        self.type = self.VTX_DEV_SMARTAUDIO
        # `band`, `channel` and `power` index into the JSON `vtx_table`, with indexes starting from 1 (0 means not set).
        self.band = 1
        self.channel = 1
        self.power = 1
        self.pit_mode = True
        self.ready = True
        self.low_power_disarm = 0
        self.pit_mode_freq = 0

        self.freq = 0
        self.update_frequency()

    def update_frequency(self):
        if self.band != 0:
            self.freq = self.bands_list[self.band - 1]["frequencies"][self.channel - 1]

    def save(self):
        with open(self.filename, "w") as f:
            pass
            # TODO: load and write type, band etc. to/from file.
            # json.dump(self.xyz, f)


class MspVtxConfigCommand(MspCommand):
    COMMAND_VTX_CONFIG = 88

    def __init__(self, config):
        super().__init__(self.COMMAND_VTX_CONFIG)
        self.config = config
        # Note: CircuitPython doesn't support '?' as the format character for booleans.
        self.format = "<BBBBBHBBHBBBB"

    def get_response(self, payload):
        # TODO: note you can pack a tuple with the spread operator `x.pack(*my_tuple)` and unpack to a named tuple.
        #  Or unpack like so: `x, y, z = x.unpack(...)`.
        return self._create_response(struct.pack(
            self.format,
            self.config.type,
            self.config.band,
            self.config.channel,
            self.config.power,
            int(self.config.pit_mode),
            self.config.freq,
            int(self.config.ready),
            self.config.low_power_disarm,
            self.config.pit_mode_freq,
            self.config.use_vtx_table,
            self.config.band_count,
            self.config.channel_count,
            self.config.level_count
        ))


class ReadBuffer:
    def __init__(self, buffer):
        self.buffer = buffer
        self.offset = 0

    def remaining(self):
        return len(self.buffer) - self.offset

    def has_remaining(self, count=1):
        return self.remaining() >= count

    def read_u8(self):
        v = self.buffer[self.offset]
        self.offset += 1
        return v

    def read_u16(self):
        v = int.from_bytes(self.buffer[self.offset:(self.offset + 2)], BYTE_ORDER)
        self.offset += 2
        return v


class MspSetVtxConfigCommand(MspCommand):
    COMMAND_SET_VTX_CONFIG = 89

    _BANDCHAN_CHKVAL = 0x3F
    _MAX_FREQUENCY_MHZ = 5999

    def __init__(self, config):
        super().__init__(self.COMMAND_SET_VTX_CONFIG)
        self.config = config

    def get_response(self, payload):
        response = self._create_response()
        buffer = ReadBuffer(payload)
        c = self.config

        frequency = buffer.read_u16()

        if frequency <= self._BANDCHAN_CHKVAL:
            c.band = (frequency >> 3) + 1
            c.channel = (frequency & 0x07) + 1
            c.update_frequency()
        elif frequency <= self._MAX_FREQUENCY_MHZ:
            c.band = 0
            c.freq = frequency

        if not buffer.has_remaining(2):
            return response

        c.power = buffer.read_u8()
        c.pit_mode = buffer.read_u8()

        if not buffer.has_remaining():
            return response

        c.low_power_disarm = buffer.read_u8()

        if not buffer.has_remaining(2):
            return response

        c.pit_mode_freq = buffer.read_u16()

        if not buffer.has_remaining(4):
            return response

        # Above band and channel are encoded in the frequency value.
        # Here they're unencoded and will overwrite the values set above.
        c.band = buffer.read_u8()
        c.channel = buffer.read_u8()
        frequency = buffer.read_u16()

        c.freq = frequency if c.band != 0 else c.update_frequency()

        if not buffer.has_remaining(4):
            return response

        band_count = buffer.read_u8()
        channel_count = buffer.read_u8()
        level_count = buffer.read_u8()
        clear_table = buffer.read_u8()

        print("Warning: ignoring table resize values")
        print(band_count)
        print(channel_count)
        print(level_count)
        print(clear_table)

        return self._create_response()


class MspVtxTableBandCommand(MspCommand):
    COMMAND_VTX_TABLE_BAND = 137

    def __init__(self, config):
        super().__init__(self.COMMAND_VTX_TABLE_BAND)
        self.config = config

    def get_response(self, payload):
        offset = payload[0]
        band = self.config.bands_list[offset - 1]
        name = band["name"].encode()
        frequencies = band["frequencies"]
        frequencies_len = len(frequencies)
        data = \
            bytes([offset, len(name)]) + \
            name + \
            bytes([ord(band["letter"]), int(band["is_factory_band"]), frequencies_len]) + \
            struct.pack("<{}H".format(frequencies_len), *frequencies)
        return self._create_response(data)


# TODO: replace with SmartPort.BYTE_ORDER.
BYTE_ORDER = "little"


class MspVtxTablePowerLevelCommand(MspCommand):
    COMMAND_VTX_TABLE_POWER_LEVEL = 138

    def __init__(self, config):
        super().__init__(self.COMMAND_VTX_TABLE_POWER_LEVEL)
        self.config = config

    def get_response(self, payload):
        print(payload)
        offset = payload[0]
        level = self.config.levels_list[offset - 1]
        label = level["label"].encode()
        data = \
            bytes([offset]) + \
            level["value"].to_bytes(2, BYTE_ORDER) + \
            bytes([len(label)]) + \
            label
        return self._create_response(data)


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
