import logging
from sensor.sensor import SensorEncoder
from sport.msp_response_encoder import MspResponseEncoder

from sport.multi_payload import MultiPayloadReader, MspError
from sport.frame import FrameId, FrameEncoder
from sport.physical_id import PhysicalId
from util.buffer import ReadBuffer, WriteBuffer
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
        self._msp_response_encoder = MspResponseEncoder()
        self._has_msp_response = False
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
        if self._has_msp_response:
            self._transmit_msp_response(write)
        elif self._sensors:
            self._transmit_sensor_value(write)

    def _transmit_sensor_value(self, write):
        sensor = self._sensors[next(self._sensor_loop)]
        sensor_data = self._sensor_encoder.encode(sensor)
        self._write_frame(write, FrameId.SENSOR, sensor_data)

    def _transmit_msp_response(self, write):
        # TODO: don't allocate this buffer per call and share it with sensor transmit logic.
        frame_payload = WriteBuffer()
        frame_payload.set_buffer(memoryview(bytearray(6)))
        self._has_msp_response = self._msp_response_encoder.encode(frame_payload)
        self._write_frame(write, FrameId.MSP_SERVER, frame_payload.get_buffer(use_offset=False))

    def _write_frame(self, write, frame_id, frame_data):
        frame_data = self._frame_encoder.encode(frame_id, frame_data)
        write(frame_data)

    def _receive(self, frame):
        if frame.id != FrameId.MSP_CLIENT:
            _logger.warning("ignoring frame with ID %02X", frame.id)
            return

        if self._has_msp_response:
            _logger.warning("MSP frame received while still sending previous response - discarding old response")
            self._has_msp_response = False

        result = self._multi_payload_reader.consume(frame.payload)

        if not result:
            return

        self._has_msp_response = True

        if result.error is not None:
            self._msp_response_encoder.set_error(result.error, result.command_id)
            return

        command = self._commands.get(result.command_id)

        if command is None:
            _logger.error("no handler registered for command %d", result.command_id)
            self._msp_response_encoder.set_error(MspError.ERROR, result.command_id)
            return

        # TODO: perhaps rename `result.payload` to `result.request`.
        response_buffer = self._msp_response_encoder.set_command(command.id)
        command.handle_request(result.payload, response_buffer)
