# Note that `range` doesn't take keyword arguments even in CPython.
def loop(*args):
    r = range(*args)
    while True:
        yield from r
