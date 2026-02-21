from gui.viewmodel.equipment_vm import EquipmentVM
from model.equipment import EquipmentDTO
import tkinter as tk

class TkEquipmentAdapter:
    @staticmethod
    def collect(tk_vms: list):
        dtos = []
        for i, vm in enumerate(tk_vms):
            dtos.append(
                EquipmentDTO(
                    name=vm.name_var.get(),
                    xoffset=vm.x_var.get(),
                    yoffset=vm.y_var.get(),
                    rotation=vm.rotation_var.get(),
                    base_rail_index=vm.base_rail_index_var.get(),
                )
            )
        return dtos

    @staticmethod
    def from_dto(data: EquipmentDTO) -> EquipmentVM:
        return EquipmentVM(
            name_var=tk.StringVar(value=data.name),
            x_var=tk.DoubleVar(value=data.xoffset),
            y_var=tk.DoubleVar(value=data.yoffset),
            rotation_var=tk.DoubleVar(value=data.rotation),
            base_rail_index_var=tk.IntVar(value=data.base_rail_index),
        )

