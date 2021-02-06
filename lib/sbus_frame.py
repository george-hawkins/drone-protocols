import array


class SBusFrame:
    SBUS_START_BYTE = 0x0F
    SBUS_END_BYTE = 0x00
    LEVEL_MAX = 0x7FF
    CH_COUNT = 18

    def __init__(self):
        self.channels = array.array("H", (0 for _ in range(0, self.CH_COUNT)))
        self.lost_frame = False
        self.failsafe = False

    # TODO: consider using `memoryview` for `buffer` as you take lots of slices of it.
    #  See http://docs.micropython.org/en/latest/reference/speed_python.html#arrays
    def parse(self, buffer):
        assert len(buffer) == 25
        assert buffer[0] == self.SBUS_START_BYTE
        assert buffer[24] == self.SBUS_END_BYTE

        ch = 0
        start = 1
        shift = 0

        # Channels are 11 bits, usually they're split over two bytes, e.g. 5 bits in one byte and 6 in the next.
        # But at points they're split over 3 bytes, e.g. 2 bits, 8 bits and 1 bit.
        while start < 22:
            b = buffer[start:start + 3]
            self.channels[ch] = (int.from_bytes(b, "little") >> shift) & 0x7FF
            ch += 1
            if shift >= 5:
                start += 2
                shift -= 5  # I.e. `shift += (3 - 8)
            else:
                start += 1
                shift += 3

        last = buffer[23]

        # Channels 16 and 17 are either fully on or fully off.
        self.channels[16] = self.LEVEL_MAX if last & 0x01 else 0
        self.channels[17] = self.LEVEL_MAX if last & 0x02 else 0

        self.lost_frame = last & 0x04 != 0
        self.failsafe = last & 0x08 != 0
