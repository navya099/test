from gui.viewmodel.wire_vm import WireVM
from model.wire import WireData
import tkinter as tk

class TKWireAdapter:
    @staticmethod
    def collect(data: list[WireVM]):
        dtos = []
        for i, vm in enumerate(data):
            from point3d import Point3d
            dtos.append(
                WireData(
                    name=vm.name_var.get(),
                    start = Point3d(x=vm.start_x_var.get(), y=vm.start_y_var.get(), z=vm.start_z_var.get()),
                    end= Point3d(x=vm.end_x_var.get(), y=vm.end_y_var.get(), z=vm.end_z_var.get()),
                )
            )
        return dtos

    @staticmethod
    def from_dto(data: WireData):
        return WireVM(
            name_var=tk.StringVar(value=data.name),
            start_x_var=tk.DoubleVar(value=data.start.x),
            start_y_var=tk.DoubleVar(value=data.start.y),
            start_z_var=tk.DoubleVar(value=data.start.z),
            end_x_var=tk.DoubleVar(value=data.end.x),
            end_y_var=tk.DoubleVar(value=data.end.y),
            end_z_var=tk.DoubleVar(value=data.end.z),
        )