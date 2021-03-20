# Note that `range` doesn't take keyword arguments even in CPython.
def loop(*args):
    r = range(*args)
    while True:
        yield from r


# Use with enum-like classes to get from a field value to a field name.
def get_field_name(obj, value):
    # CircuitPython doesn't provide `vars` so we use `dir` and `getattr` instead.
    return next(attr for attr in dir(obj) if getattr(obj, attr) == value)


# Python equivalent of ffs - find first bit set in a word - https://linux.die.net/man/3/ffs
# https://stackoverflow.com/a/36059264/245602
def ffs(x):
    return (-x & x).bit_length() - 1


# For use with `int.from_bytes` and similar methods.
class ByteOrder:
    LITTLE = "little"
    BIG = "big"
