from adapter.tk_raildata_adapter import TKRaildataAdapter
from model.pole_install import PoleInstall
from model.tkraildata import TKRailData


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

    @staticmethod
    def apply(master, install: PoleInstall):
        master.station.set(install.station)
        master.pole_number.set(install.pole_number)
        master.rail_count.set(install.rail_count)
        master.left_x.set(install.left_x)
        master.right_x.set(install.right_x)

        sf = master.structure_frame
        sf.beam_type.set(install.beam_type)
        sf.pole_type.set(install.pole_type)
        sf.pole_width.set(install.pole_width)
        sf.pole_height.set(install.pole_height)
        sf.pole_count.set(install.pole_count)

        # rail은 rebuild 후 주입
        master.bracket_frame.rebuild_from_install(install.rails)
