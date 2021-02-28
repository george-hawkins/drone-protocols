import struct

from command.core import MspCommand
from util.buffer import ReadBuffer


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


class MspSetVtxConfigCommand(MspCommand):
    COMMAND_SET_VTX_CONFIG = 89

    _BAND_CHANNEL_ENCODED = 0x3F
    _MAX_FREQUENCY_MHZ = 5999

    def __init__(self, config):
        super().__init__(self.COMMAND_SET_VTX_CONFIG)
        self.config = config

    # MspSetVtxConfigCommand is a bit unusual in that incoming payload is of variable length.
    def get_response(self, payload):
        response = self._create_response()
        buffer = ReadBuffer(payload)
        c = self.config

        frequency = buffer.read_u16()

        if frequency <= self._BAND_CHANNEL_ENCODED:
            band = (frequency >> 3) + 1
            channel = (frequency & 0x07) + 1
            c.set_frequency(band=band, channel=channel)
        elif frequency <= self._MAX_FREQUENCY_MHZ:
            c.set_frequency(freq=frequency)

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
        band = buffer.read_u8()
        channel = buffer.read_u8()
        frequency = buffer.read_u16()

        c.set_frequency(band=band, channel=channel, freq=frequency)

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
