from Electric.Overhead.Structure.beamtype import BeamType
from gui.viewmodel.beam_vm import BeamVM
from model.beam import Beam


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
