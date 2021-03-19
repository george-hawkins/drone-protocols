import json

from config.vtx_table import VtxTable
from util.field_name import get_field_name


# From `vtxDevType_e` in Betaflight src/main/drivers/vtx_common.h
class VtxDeviceType:
    UNSUPPORTED = 0
    RTC6705 = 1
    SMART_AUDIO = 3
    TRAMP = 4


class VtxConfig:
    def __init__(self, config_filename="vtx_config.json", table_filename="vtx_table.json"):
        self._filename = config_filename

        store = self._load()

        self.type = getattr(VtxDeviceType, store["type"])
        self.ready = store["ready"]

        self.use_vtx_table = store["use_vtx_table"]
        self.table = VtxTable(table_filename)

        self.low_power_disarm = store["low_power_disarm"]

        self.pit_mode = store["pit_mode"]
        self.pit_mode_freq = store["pit_mode_freq"]

        # `power`, `band` and `channel` index into `self.table`, with indexes starting from 1 (0 means not set).

        self.power = store["power"]

        self.band = store["band"]
        self.channel = store["channel"]
        self.freq = store.get("freq", 0)
        self.set_frequency(self.band, self.channel, self.freq)

    # `freq` is normally determined from `band` and `channel` but you can set them to 0 and set `freq` directly.
    def set_frequency(self, band=0, channel=0, freq=0):
        self.band = band
        self.channel = channel
        self.freq = freq if band == 0 else self.table.get_freq(band - 1, channel - 1)

    def _load(self):
        with open(self._filename) as f:
            return json.load(f)

    # Saving is very slow - so incoming requests may back up and we may miss transmission slots.
    def save(self):
        store = {
            "type": get_field_name(VtxDeviceType, self.type),
            "ready": self.ready,
            "use_vtx_table": self.use_vtx_table,
            "low_power_disarm": self.low_power_disarm,
            "pit_mode": self.pit_mode,
            "pit_mode_freq": self.pit_mode_freq,
            "power": self.power,
            "band": self.band,
            "channel": self.channel
        }
        if self.band == 0:
            store["freq"] = self.freq
        with open(self._filename, "w") as f:
            json.dump(store, f)
