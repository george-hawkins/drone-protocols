import logging
from sport.control_code import SportControlCode

from sport.frame import FrameDecoder, FrameEncoder
from sport.physical_id import PhysicalId
from util.uart_pumper import UartPumper

_logger = logging.getLogger("sport_pumper")


# The Sport bus is managed by the FrSky receiver. It cycles through a sequence of physical IDs, transmitting an
# invitation for each ID in turn to transmit. It pauses for about 12ms after each invite, giving the device with the
# current ID a chance to transmit.
# Simple devices just transmit their own data during their transmission slot and are uninterested in the data
# transmitted by other devices. However, devices can also listen out for what each other transmits and use this as a
# mechanism to communicate between themselves.
# Important: the physical ID identifies a device - when invited to transmit, a given device can write data to the bus
# and this data starts with a frame ID. The frame ID identifies the type of data and a device can use a different ID
# each time its given an opportunity to transmit, e.g. it might transmit a current value one time, voltage the next
# and temperature the next.
class SportPumper(UartPumper):
    _BAUD_RATE = 57600

    def __init__(self, tx, rx):
        super().__init__(tx, rx, self._BAUD_RATE, echo=True)
        self._frame_decoder = FrameDecoder()
        self._frame_encoder = FrameEncoder()
        self._frame_listener = None
        self._subscribe_ids = {}
        self._publish_ids = {}
        self._has_physical_id = False

    def add_subscriber(self, physical_id, subscriber):
        self._subscribe_ids[physical_id] = subscriber

    def add_publisher(self, physical_id, publisher):
        self._publish_ids[physical_id] = publisher

    def _consume(self, b, is_clear):
        if b == SportControlCode.START:
            self._has_physical_id = False
        elif not self._has_physical_id:
            self._has_physical_id = True
            physical_id = b
            # Check if we want to listen for data published by another device during this slot.
            self._frame_listener = self._subscribe_ids.get(physical_id)
            if self._frame_listener:
                self._frame_decoder.reset()
            else:
                # Check if we want to publish data during this slot.
                self._handle_publish(physical_id, is_clear)
        elif self._frame_listener:
            frame = self._frame_decoder.decode(b)
            if frame:
                if frame is not FrameDecoder.INVALID_FRAME:
                    self._frame_listener(frame)
                self._frame_listener = None
        else:
            _logger.debug("ignoring 0x%02X", b)

    def _handle_publish(self, physical_id, is_clear):
        write_frame = self._publish_ids.get(physical_id)

        if not write_frame:
            return

        if is_clear():
            send = write_frame(self._frame_encoder.get_frame())
            if send:
                encoded_frame = self._frame_encoder.encode()
                self._write(encoded_frame)
        else:
            # This could happen if we're reading too slowly or if some other device has stolen this slot.
            _logger.error("%s slot is not clear for writing", PhysicalId.name(physical_id))
