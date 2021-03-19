import time


# Use to do a blocking read (with timeout) on a non-blocking stream.
class BlockingReader:
    def __init__(self, timeout=0):
        self._timeout = timeout
        self._buffer = bytearray(1)

    def read(self, stream):
        start = time.monotonic_ns()
        while True:
            count = stream.readinto(self._buffer)
            # None means a timeout. A `count` of 0 should never really happen.
            if count is not None:
                return self._buffer[0] if count == 1 else None
            elif self._timeout != 0:
                diff = time.monotonic_ns() - start
                if diff > self._timeout:
                    return None

    # Calculate a timeout (in nanoseconds) based on a multiple of the transmission
    # time for a byte at a given baud rate (assuming 8 data bits and one stop bit).
    @staticmethod
    def calculate_timeout(baud_rate, factor):
        return (9 * factor) * pow(10, 9) // baud_rate
