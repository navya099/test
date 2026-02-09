from Electric.Overhead.Pole.poletype import PoleType
from adapter.tk_beam_adapter import TkBeamAdapter
from adapter.tk_pole_adapter import TkPoleAdapter
from adapter.tk_raildata_adapter import TKRaildataAdapter
from model.pole_install import PoleInstall
from model.tkraildata import TKRailData


class TkInstallAdapter:
    def collect(self, master) -> PoleInstall:
        rails = TKRaildataAdapter.collect(
            master.bracket_frame.bracket_vars
        )

        poles = TkPoleAdapter.collect(
            master.structure_frame.pole_vars
        )

        beams = TkBeamAdapter.collect(
            master.structure_frame.beam_vars  # beam도 rail 참조하면 동일
        )

        return PoleInstall(
            station=master.station.get(),
            pole_number=master.pole_number.get(),
            rail_count=master.rail_count.get(),
            pole_count=master.pole_count.get(),
            beam_count=master.beam_count.get(),
            rails=rails,
            poles=poles,
            beams=beams,
        )


    def apply(self, master, install: PoleInstall):
        master.isloading = True
        master.station.set(install.station)
        master.pole_number.set(install.pole_number)
        master.rail_count.set(install.rail_count)
        master.pole_count.set(install.pole_count)
        master.bracket_frame.rebuild_from_install(install.rails)

        sf = master.structure_frame

        sf.rebuild_from_install(install.beams, install.poles)
        master.isloading = False
        # 🔥 로드 완료 후 1회 sync
        master.event.emit("rails.updated",
                          master.bracket_frame.bracket_vars)