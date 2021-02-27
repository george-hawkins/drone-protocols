import logging

from sport.payload import PayloadReader
from sport.physical_id import PhysicalId
from uart_pumper import UartPumper

_logger = logging.getLogger("sport_pumper")


# The Sport bus is managed by the FrSky receiver. It cycles through a sequence of physical IDs, transmitting an
# invitation for each ID in turn to transmit. It pauses for about 12ms after each invite, giving the device with the
# current ID a chance to transmit.
# Simple sensors just transmit their own data during their transmission slot and are uninterested in the data
# transmitted by other devices. However, devices can also listen out for what each other transmits and use this as a
# mechanism to communicate between themselves.
class SportPumper(UartPumper):
    _BAUD_RATE = 57600
    _START = 0x7E

    def __init__(self, tx, rx):
        super().__init__(tx, rx, self._BAUD_RATE)
        self._payload_reader = PayloadReader()
        self._payload_listener = None
        self._subscribe_ids = {}
        self._publish_ids = {}
        self._has_id = False

    def add_subscriber(self, physical_id, callback):
        self._subscribe_ids[physical_id] = callback

    def add_publisher(self, physical_id, callback):
        self._publish_ids[physical_id] = callback

    def _consume(self, b, is_clear):
        if b == self._START:
            self._has_id = False
        elif not self._has_id:
            self._has_id = True
            physical_id = b
            # Check if we want to listen for data published by another device during this slot.
            self._payload_listener = self._subscribe_ids.get(physical_id)
            if self._payload_listener:
                self._payload_reader.reset()
            else:
                # Check if we want to publish data during this slot.
                self._handle_publish(physical_id, is_clear)
        elif self._payload_listener:
            finished = self._payload_reader.consume(b)
            if finished:
                payload = self._payload_reader.get_payload()
                if payload:
                    self._payload_listener(payload)
                self._payload_listener = None
        else:
            _logger.debug("ignoring 0x02X", b)

    def _handle_publish(self, physical_id, is_clear):
        listener = self._publish_ids.get(physical_id)

        if not listener:
            return

        if is_clear():
            listener(self._uart.write)
        else:
            # This could happen if we're reading too slowly or if some other device has stolen this slot.
            _logger.error("%s slot already contains data", PhysicalId.name(physical_id))
