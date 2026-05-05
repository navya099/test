from gui.viewmodel.bracket_fitting_vm import BracketFittingViewModel
from model.bracket_fitting import FittingDATA
import tkinter as tk

class TKBracketFittngAdapter:
    @staticmethod
    def from_vm(data: BracketFittingViewModel):
        return FittingDATA(
            index=-1,
            xoffset=data.xoffset.get(),
            yoffset=data.yoffset.get(),
            rotation=data.rotation.get(),
            label=data.name_var.get()
        )
    @staticmethod
    def from_dto(data: FittingDATA):
        return BracketFittingViewModel(
            name_var=tk.StringVar(value=data.label),
            xoffset=tk.DoubleVar(value=data.xoffset),
            yoffset=tk.DoubleVar(value=data.yoffset),
            rotation=tk.DoubleVar(value=data.rotation),
        )
