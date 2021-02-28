import logging

from sport.multi_payload import MultiPayloadReader
from sport.physical_id import PhysicalId
from util.loop import loop

_logger = logging.getLogger("exchange")


class SportExchange:
    _MSP_CLIENT_FRAME = 0x30
    _MSP_SERVER_FRAME = 0x32

    _DEFAULT_TRANSMIT_ID = PhysicalId.ID27
    _DEFAULT_RECEIVE_ID = PhysicalId.ID13

    def __init__(self, pumper, transmit_id=_DEFAULT_TRANSMIT_ID, receive_id=_DEFAULT_RECEIVE_ID):
        pumper.add_publisher(transmit_id, self._transmit)
        pumper.add_subscriber(receive_id, self._receive)
        self._multi_payload_reader = MultiPayloadReader()
        self._sensors = None
        self._sensor_loop = None
        self._commands = {}

    def set_sensors(self, sensors):
        self._sensors = sensors
        self._sensor_loop = loop(len(sensors))

    def set_commands(self, commands):
        self._commands = commands

    def _transmit(self, writer):
        print("can transmit to", writer)
        if self._sensors:
            sensor = self._sensors[next(self._sensor_loop)]
            print(sensor.get_value())

    def _receive(self, payload):
        if payload.frame_id != self._MSP_CLIENT_FRAME:
            _logger.warning("ignoring payload with frame ID %d", payload.frame_id)
            return

        result = self._multi_payload_reader.consume(payload.data)
        if result:
            print(result.command, len(result.payload), result.error)
            command = self._commands.get(result.command)
            print(command)


