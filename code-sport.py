import board
import busio
import array
from collections import namedtuple


class Fssp:
    START_STOP = 0x7E

    DLE = 0x7D
    DLE_XOR = 0x20

    DATA_FRAME = 0x10
    MSPC_FRAME_SMARTPORT = 0x30  # MSP client frame
    MSPS_FRAME = 0x32  # MSP server frame

    # ID of sensor. Must be something that is polled by FrSky RX
    SENSOR_ID1 = 0x1B
    SENSOR_ID2 = 0x0D


Payload = namedtuple("Payload", "frameId valueId data")


# Notes:
#
# You can find sensor IDs in https://github.com/opentx/opentx/blob/2.3/radio/src/telemetry/frsky.h
#
# Note: time.monotonic_ns() appears to be the time since the last _hard_ reset.
# It's a uint64_t value and and so will only roll over after 584 years.
# On a SAMD51, the granularity is around 120us.


class AbstractSensor:
    def __init__(self, sensor_id):
        self.sensor_id = sensor_id.to_bytes(2, "little")

    def get_value(self):
        raise NotImplementedError("get_value")


class Tmp1Sensor(AbstractSensor):
    T1 = 0x0400

    def __init__(self):
        super().__init__(self.T1)
        self._count = 0

    def get_value(self):
        self._count += 1
        if self._count > 99999:
            self._count = 0
        return self._count


class Tmp2Sensor(AbstractSensor):
    T2 = 0x0410

    def __init__(self):
        super().__init__(self.T2)
        self._count = 0

    def get_value(self):
        self._count -= 1
        if self._count < 0:
            self._count = 99999
        return self._count


def looper(s):
    i = 0
    end = len(s)
    while True:
        yield s[i]
        i += 1
        if i == end:
            i = 0


class SmartPort:
    SPORT_BAUD = 57600
    PAYLOAD_SIZE = 7  # TODO: see if you can work this out in Python from struct description - remember it's packed, so you want 7 and 8 as the answer.
    SERVICE_TIMEOUT_NS = 1000 * 1000  # 1ms.

    def __init__(self, sport_tx, sport_rx, sensors=None):
        self.clear_to_send = False
        self.rx_buffer = array.array("B", (0 for _ in range(0, self.PAYLOAD_SIZE)))
        self.rx_offset = 0
        self.skip_until_start = True
        self.awaiting_sensor_id = False
        self.byte_stuffing = False
        self.checksum = 0
        self.id_cycle_count = 0
        self.t1_cnt = 0
        self.t2_cnt = 0
        self.skip_requests = 0

        self.uart = busio.UART(sport_tx, sport_rx, baudrate=self.SPORT_BAUD)

        if sensors is not None:
            ids = list(map(lambda s: s.sensor_id, sensors))
            assert all(ids.count(i) == 1 for i in ids)  # Check all IDs are unique.
            self.sensors = sensors
            self.sensors_iter = looper(sensors)

    def ready_to_send(self):
        return self.uart.in_waiting == 0

    def data_receive(self, c):
        if c == Fssp.START_STOP:
            self.clear_to_send = False
            self.rx_offset = 0
            self.awaiting_sensor_id = True
            self.skip_until_start = False
            return None
        elif self.skip_until_start:
            print("Ignoring {:02X}".format(c))
            return None

        # TODO: add in comments from original C, e.g. of setting `clear_to_send` to `True` below.
        if self.awaiting_sensor_id:
            self.awaiting_sensor_id = False
            if c == Fssp.SENSOR_ID1 and self.ready_to_send():
                self.clear_to_send = True
                self.skip_until_start = True
            elif c == Fssp.SENSOR_ID2:
                self.checksum = 0
            else:
                self.skip_until_start = True
        else:
            if c == Fssp.DLE:
                self.byte_stuffing = True
                return None
            elif self.byte_stuffing:
                c ^= Fssp.DLE_XOR
                self.byte_stuffing = False

            self.checksum += c

            if self.rx_offset < self.PAYLOAD_SIZE:
                self.rx_buffer[self.rx_offset] = c
                self.rx_offset += 1
            else:
                self.skip_until_start = True

                self.checksum = (self.checksum & 0xFF) + (self.checksum >> 8)
                if self.checksum == 0xFF:
                    # TODO: consider `memoryview` or look at working with `struct`.
                    frame_id = self.rx_buffer[0]
                    value_id = int.from_bytes(self.rx_buffer[1:3], "little")
                    data = self.rx_buffer[3:7]
                    print("frame_id:", frame_id)
                    print("value_id:", value_id)
                    print("data:", data)
                    return Payload(frame_id, value_id, data)

        return None

    @staticmethod
    def get_checksum(total):
        checksum = total & 0xFFFF
        while checksum > 0xFF:
            checksum = (checksum & 0xFF) + (checksum >> 8)
        return 0xFF - checksum

    # TODO: which is better `bytes([x])` or `x.to_bytes(1, "little")`.
    def write(self, b):
        # TODO: should check count returned by `write`.
        self.uart.write(bytes([b]))

    def send_byte(self, b):
        sent = 0
        if b == Fssp.DLE or b == Fssp.START_STOP:
            self.write(Fssp.DLE)
            sent += 1
            b = b ^ Fssp.DLE_XOR
        self.write(b)
        sent += 1
        return sent

    def write_frame(self, payload):
        sent = 0
        total = 0
        for b in payload:
            sent += self.send_byte(b)
            total += b
        sent += self.send_byte(self.get_checksum(total))
        # The UART will see the sent data echoed on its RX - ignore this data.
        # TODO: remember to remove this if you get half-duplex working on a single pin.
        self.uart.read(sent)

    def send_package(self, sensor_id, value):
        # TODO: look at working with `struct`.
        payload = bytes([Fssp.DATA_FRAME]) + sensor_id + value.to_bytes(4, "little")
        self.write_frame(payload)

    # TODO: rename private methods and field to start with `_`.
    def process(self, payload):
        if self.skip_requests > 0:
            self.skip_requests -= 1
        # TODO: else check for MSP payloads.
        # TODO: is self.skip_requests just some weird EEPROM related thing that we can live without?

        # TODO: are `clear_to_send` or `skip_requests` really needed?

        if not self.clear_to_send or self.skip_requests > 0:
            return

        # TODO: handle smartPortMspReplyPending.

        if self.sensors is not None:
            sensor = next(self.sensors_iter)
            self.send_package(sensor.sensor_id, sensor.get_value())
            # TODO: `clear_to_send` will become False anyway when we return and `pump` is next called.
            self.clear_to_send = False

    def pump(self):
        payload = None
        self.clear_to_send = False
        while self.uart.in_waiting > 0 and not payload:
            c = self.uart.read(1)[0]
            payload = self.data_receive(c)

        # Note that `payload` can be `None` at this point - `process` will do work even in this case.
        self.process(payload)


# TODO: note on STM32 FC boards it's always a **TX** pin that's used for bi-directional SPORT coms.
SPORT_RX = board.RX
SPORT_TX = board.TX

sensors = [Tmp1Sensor(), Tmp2Sensor()]
sport = SmartPort(SPORT_TX, SPORT_RX, sensors)

while True:
    sport.pump()
