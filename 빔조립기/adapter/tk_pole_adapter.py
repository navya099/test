from Electric.Overhead.Pole.poletype import PoleType
from gui.viewmodel.pole_vm import PoleVM
from model.pole import Pole


class TkPoleAdapter:
    @staticmethod
    def collect(pole_vms: list[PoleVM]) -> list[Pole]:
        poles = []
        for vm in pole_vms:
            poles.append(
                Pole(
                    index=None,
                    type=PoleType(vm.poletype.get()),
                    length=vm.pole_length.get(),
                    xoffset=vm.gauge.get(),
                    display_name=None,
                    width=None
                )
            )
        return poles
