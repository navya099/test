from Electric.Overhead.Pole.poletype import PoleType
from gui.viewmodel.pole_vm import PoleVM
from gui.viewmodel.polebasevm import PoleBaseVM
from model.pole import Pole
import uuid
import tkinter as tk

from model.polebase import PoleBase


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
                    series=vm.polespec.get(),
                    uid=vm.base_rail_uid.get(),
                    base_rail_index=vm.base_rail_index.get(),
                    base=PoleBase(name=vm.foundation.basename_var.get(),index=-1),
                )
            )
        return poles

    @staticmethod
    def from_dto(data: Pole) -> PoleVM:
        # base가 None일 경우 대비
        base_name = data.base.name if data.base is not None else "없음"
        series = data.series if data.series is not None else data.width
        return PoleVM(
            index=tk.IntVar(value=data.index),
            poletype=tk.StringVar(value=data.type.value),
            pole_length=tk.DoubleVar(value=data.length),
            gauge=tk.DoubleVar(value=data.xoffset),
            polespec=tk.StringVar(value=series),
            base_rail_index=tk.IntVar(value=data.base_rail_index),
            base_rail_uid=tk.StringVar(value=data.uid),
            foundation=PoleBaseVM(basename_var=tk.StringVar(value=base_name)),
        )