from sensor.sensor import GeneratorSensor
from sensor.sensor_id import SensorId
from util.util import loop


# In Betaflight, IDs `T1_FIRST` and `T2_FIRST` are pseudo-sensors that are actually used to report internal
# Betaflight state (encoded in the digits of the sensor values). These IDs are displayed "Tmp1" and "Tmp2"
# in OpenTX. Here the IDs are used simply for demo sensors that continuously loop through the values [0, 99999]
# forward (for `T1_FIRST`) and backward (for `T2_FIRST`).


def create_demo_1_sensor():
    return GeneratorSensor(SensorId.T1_FIRST, loop(100000))


def create_demo_2_sensor():
    return GeneratorSensor(SensorId.T2_FIRST, loop(99999, -1, -1))
