from adapter.tk_raildata_adapter import TKRaildataAdapter
from model.pole_install import PoleInstall

class TkInstallAdapter:
    @staticmethod
    def collect(master) -> PoleInstall:

        return PoleInstall(
            station=master.station.get(),
            pole_number=master.pole_number.get(),
            rail_count=master.rail_count.get(),
            left_x=master.left_x.get(),
            right_x=master.right_x.get(),
            beam_type=master.structure_frame.beam_type.get(),
            pole_type=master.structure_frame.pole_type.get(),
            pole_width=master.structure_frame.pole_width.get(),
            pole_height=master.structure_frame.pole_height.get(),
            pole_count=master.structure_frame.pole_count.get(),
            rails=TKRaildataAdapter.collect(master.bracket_frame.bracket_vars),
        )