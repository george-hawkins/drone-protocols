import logging

import busio

from util.blocking_reader import BlockingReader

_logger = logging.getLogger("uart_pumper")


class UartPumper:
    _RX_BUFFER_LEN = 32

    def __init__(self, tx, rx, baud_rate, echo=False):
        self._uart = busio.UART(
            tx,
            rx,
            baudrate=baud_rate,
            timeout=0,
            receiver_buffer_size=self._RX_BUFFER_LEN,
        )
        self._rx_buffer = bytearray(self._RX_BUFFER_LEN)
        self._blocking_reader = self.create_blocking_reader(baud_rate) if echo else None

    @staticmethod
    def create_blocking_reader(baud_rate):
        timeout = BlockingReader.calculate_timeout(baud_rate, factor=4)
        return BlockingReader(timeout)

    def _write(self, tx_buffer):
        self._uart.write(tx_buffer)
        self._consume_echo(tx_buffer)

    # Consume the bytes that have just been written on the TX pin and echoed on the RX pin.
    def _consume_echo(self, tx_buffer):
        if self._blocking_reader:
            for b in tx_buffer:
                echo = self._blocking_reader.read(self._uart)
                if echo != b:
                    _logger.error("echo - expected 0x%02X, got 0x%02X", b, echo)
                    return

    def pump(self):
        count = self._uart.readinto(self._rx_buffer)
        if count:
            i = 0
            last = count - 1

            def is_clear():
                return i == last and self._uart.in_waiting == 0

            while i < count:
                self._consume(self._rx_buffer[i], is_clear)
                i += 1

    def _consume(self, b, is_clear):
        raise NotImplementedError("_consume")


# On MicroPython, this class used `uselect.poll` but CircuitPython doesn't support `uselect` for SAMD MCUs.
class PumpMaster:
    def __init__(self):
        self._pumpers = []

    def register(self, pumper):
        self._pumpers.append(pumper)

    def pump_all(self):
        for pumper in self._pumpers:
            pumper.pump()
