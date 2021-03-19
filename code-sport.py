import logging
import board

from msp.command.core import MspApiVersionCommand, MspSaveAllCommand
from msp.command.vtx import MspVtxConfigCommand, MspVtxTableBandCommand, MspVtxTablePowerLevelCommand, \
    MspSetVtxConfigCommand
from config.vtx import VtxConfig
from sensor.demo import create_demo_2_sensor, create_demo_1_sensor
from sport.exchange import SportExchange
from sport.sport_pumper import SportPumper
from uart_pumper import UartPumper, Poller

_logger = logging.getLogger("main")


class HostPumper(UartPumper):
    def _consume(self, b, is_clear):
        print("{:02X}".format(b), is_clear())


class Main:
    _HOST_TX = board.A2
    _HOST_RX = board.A3
    _HOST_BAUD_RATE = 115200

    _SPORT_TX = board.TX
    _SPORT_RX = board.RX

    @staticmethod
    def _get_commands():
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
        return {c.id: c for c in commands}

    @staticmethod
    def _get_sensors():
        return [create_demo_1_sensor(), create_demo_2_sensor()]

    def _setup_sport(self, poller):
        pumper = SportPumper(self._SPORT_TX, self._SPORT_RX)
        exchange = SportExchange(pumper)
        exchange.set_sensors(self._get_sensors())
        exchange.set_commands(self._get_commands())
        poller.register(pumper)

    def run(self):
        poller = Poller()

        self._setup_sport(poller)

        host_pumper = HostPumper(self._HOST_TX, self._HOST_RX, self._HOST_BAUD_RATE)
        poller.register(host_pumper)

        while True:
            poller.poll()


Main().run()
