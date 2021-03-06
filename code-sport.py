import logging
import board

from msp.command.core import MspApiVersionCommand, MspSaveAllCommand
from msp.command.vtx import (
    MspVtxConfigCommand,
    MspVtxTableBandCommand,
    MspVtxTablePowerLevelCommand,
    MspSetVtxConfigCommand,
)
from config.vtx import VtxConfig
from sbus.sbus_pumper import SbusPumper
from sensor.demo import create_demo_2_sensor, create_demo_1_sensor
from sport.coordinator import SportCoordinator
from sport.sport_pumper import SportPumper
from util.uart_pumper import PumpMaster

_logger = logging.getLogger("main")


def dump_sbus_frame(frame):
    print(":".join("{:03X}".format(ch) for ch in frame.channels))

    print("lost_frame:", frame.lost_frame)
    print("failsafe:", frame.failsafe)


class Main:
    _SPORT_TX = board.TX
    _SPORT_RX = board.RX

    _SBUS_RX = board.A3

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
            MspSaveAllCommand(configs),
        ]
        return {c.id: c for c in commands}

    @staticmethod
    def _get_sensors():
        return [create_demo_1_sensor(), create_demo_2_sensor()]

    def _setup_sport(self, master):
        pumper = SportPumper(self._SPORT_TX, self._SPORT_RX)
        coordinator = SportCoordinator(pumper)
        coordinator.set_sensors(self._get_sensors())
        coordinator.set_commands(self._get_commands())
        master.register(pumper)

    def _setup_sbus(self, master):
        pumper = SbusPumper(self._SBUS_RX, dump_sbus_frame)
        master.register(pumper)

    def run(self):
        pump_master = PumpMaster()

        # Bottom left -
        self._setup_sport(pump_master)
        self._setup_sbus(pump_master)

        while True:
            pump_master.pump_all()


Main().run()
