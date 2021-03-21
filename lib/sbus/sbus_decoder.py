import array
import logging

from util.buffer import WriteBuffer
from util.util import repeat, ByteOrder

_logger = logging.getLogger("sbus_decoder")


class SbusFrame:
    # Note: Betaflight uses quite different values for max and min. See `SBUS_DIGITAL_CHANNEL_MAX`
    # and `SBUS_DIGITAL_CHANNEL_MIN` in `rc/main/rx/sbus_channels.c`.
    # TODO: use Betaflight values - they match the min and max you see for real channels.
    LEVEL_MAX = 0x7FF

    _CH_COUNT = 18

    def __init__(self):
        self.channels = array.array("H", repeat(0, self._CH_COUNT))
        self.lost_frame = False
        self.failsafe = False


# See `sbus-notes.md` for more details on S.BUS.
class SbusDecoder:
    _START_BYTE = 0x0F
    _BUFFER_LEN = 23
    _CH16_FLAG = 0x01
    _CH17_FLAG = 0x02
    _LOST_FRAME_FLAG = 0x04
    _FAILSAFE_FLAG = 0x08

    def __init__(self):
        self._payload = WriteBuffer(length=self._BUFFER_LEN)
        self._frame = SbusFrame()
        self._searching = True

    def decode(self, b):
        if self._searching:
            if b == self._START_BYTE:
                self._payload.reset_offset()
                self._searching = False
            else:
                _logger.warning("ignoring 0x%02X", b)
        elif self._payload.has_remaining():
            self._payload.write_u8(b)
        else:
            self._searching = True
            return self._parse()

        return None

    def _parse(self):
        buffer = self._payload.get_buffer()

        ch = 0
        start = 0
        shift = 0

        def from_bytes(b):
            int.from_bytes(b, ByteOrder.LITTLE)

        # Channels are 11 bits, usually they're split over two bytes, e.g. 5 bits in one byte and 6 in the next.
        # But at points they're split over 3 bytes, e.g. 2 bits, 8 bits and 1 bit.
        while start < 21:
            b = buffer[start : start + 3]
            self._frame.channels[ch] = (from_bytes(b) >> shift) & 0x7FF
            ch += 1
            if shift >= 5:
                start += 2
                shift -= 5  # I.e. `shift += (3 - 8)`.
            else:
                start += 1
                shift += 3

        last = buffer[22]

        # Channels 16 and 17 are either fully on or fully off.
        self._frame.channels[16] = SbusFrame.LEVEL_MAX if last & self._CH16_FLAG else 0
        self._frame.channels[17] = SbusFrame.LEVEL_MAX if last & self._CH17_FLAG else 0

        self._frame.lost_frame = last & self._LOST_FRAME_FLAG != 0
        self._frame.failsafe = last & self._FAILSAFE_FLAG != 0

        return self._frame
