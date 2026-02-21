from Electric.Overhead.Structure.beamtype import BeamType
from gui.viewmodel.beam_vm import BeamVM
from model.beam import Beam
import tkinter as tk

class TkBeamAdapter:
    @staticmethod
    def collect(beam_vms: list[BeamVM]) -> list[Beam]:
        beams = []
        for i, vm in enumerate(beam_vms, start=1):
            beams.append(
                Beam(
                    index=vm.index.get(),#초기화
                    type=BeamType(vm.beamtype.get()),
                    start_pole=vm.start_pole.get(),
                    end_pole=vm.end_pole.get()
                )
            )
        return beams

    @staticmethod
    def from_dto(data: Beam) -> BeamVM:
        return BeamVM(
            index=tk.IntVar(value=data.index),
            beamtype=tk.StringVar(value=data.type.value),
            start_pole=tk.IntVar(value=data.start_pole),
            end_pole=tk.IntVar(value=data.end_pole),
        )
