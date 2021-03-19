# Note: in the Betaflight code `ESCAPE` is called `DLE` even though it doesn't have the same value as the
# traditional ASCII data link escape (DLE) code - https://en.wikipedia.org/wiki/C0_and_C1_control_codes
class SportControlCode:
    START = 0x7E
    ESCAPE = 0x7D
    ESCAPE_XOR = 0x20
