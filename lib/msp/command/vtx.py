import logging

from msp.command.core import MspCommand

_logger = logging.getLogger("vtx_commands")


class MspVtxConfigCommand(MspCommand):
    COMMAND_VTX_CONFIG = 88

    # Note: CircuitPython doesn't support '?' as the format character for booleans.
    _STRUCT_FORMAT = "<BBBBBHBBHBBBB"

    def __init__(self, config):
        super().__init__(self.COMMAND_VTX_CONFIG)
        self.config = config

    def handle_request(self, _, response):
        response.pack_into(
            self._STRUCT_FORMAT,
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
            self.config.table.band_count,
            self.config.table.channel_count,
            self.config.table.level_count,
        )


class MspVtxTableBandCommand(MspCommand):
    COMMAND_VTX_TABLE_BAND = 137

    def __init__(self, config):
        super().__init__(self.COMMAND_VTX_TABLE_BAND)
        self._config = config

    def handle_request(self, request, response):
        offset = request.read_u8()
        band = self._config.table.bands_list[offset - 1]

        response.write_u8(offset)
        self._write_with_length(response, band.name)
        response.write_u8(band.letter)
        response.write_u8(int(band.is_factory_band))
        response.write_u8(len(band.frequencies))
        for f in band.frequencies:
            response.write_u16(f)


class MspVtxTablePowerLevelCommand(MspCommand):
    COMMAND_VTX_TABLE_POWER_LEVEL = 138

    def __init__(self, config):
        super().__init__(self.COMMAND_VTX_TABLE_POWER_LEVEL)
        self._config = config

    def handle_request(self, request, response):
        offset = request.read_u8()
        level = self._config.table.levels_list[offset - 1]

        response.write_u8(offset)
        response.write_u16(level.value)
        self._write_with_length(response, level.label)


class MspSetVtxConfigCommand(MspCommand):
    COMMAND_SET_VTX_CONFIG = 89

    _BAND_CHANNEL_ENCODED = 0x3F
    _MAX_FREQUENCY_MHZ = 5999

    def __init__(self, config):
        super().__init__(self.COMMAND_SET_VTX_CONFIG)
        self._config = config

    # MspSetVtxConfigCommand is a bit unusual in that the incoming request is of variable length.
    def handle_request(self, request, _):
        c = self._config

        frequency = request.read_u16()

        if frequency <= self._BAND_CHANNEL_ENCODED:
            band = (frequency >> 3) + 1
            channel = (frequency & 0x07) + 1
            c.set_frequency(band=band, channel=channel)
        elif frequency <= self._MAX_FREQUENCY_MHZ:
            c.set_frequency(freq=frequency)

        if not request.has_remaining(2):
            return

        c.power = request.read_u8()
        c.pit_mode = request.read_u8()

        if not request.has_remaining():
            return

        c.low_power_disarm = request.read_u8()

        if not request.has_remaining(2):
            return

        c.pit_mode_freq = request.read_u16()

        if not request.has_remaining(4):
            return

        # Above band and channel can be encoded in the frequency value.
        # Here band, channel and frequency are unencoded and will overwrite the values set above.
        band = request.read_u8()
        channel = request.read_u8()
        frequency = request.read_u16()

        c.set_frequency(band=band, channel=channel, freq=frequency)

        if not request.has_remaining(4):
            return

        band_count = request.read_u8()
        channel_count = request.read_u8()
        level_count = request.read_u8()
        clear_table = request.read_u8() == 0

        _logger.warning(
            "ignoring table resize values - bands=%d, channels=%d, levels=%d, clear=%s",
            band_count,
            channel_count,
            level_count,
            clear_table,
        )
