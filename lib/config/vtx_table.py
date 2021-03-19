import json
from collections import namedtuple


VtxPowerLevel = namedtuple("VtxPowerLevel", ["value", "label"])

VtxBand = namedtuple("Band", ["name", "letter", "is_factory_band", "frequencies"])


class VtxTable:
    def __init__(self, filename):
        # In CircuitPython strings are automatically interned. So parsing JSON is reasonably
        # space efficient, e.g. you don't end up with multiple strings for repeated keys.
        with open(filename) as f:
            table = json.load(f)["vtx_table"]

        def to_band(d):
            return VtxBand(d["name"].encode(), ord(d["letter"]), d["is_factory_band"], d["frequencies"])

        def to_level(d):
            return VtxPowerLevel(d["value"], d["label"].encode())

        self.bands_list = [to_band(d) for d in table["bands_list"]]
        self.levels_list = [to_level(d) for d in table["powerlevels_list"]]

        self.band_count = len(self.bands_list)
        self.channel_count = max([len(band.frequencies) for band in self.bands_list])
        self.level_count = len(self.levels_list)

    def get_freq(self, band, channel):
        return self.bands_list[band].frequencies[channel]


