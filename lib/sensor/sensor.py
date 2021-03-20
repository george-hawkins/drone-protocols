import struct

from sport.frame import FrameId


class SensorEncoder:
    _STRUCT_FORMAT = "<HI"

    @staticmethod
    def encode(sensor, frame):
        frame.set_id(FrameId.SENSOR)
        struct.pack_into(
            SensorEncoder._STRUCT_FORMAT,
            frame.payload,
            0,
            sensor.id,
            sensor.get_value(),
        )


class Sensor:
    def __init__(self, sensor_id, get_value):
        self.id = sensor_id
        self.get_value = get_value


class GeneratorSensor(Sensor):
    def __init__(self, sensor_id, generator):
        super().__init__(sensor_id, lambda: next(generator))
