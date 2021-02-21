import busio


class UartPumper:
    _RX_BUFFER_LEN = 64

    def __init__(self, tx, rx, baud_rate):
        self._uart = busio.UART(tx, rx, baudrate=baud_rate, timeout=0, receiver_buffer_size=self._RX_BUFFER_LEN)
        self._rx_buffer = bytearray(self._RX_BUFFER_LEN)

    def available(self):
        return self._uart.in_waiting > 0

    def pump(self):
        count = self._uart.readinto(self._rx_buffer)
        if count:
            i = 0
            last = count - 1

            def is_clear():
                return i == last and not self.available()

            while i < count:
                self._consume(self._rx_buffer[i], is_clear)
                i += 1

    def _consume(self, b, is_clear):
        raise NotImplementedError("_consume")


class Poller:
    def __init__(self):
        self.pumpers = []

    def register(self, pumper):
        self.pumpers.append(pumper)

    def poll(self):
        for pumper in self.pumpers:
            if pumper.available():
                pumper.pump()
