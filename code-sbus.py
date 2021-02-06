import board
import busio

from sbus_frame import SBusFrame

SBUS_RX = board.D7
SBUS_BAUD = 100000

uart = busio.UART(None, SBUS_RX, baudrate=SBUS_BAUD)


def dump(frame):
    print(":".join("{:03X}".format(ch) for ch in frame.channels))

    print("lost_frame:", frame.lost_frame)
    print("failsafe:", frame.failsafe)


parser = SBusFrame()

searching = True
offset = 0
# TODO: should I bother storing start and stop bytes?
buffer = bytearray(25)

while True:
    data = uart.read(1)

    if data is not None:
        ch = data[0]

        if offset == 0:
            if ch == SBusFrame.SBUS_START_BYTE:
                searching = False
                buffer[0] = SBusFrame.SBUS_START_BYTE
                offset = 1
            elif not searching:
                print("bad frame start")
                searching = True
        else:
            buffer[offset] = ch
            if offset != 24:
                offset += 1
            else:
                offset = 0
                if ch == SBusFrame.SBUS_END_BYTE:
                    parser.parse(buffer)
                    dump(parser)
                else:
                    print("bad frame")
                    searching = True
