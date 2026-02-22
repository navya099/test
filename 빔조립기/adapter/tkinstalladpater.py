import tkinter as tk
from adapter.tk_beam_adapter import TkBeamAdapter
from adapter.tk_bracket_adapter import TKBracketAdapter
from adapter.tk_bracket_fitting_adapter import TKBracketFittngAdapter
from adapter.tk_equipment_adapter import TkEquipmentAdapter
from adapter.tk_pole_adapter import TkPoleAdapter
from adapter.tk_raildata_adapter import TKRaildataAdapter
from gui.viewmodel.tkinstalldata import TKInstallData
from model.pole_install import PoleInstall
from model.tkraildata import TKRailData


class TkInstallAdapter:
    def collect(self, sections) -> list[PoleInstall]:
        result = []
        for section in sections:
            rails = TKRaildataAdapter.collect(
                section.rails_var
            )

            poles = TkPoleAdapter.collect(
                section.poles_var
            )

            beams = TkBeamAdapter.collect(
                section.beams_var
            )
            equips = TkEquipmentAdapter.collect(section.equips_var)

            poleinstall =  PoleInstall(
                iid=section.iid,
                station=section.station_var.get(),
                pole_number=section.pole_number_var.get(),
                rail_count=section.rail_count_var.get(),
                pole_count=section.pole_count_var.get(),
                beam_count=section.beam_count_var.get(),
                rails=rails,
                poles=poles,
                beams=beams,
                equips=equips
            )
            result.append(poleinstall)
        return result

    def apply(self, master, installs: list[PoleInstall]):
        vms = []
        for dto in installs:
            # VM 생성
            vm = TKInstallData(
                station_var=tk.DoubleVar(value=dto.station),
                pole_number_var=tk.StringVar(value=dto.pole_number),
                rail_count_var=tk.IntVar(value=dto.rail_count),
                pole_count_var=tk.IntVar(value=dto.pole_count),
                beam_count_var=tk.IntVar(value=dto.beam_count),
                poles_var=[], beams_var=[], rails_var=[], equips_var=[],
                isbeaminstall_var=tk.BooleanVar(value=True),
                iid=dto.iid
            )

            # 하위 데이터 복원
            vm.rails_var = [TKRaildataAdapter.from_dto(r) for r in dto.rails]
            # 각 rail의 brackets 복원
            for rail_vm, rail_dto in zip(vm.rails_var, dto.rails):
                rail_vm.brackets = []
                for b_dto in rail_dto.brackets:
                    dto_fittings = getattr(b_dto, "fittings", []) # 기존 데이터에는 fittings 속성이 없을 수 있음=

                    fittings = [TKBracketFittngAdapter.from_dto(f) for f in dto_fittings]
                    bracket_vm = TKBracketAdapter.from_dto(b_dto, fittings=fittings)
                    rail_vm.brackets.append(bracket_vm)

            vm.poles_var = [TkPoleAdapter.from_dto(p) for p in dto.poles]
            vm.beams_var = [TkBeamAdapter.from_dto(b) for b in dto.beams]
            vm.equips_var = [TkEquipmentAdapter.from_dto(e) for e in dto.equips]
            vms.append(vm)

        return vms

