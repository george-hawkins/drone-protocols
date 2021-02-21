# The lower 5 bits are the ID and the upper 3 are a checksum.
class PhysicalId:
    ID1 = 0xA0 | 0x01
    ID2 = 0x20 | 0x02
    ID3 = 0x80 | 0x03
    ID4 = 0xE0 | 0x04
    ID5 = 0x40 | 0x05
    ID6 = 0xC0 | 0x06
    ID7 = 0x60 | 0x07
    ID8 = 0x40 | 0x08
    ID9 = 0xE0 | 0x09
    ID10 = 0x60 | 0x0A
    ID11 = 0xC0 | 0x0B
    ID12 = 0xA0 | 0x0C
    ID13 = 0x00 | 0x0D
    ID14 = 0x80 | 0x0E
    ID15 = 0x20 | 0x0F
    ID16 = 0xC0 | 0x10
    ID17 = 0x60 | 0x11
    ID18 = 0xE0 | 0x12
    ID19 = 0x40 | 0x13
    ID20 = 0x20 | 0x14
    ID21 = 0x80 | 0x15
    ID22 = 0x00 | 0x16
    ID23 = 0xA0 | 0x17
    ID24 = 0x80 | 0x18
    ID25 = 0x20 | 0x19
    ID26 = 0xA0 | 0x1A
    ID27 = 0x00 | 0x1B

    _ID_MASK = 0x1F

    @staticmethod
    def name(physical_id):
        return "ID{}".format(PhysicalId._ID_MASK & physical_id)
