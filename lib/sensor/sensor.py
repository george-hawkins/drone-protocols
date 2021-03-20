import struct


class SensorEncoder:
    _BUFFER_LEN = 6
    _STRUCT_FORMAT = "<HI"

    def __init__(self):
        self._buffer = bytearray(self._BUFFER_LEN)

    def encode(self, sensor):
        struct.pack_into(self._STRUCT_FORMAT, self._buffer, 0, sensor.id, sensor.get_value())
        return self._buffer


class Sensor:
    def __init__(self, sensor_id, get_value):
        self.id = sensor_id
        self.get_value = get_value


class GeneratorSensor(Sensor):
    def __init__(self, sensor_id, generator):
        super().__init__(sensor_id, lambda: next(generator))
