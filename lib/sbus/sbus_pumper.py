from sbus.sbus_decoder import SbusDecoder
from util.uart_pumper import UartPumper


class SbusPumper(UartPumper):
    # S.BUS uses its own rate rather than one of the common ones like 115200.
    _BAUD_RATE = 100000

    def __init__(self, rx, subscriber):
        super().__init__(None, rx, self._BAUD_RATE)
        self._decoder = SbusDecoder()
        self._subscriber = subscriber

    def _consume(self, b, _):
        frame = self._decoder.decode(b)
        if frame:
            self._subscriber(frame)


