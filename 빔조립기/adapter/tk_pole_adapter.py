from Electric.Overhead.Pole.poletype import PoleType
from gui.viewmodel.pole_vm import PoleVM
from model.pole import Pole
import uuid
import tkinter as tk

class TkPoleAdapter:
    @staticmethod
    def collect(pole_vms: list[PoleVM]) -> list[Pole]:
        poles = []
        for vm in pole_vms:
            poles.append(
                Pole(
                    index=vm.index.get(),
                    type=PoleType(vm.poletype.get()),
                    length=vm.pole_length.get(),
                    xoffset=vm.gauge.get(),
                    width=vm.polespec.get(),
                    uid=uuid.uuid4().hex,
                    base_rail_index=vm.base_rail_index.get(),
                )
            )
        return poles

    @staticmethod
    def from_dto(data: Pole) -> PoleVM:
        return PoleVM(
            index=tk.IntVar(value=data.index),
            poletype=tk.StringVar(value=data.type.value),
            pole_length=tk.DoubleVar(value=data.length),
            gauge=tk.DoubleVar(value=data.xoffset),
            polespec=tk.StringVar(value=data.width),
            base_rail_index=tk.IntVar(value=data.base_rail_index),
            base_rail_uid=tk.StringVar(value=data.uid),
        )
