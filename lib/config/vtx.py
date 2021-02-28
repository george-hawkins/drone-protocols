import json


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
        self.pit_mode = True
        self.ready = True
        self.low_power_disarm = 0
        self.pit_mode_freq = 0

        # `band`, `channel` and `power` index into the JSON `vtx_table`, with indexes starting from 1 (0 means not set).
        self.band = 1
        self.channel = 1
        self.power = 1

        self.freq = 0
        self.set_frequency(self.band, self.channel, self.freq)

    # `freq` is normally determined from `band` and `channel` but you can set them to 0 and set `freq` directly.
    def set_frequency(self, band=0, channel=0, freq=0):
        self.band = band
        self.channel = channel
        self.freq = freq if band == 0 else self.bands_list[band - 1]["frequencies"][channel - 1]

    def save(self):
        with open(self.filename, "w") as f:
            pass
            # TODO: load and write type, band etc. to/from file.
            # json.dump(self.xyz, f)
