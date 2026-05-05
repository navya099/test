import pandas as pd
from controller.library_controller import IndexLibrary
from model.equipment import EquipmentDTO
from model.pole_install import PoleInstall
from resolver.beam_resolver import BeamResolver
from resolver.bracket_resolver import BracketResolver
from resolver.equip_resolver import EquipmentResolver
from resolver.pole_resolver import PoleResolver

class MainProcess:
    def __init__(self, idxlib):
        self.idxlib = idxlib
        self._cached_df = None

    def run(self, dtos: list[PoleInstall]):

        for dto in dtos:
            self.run_single(dto)
    def run_single(self, dto):
        # 🔹 여기서 bracket 보정
        all_brackets = [
            b for rail in dto.rails for b in rail.brackets
        ]
        # rail맵 생성
        rail_map = {
            rail.index: rail
            for rail in dto.rails
        }
        pole_map = {p.index: p for p in dto.poles}
        BracketResolver.resolve(all_brackets, self.idxlib)
        PoleResolver.resolve(dto.poles, self.idxlib, rail_map)
        BeamResolver.resolve(dto.beams, self.idxlib, rail_map, pole_map)
        EquipmentResolver.resolve(dto.equips, self.idxlib, rail_map, pole_map)