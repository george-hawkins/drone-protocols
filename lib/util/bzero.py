# Memory zeroing similar to C `bzero`.
def bzero(buf, offset, length=-1):
    if length == -1:
        length = len(buf)
    i = offset
    while i < length:
        buf[i] = 0
        i += 1
