import logging
from sensor.sensor import SensorEncoder

from sport.multi_payload import MultiPayloadReader
from sport.frame import FrameId, FrameEncoder
from sport.physical_id import PhysicalId
from util.loop import loop

_logger = logging.getLogger("exchange")


# TODO: `SportExchange` isn't a great name - it was supposed to capture the idea of a telephone exchange.
class SportExchange:
    _DEFAULT_TRANSMIT_ID = PhysicalId.ID27
    _DEFAULT_RECEIVE_ID = PhysicalId.ID13

    def __init__(self, pumper, transmit_id=_DEFAULT_TRANSMIT_ID, receive_id=_DEFAULT_RECEIVE_ID):
        pumper.add_publisher(transmit_id, self._transmit)
        pumper.add_subscriber(receive_id, self._receive)
        self._multi_payload_reader = MultiPayloadReader()
        self._frame_encoder = FrameEncoder()
        self._sensors = None
        self._sensor_loop = None
        self._sensor_encoder = None
        self._commands = {}

    def set_sensors(self, sensors):
        self._sensors = sensors
        self._sensor_loop = loop(len(sensors))
        self._sensor_encoder = SensorEncoder()

    def set_commands(self, commands):
        self._commands = commands

    def _transmit(self, write):
        if self._sensors:
            self._sensor_transmit(write)

    def _sensor_transmit(self, write):
        sensor = self._sensors[next(self._sensor_loop)]
        sensor_data = self._sensor_encoder.encode(sensor)
        frame_data = self._frame_encoder.encode(FrameId.SENSOR, sensor_data)
        write(frame_data)

    def _receive(self, frame):
        if frame.id != FrameId.MSP_CLIENT:
            _logger.warning("ignoring frame with frame ID %d", frame.id)
            return

        result = self._multi_payload_reader.consume(frame.payload)
        if result:
            print(result.command, len(result.payload), result.error)
            command = self._commands.get(result.command)
            print(command)


