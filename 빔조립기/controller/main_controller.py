import pandas as pd
from scipy.optimize import bracket

from controller.library_controller import IndexLibrary
from controller.poleinstall_controller import PoleInstall
from model.beam_assembly import BeamAssembly

SHEET_ID = "1z0aUcuZCxOQp2St3icbQMbOkrSPfJK_8iZ2JKFDbW8c"
SHEET_NAME = "freeobj"  # ← 원하는 시트 이름
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

class MainProcess:
    def __init__(self, master):
        self.master = master

    _cached_df = None

    def run(self):
        if MainProcess._cached_df is None:
            MainProcess._cached_df = pd.read_csv(URL)
        df = MainProcess._cached_df
        idxlib = IndexLibrary(df)

        # 설치 시작
        install = PoleInstall(
            station=self.master.station.get(),
            pole_number=self.master.pole_number.get(),
            railtype=self.master.railtype.get(),
            rail_count=self.master.rail_count.get(),
            left_x=self.master.left_x.get(),
            right_x=self.master.right_x.get(),
            beam_type=self.master.structure_frame.beam_type.get(),
            pole_type=self.master.structure_frame.pole_type.get(),
            pole_width=self.master.structure_frame.pole_width.get(),
            pole_height=self.master.structure_frame.pole_height.get(),
            pole_count=2
        )
        install.brackets = self.master.bracket_frame.bracket_vars
        install.beam = BeamAssembly.create_from_install(install, idxlib)
        return install

