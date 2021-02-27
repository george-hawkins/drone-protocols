import logging
import board

from sport.multi_payload import MultiPayloadReader
from sport.physical_id import PhysicalId
from sport.sport_pumper import SportPumper
from uart_pumper import UartPumper, Poller

_HOST_TX = board.A2
_HOST_RX = board.A3
_HOST_BAUD_RATE = 115200


_SPORT_TX = board.TX
_SPORT_RX = board.RX

_TRANSMIT_ID = PhysicalId.ID27
_MSP_RECEIVE_ID = PhysicalId.ID13

_logger = logging.getLogger("main")


class HostPumper(UartPumper):
    def _consume(self, b, is_clear):
        print("{:02X}".format(b), is_clear())


_counter = 0
_multi_payload_reader = MultiPayloadReader()

_MSP_CLIENT_FRAME = 0x30
_MSP_SERVER_FRAME = 0x32


def _transmit(writer):
    global _counter
    print("can transmit to", writer, _counter)
    _counter += 1


def _receive(payload):
    global _multi_payload_reader
    print("received", payload)
    if payload.frame_id == _MSP_CLIENT_FRAME:
        result = _multi_payload_reader.consume(payload.data)
        if result:
            print(result.command, len(result.payload), result.error)
    else:
        _logger.warning("ignoring payload with frame ID %d", payload.frame_id)


class Main:
    @staticmethod
    def run():
        poller = Poller()
        host_pumper = HostPumper(_HOST_TX, _HOST_RX, _HOST_BAUD_RATE)
        sport_pumper = SportPumper(_SPORT_TX, _SPORT_RX)
        sport_pumper.add_publisher(_TRANSMIT_ID, _transmit)
        sport_pumper.add_subscriber(_MSP_RECEIVE_ID, _receive)
        poller.register(host_pumper)
        poller.register(sport_pumper)
        while True:
            poller.poll()


Main().run()
