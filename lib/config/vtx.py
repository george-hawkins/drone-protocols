from config.vtx_table import VtxTable


class VtxConfig:
    # From `vtxDevType_e` in src/main/drivers/vtx_common.h
    VTX_DEV_SMARTAUDIO = 3

    def __init__(self, config_filename="vtx_config.json", table_filename="vtx_table.json"):
        self._filename = config_filename

        self.type = self.VTX_DEV_SMARTAUDIO
        self.ready = True

        self.use_vtx_table = True
        self.table = VtxTable(table_filename)

        self.low_power_disarm = 0

        self.pit_mode = True
        self.pit_mode_freq = 0

        # `band`, `channel` and `power` index into `self.table`, with indexes starting from 1 (0 means not set).
        self.band = 1
        self.channel = 1
        self.power = 1

        self.freq = 0
        self.set_frequency(self.band, self.channel, self.freq)

    # `freq` is normally determined from `band` and `channel` but you can set them to 0 and set `freq` directly.
    def set_frequency(self, band=0, channel=0, freq=0):
        self.band = band
        self.channel = channel
        self.freq = freq if band == 0 else self.table.get_freq(band - 1, channel - 1)

    def save(self):
        with open(self._filename, "w") as f:
            pass
            # TODO: load and write type, band etc. to/from file.
            # json.dump(self.xyz, f)
