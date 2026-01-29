import pandas as pd
from controller.library_controller import IndexLibrary
from model.beam_assembly import BeamAssembly
from model.pole_install import PoleInstall
from resolver.bracket_resolver import BracketResolver

SHEET_ID = "1z0aUcuZCxOQp2St3icbQMbOkrSPfJK_8iZ2JKFDbW8c"
SHEET_NAME = "freeobj"  # ← 원하는 시트 이름
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

class MainProcess:
    def __init__(self):
        self._cached_df = None

    def run(self, dto: PoleInstall):
        if self._cached_df is None:
            self._cached_df = pd.read_csv(URL)
        df = self._cached_df
        idxlib = IndexLibrary(df)

        # 🔹 여기서 bracket 보정
        all_brackets = [
            b for rail in dto.rails for b in rail.brackets
        ]
        BracketResolver.resolve(all_brackets, idxlib)

        dto.beam_assembly = BeamAssembly.create_from_install(dto, idxlib)
        return dto

