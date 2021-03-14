# Python equivalent of ffs - find first bit set in a word - https://linux.die.net/man/3/ffs
# https://stackoverflow.com/a/36059264/245602
def ffs(x):
    return (-x & x).bit_length() - 1
