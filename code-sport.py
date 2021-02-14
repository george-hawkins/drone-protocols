import board
import busio
import array
from collections import namedtuple

from msp import MspApiVersionCommand, MspErrorResponse, MspVtxConfigCommand, VtxConfig, MspVtxTableBandCommand, \
    MspVtxTablePowerLevelCommand, MspSetVtxConfigCommand, MspSaveAllCommand
from msp_request import MspPackage, MspError


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


Payload = namedtuple("Payload", "frame_id value_id data")


# Notes:
#
# You can find sensor IDs in https://github.com/opentx/opentx/blob/2.3/radio/src/telemetry/frsky.h
#
# Note: time.monotonic_ns() appears to be the time since the last _hard_ reset.
# It's a uint64_t value and and so will only roll over after 584 years.
# On a SAMD51, the granularity is around 120us.


class AbstractSensor:
    def __init__(self, sensor_id):
        self.sensor_id = sensor_id.to_bytes(2, SmartPort.BYTE_ORDER)

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


def looper(end):
    i = 0
    while True:
        yield i
        i = (i + 1) % end


class SmartPort:
    SPORT_BAUD = 57600
    PAYLOAD_SIZE = 7  # TODO: see if you can work this out in Python from struct description - remember it's packed, so you want 7 and 8 as the answer.
    SERVICE_TIMEOUT_NS = 1000 * 1000  # 1ms.
    BYTE_ORDER = "little"

    def __init__(self, sport_tx, sport_rx, sensors=None):
        self.clear_to_send = False
        # TODO: why did I do this with `array` - change to `bytearray`.
        self.rx_buffer = array.array("B", (0 for _ in range(0, self.PAYLOAD_SIZE)))
        self.rx_offset = 0
        self.skip_until_start = True
        self.awaiting_sensor_id = False
        self.byte_stuffing = False
        self.checksum = 0
        self.id_cycle_count = 0
        self.t1_cnt = 0
        self.t2_cnt = 0
        self.msp_package = MspPackage()
        self.msp_response = None
        self.msp_seq_iter = looper(0x10)

        self.uart = busio.UART(sport_tx, sport_rx, baudrate=self.SPORT_BAUD)

        if sensors is not None:
            ids = list(map(lambda s: s.sensor_id, sensors))
            assert all(ids.count(i) == 1 for i in ids)  # Check all IDs are unique.
            self.sensors = sensors
            self.sensors_iter = looper(len(sensors))

        self.msp_commands = self.get_msp_commands()

    @staticmethod
    def get_msp_commands():
        vtx_config = VtxConfig()
        configs = [vtx_config]  # At the moment there's just the VTX config.
        commands = [
            MspApiVersionCommand(),
            MspVtxConfigCommand(vtx_config),
            MspVtxTableBandCommand(vtx_config),
            MspVtxTablePowerLevelCommand(vtx_config),
            MspSetVtxConfigCommand(vtx_config),
            MspSaveAllCommand(configs)
        ]
        return {c.command: c for c in commands}

    # TODO: WARNING - if you move to reading more that 1 byte at a time you also have to check that there are
    #  no bytes left in the buffer of bytes that you read.
    def ready_to_send(self):
        return self.uart.in_waiting == 0

    # TODO: this is all a bit odd, what exactly are the structures we expect to see? Maybe:
    #   * [ START_STOP, SENSOR_ID1 ] and empty input buffer = clear-to-send
    #   * [ START_STOP, SENSOR_ID2, p1, ..., pn, checksum ] = MSP (and possibly other things) packet.
    #   Note: p1 to pn will reduce down to 7 bytes, i.e. PAYLOAD_SIZE, after `byte_stuffing` logic is applied.
    # TODO: print out all blocks starting with START_STOP, with each byte (including START_STOP) preceded
    #  by time in micros since last byte, is [ START_STOP, SENSOR_ID1 ] followed by an unusually long pause?
    #  At the moment we break out of the calling loop:
    #  * If we hit [ START_STOP, SENSOR_ID1 ] followed by no characters (both this fn and caller check for no further chars).
    #  * If we get a packet.
    #  However, if we get a packet we won't also get clear-to-send until we reenter this loop.
    #  Surely there's a clearer way of expressing this flow.
    #  If we get a packet we want to ready a response.
    #  If we get a clear to send we see if we've got an outstanding response otherwise we send a sensor value.
    #
    # Proposal:
    # Have logic that looks out for RX advertisements to talk, i.e. START_STOP followed by an ID (is START_STOP
    # really just START or does it appear elsewhere?)
    # Have separate logic that decides what to do - use the opportunity to talk (send sensor or MSP data) for
    # SENSOR_ID1 or listen out for MSP data for SENSOR_ID2.
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

                self.checksum &= 0xFFF
                self.checksum = (self.checksum & 0xFF) + (self.checksum >> 8)

                if self.checksum == 0xFF:
                    # TODO: consider `memoryview` or look at working with `struct`.
                    frame_id = self.rx_buffer[0]
                    value_id = int.from_bytes(self.rx_buffer[1:3], self.BYTE_ORDER)
                    data = self.rx_buffer[3:7]
                    # TODO: if `frame_id` is anything other than MSPC_FRAME_SMARTPORT (see `contains_msp`) we ignore
                    #  the payload later - maybe it would be better to discard it here.
                    # TODO: splitting out `value_id` and `data` is stupid - really it's 6 bytes of opaque data. See note on smartPortPayload_t definition.
                    print("MSP frame: ", "".join("\\x{:02X}".format(ch) for ch in self.rx_buffer).join(['"', '"']))
                    return Payload(frame_id, value_id, data)
                else:
                    print("Error: invalid checksum:", self.checksum)

        return None

    # TODO: `self.checksum` is the incoming checksum, this is the calculation for the outgoing checksum.
    @staticmethod
    def get_checksum(total):
        checksum = total & 0xFFFF
        while checksum > 0xFF:
            checksum = (checksum & 0xFF) + (checksum >> 8)
        return 0xFF - checksum

    # TODO: which is better `bytes([x])` or `x.to_bytes(1, self.BYTE_ORDER)`.
    def write(self, b):
        # TODO: should check count returned by `write`.
        self.uart.write(bytes([b]))
        # print("{:02X}".format(b))

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
        # print("--")

    def send_package(self, sensor_id, value):
        # TODO: look at working with `struct`.
        payload = bytes([Fssp.DATA_FRAME]) + sensor_id + value.to_bytes(4, self.BYTE_ORDER)
        self.write_frame(payload)

    # TODO: smartPortPayload_t is defined as:
    #  typedef struct {
    #      uint8_t  frameId;
    #      uint16_t valueId;
    #      uint32_t data;
    #  } __attribute__((packed)) smartPortPayload_t;
    #  The packed means it's 7 bytes rather than 8.
    #  But really `frameId` and that it's 7 bytes in total are the only fixed thing.
    #  For DATA_FRAME, `frameId` is followed by `valueId` (2 bytes) and `data` (4 bytes).
    #  For MSPS_FRAME, `frameId` is followed by 6 bytes of data.
    #  So either model things using a union or as two different structs.
    def send_msp_response(self, data):
        assert len(data) == 6
        payload = bytes([Fssp.MSPS_FRAME]) + data
        self.write_frame(payload)

    # TODO: confusing naming - rename `payload` to frame or frame_buf.
    def handle_msp_frame(self, payload):
        result = self.msp_package.handle_frame(payload)
        if result is None:
            return None
        if result.error is None:
            command = self.msp_commands.get(result.command)
            if command is None:
                print("Error: no command for {} {}".format(result.command, result.payload))
                return MspErrorResponse(MspError.ERROR, result.command)
            else:
                return command.get_response(result.payload)
        else:
            return MspErrorResponse(result.error, result.command)

    @staticmethod
    def contains_msp(payload):
        return payload.frame_id == Fssp.MSPC_FRAME_SMARTPORT

    # TODO: what happens when we see traffic from other sensors on the same bus?

    # TODO: rename private methods and field to start with `_`.
    def process(self, payload):
        if payload is not None and self.contains_msp(payload):
            if self.msp_response is not None:
                print("Warning: MSP payload received while still sending previous response - discarding old response")
            # TODO: this is stupid - we're just reversing a pointless split we did when creating the payload.
            data = payload.value_id.to_bytes(2, self.BYTE_ORDER) + payload.data
            self.msp_response = self.handle_msp_frame(data)

        # TODO: is `clear_to_send` really needed?
        if not self.clear_to_send:
            return

        if self.msp_response:
            # TODO: make 6 a constant.
            frame_buf = bytearray(6)
            # TODO: bundle `msp_seq_iter` and `send_msp_response` and the other MSP logic into its own class.
            finished = self.msp_response.write(next(self.msp_seq_iter), frame_buf)
            if finished:
                self.msp_response = None
            self.send_msp_response(frame_buf)
            self.clear_to_send = False
            return

        # TODO:
        #  The remote side has given us a slot of about 1ms to transmit something.
        #  The code below assumes that every sensor will always have a value it wants to transmit.
        #  So we simply ask the `next` sensor for a value and transmit it.
        #  However, in the original code a sensor might not currently have anything to transmit.
        #  In such a case we could loop, taking care not to run over our 1ms slot, until a sensor has something to say.
        #  We'd replace the `clear_to_send` check above with a while loop.

        if self.sensors is not None:
            sensor = self.sensors[next(self.sensors_iter)]
            self.send_package(sensor.sensor_id, sensor.get_value())
            # TODO: `clear_to_send` will become False anyway when we return and `pump` is next called.
            #  However, see note above - it's not a given that a sensor must have something to transmit.
            #  In which case we wouldn't automatically set `clear_to_send` here but would loop until someone sent (or we ran out of time).
            self.clear_to_send = False

    def pump(self):
        payload = None
        self.clear_to_send = False
        # TODO: see WARNING on `ready_to_send` method.
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
