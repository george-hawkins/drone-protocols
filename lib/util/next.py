# For whatever reason `next` with a default isn't implemented in CircuitPython or MicroPython.
# https://docs.micropython.org/en/latest/genrst/modules.html#second-argument-to-next-is-not-implemented
def next_with_default(it, default):
    try:
        return next(it)
    except StopIteration:
        return default
