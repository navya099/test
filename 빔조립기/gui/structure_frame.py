from tkinter import ttk
from gui.beam_frame import BeamFrame
from gui.pole_frame import PoleFrame

class StructureFrame(ttk.LabelFrame):
    def __init__(self, master, event):
        super().__init__(master, text="구조물 정보")
        self.event = event
        self.pole_frame = PoleFrame(self, self.event)
        self.pole_frame.grid(row=0, column=0, columnspan=2, sticky="w")
        self.beam_frame = BeamFrame(self, self.event)
        self.beam_frame.grid(row=1, column=0, columnspan=2, sticky="w")

    def rebuild_from_install(self, beams, poles):
        # pole
        self.master.isloading = True
        self.current_section.pole_count_var.set(len(poles))
        self.pole_frame.rebuild_poles()  # UI/VM 초기화

        # 각 PoleVM에 install 데이터 반영
        for vm, pole in zip(self.pole_vars, poles):
            vm.poletype.set(pole['type'])  # Enum -> String
            vm.polespec.set(pole['width'])
            vm.pole_length.set(pole['length'])
            vm.gauge.set(pole['xoffset'])
            # ⭐ 핵심
            vm.base_rail_index.set(pole['base_rail_index'])
            # uid 매칭
            for rail in self.rails:
                if rail.index_var.get() == pole['base_rail_index']:
                    vm.base_rail_uid.set(rail.uid)
                    break

        self._refresh_pole_rail_combos()

        # beam
        self.current_section.beam_count.set(len(beams))
        self.beam_frame.rebuild_beams()
        for vm, beam in zip(self.beam_vars, beams):
            vm.beamtype.set(beam['type'])
            vm.start_pole.set(beam['start_pole'])
            vm.end_pole.set(beam['end_pole'])
        self.master.isloading = False

    

