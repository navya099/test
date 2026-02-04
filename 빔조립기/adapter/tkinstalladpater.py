from Electric.Overhead.Pole.poletype import PoleType
from adapter.tk_beam_adapter import TkBeamAdapter
from adapter.tk_pole_adapter import TkPoleAdapter
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
            pole_count=master.pole_count.get(),
            beam_count = master.beam_count.get(),
            poles=TkPoleAdapter.collect(master.structure_frame.pole_vars),
            beams=TkBeamAdapter.collect(master.structure_frame.beam_vars),
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
