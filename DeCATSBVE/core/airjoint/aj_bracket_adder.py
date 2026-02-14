from core.airjoint.aj_data_context import AirjointDataContext
from core.bracket.bracket_data import BracketDATA
from core.bracket.fitting_data import FittingDATA
from core.equipment.equipment_data import EquipmentDATA
from core.mast.mastdata import Mast
from core.pole.normal_section_processor import NormalSectionProcessor
from core.pole.poledata import PoleDATA
from enums.airjoint_section import AirJoint
from utils.math_util import calculate_curve_angle


class AirjointBracketAdder:
    def __init__(self, params: AirjointDataContext ,dataprocessor, normal_processor):
        self.params = params
        self.prosc = dataprocessor
        self.nps = normal_processor
    def add_airjoint_brackets(self, pole: PoleDATA, polyline_with_sta, idxlib):
        """에어조인트 각 구간별 브래킷 추가"""
        if pole.section == AirJoint.START.value:
            # START 구간 처리

            self.nps.process(pole, self.prosc, idxlib)
            x1, y1 = self.prosc.get_bracket_coordinates('F형_시점')
            if pole.side == 'L':
                x1 *= -1
            start_angle = calculate_curve_angle(polyline_with_sta, pole.pos, pole.next_pos, pole.gauge, x1)
            en = idxlib.get_name(1247)
            pole.equipments.append(EquipmentDATA(name=en, index=1247, offset=(pole.gauge,0),rotation=start_angle, type='장력장치'))

        elif pole.section == AirJoint.POINT_2.value:
            # POINT_2 구간 처리
            self.add_common_equipts(pole)
            self.add_F_and_AJ_brackets(pole, idxlib=idxlib)

        elif pole.section == AirJoint.MIDDLE.value:
            # MIDDLE 구간 처리
            self.add_common_equipts(pole)
            self.add_AJ_brackets_middle(pole, idxlib)

        elif pole.section == AirJoint.POINT_4.value:
            # POINT_4 구간 처리
            self.add_common_equipts(pole)
            self.add_F_and_AJ_brackets(pole, end=True, idxlib=idxlib)

        elif pole.section == AirJoint.END.value:
            # END 구간 처리
            en = idxlib.get_name(1247)
            self.nps.process(pole, self.prosc, idxlib)
            x5, y5 = self.prosc.get_bracket_coordinates('F형_끝')
            if pole.side == 'R':
                x5 *= -1
            end_angle = calculate_curve_angle(polyline_with_sta, pole.pos, pole.next_pos, x5, pole.next_gauge,start=False)
            pole.equipments.append(EquipmentDATA(name=en, index=1247, offset=(pole.gauge,0),rotation=180 + end_angle, type='장력장치'))



    def add_F_and_AJ_brackets(self, pole, end=False, idxlib=None):
        """F형 및 AJ형 브래킷을 추가하는 공통 함수"""
        f_i, f_o = self.params.f_bracket_valuse
        aj_i,aj_o = self.params.aj_bracket_values
        #기본 브래킷 제거
        pole.brackets.clear()
        # F형 가동 브래킷 추가
        x1, y1 = self.prosc.get_bracket_coordinates('F형_시점' if not end else 'F형_끝')
        if not end and pole.side == 'L':
            x1 *= -1
        self.add_F_bracket(pole, f_i,idxlib, x1, y1)

        # AJ형 가동 브래킷 추가
        x1, y1 = self.prosc.get_bracket_coordinates('AJ형_시점' if not end else 'AJ형_끝')
        if not end and pole.side == 'L':
            x1 *= -1
        self.add_AJ_bracket(pole, aj_i, idxlib, x1, y1)

    def add_F_bracket(self, pole: PoleDATA, bracket_code, idxlib, x1, y1):
        """F형 가동 브래킷 및 금구류 추가"""
        rotation = 180 if pole.side == 'R' else 0
        idx1, idx2 = self.params.flat_fitting
        n1 = idxlib.get_name(idx1)
        n2 = idxlib.get_name(idx2)
        h = self.params.f_bracket_height
        bracket_name = idxlib.get_name(bracket_code)
        # 브래킷 추가
        bracket = BracketDATA(
            bracket_type='F',
            index=bracket_code,
            bracket_name=bracket_name,
            offset=(0,h),
            rotation=rotation
        )
        # 금구류 추가
        bracket.fittings.append(FittingDATA(index=idx1, label=n1, offset=(x1, y1), rotation=rotation))
        bracket.fittings.append(FittingDATA(index=idx2, label=n2, offset=(x1, y1), rotation=rotation))

        # PoleDATA에 브래킷 등록
        pole.brackets.append(bracket)

    def add_AJ_bracket(self, pole: PoleDATA, bracket_code, idxlib, x1, y1, end=False):
        """AJ형 가동 브래킷 및 금구류 추가"""
        rotation = 180 if pole.side == 'R' else 0
        idx1 = self.params.airjoint_fitting
        idx2 = self.params.steady_arm_fitting[0] if not end else self.params.steady_arm_fitting[1]
        n1 = idxlib.get_name(idx1)
        n2 = idxlib.get_name(idx2)
        bn = idxlib.get_name(bracket_code)
        # 브래킷 추가
        bracket = BracketDATA(
            bracket_type='AJ',
            index=bracket_code,
            bracket_name=bn,
            offset=(0, y1),
            rotation=rotation
        )
        # 금구류 추가
        bracket.fittings.append(FittingDATA(index=idx1, label=n1, offset=(x1, y1), rotation=rotation))
        bracket.fittings.append(FittingDATA(index=idx2, label=n2, offset=(x1, y1),rotation=rotation))

        # PoleDATA에 브래킷 등록
        pole.brackets.append(bracket)


    def add_AJ_brackets_middle(self, pole, idxlib):
        """MIDDLE 구간에서 AJ형 브래킷 추가"""
        # 기본 브래킷 제거
        pole.brackets.clear()

        aj_i, aj_o = self.params.aj_bracket_values
        # AJ형 가동 브래킷 및 금구류 추가
        x1, y1 = self.prosc.get_bracket_coordinates('AJ형_중간1')
        if pole.side == 'L':
            x1 *= -1
        self.add_AJ_bracket(pole, aj_i, idxlib, x1, y1)

        # AJ형 가동 브래킷 및 금구류 추가
        x1, y1 = self.prosc.get_bracket_coordinates('AJ형_중간2')
        if pole.side == 'R':
            x1 *= -1
        self.add_AJ_bracket(pole, aj_o, idxlib, x1, y1)

    def add_common_equipts(self, pole):
        rotation = 180 if pole.side == 'R' else 0
        pole.mast = Mast(self.params.mast_name, self.params.mast_type, pole.gauge, rotation=rotation)
        feederidx = self.params.feeder_idx
        feeder_name = self.params.feeder_name
        spreaderidx = self.params.spreader_idx
        spreader_name = self.params.spreader_name
        pole.equipments.append(
            EquipmentDATA(name=feeder_name, index=feederidx, offset=(pole.gauge, 0),rotation=rotation,type='급전선설비'))
        pole.equipments.append(
            EquipmentDATA(name=spreader_name, index=spreaderidx, offset=(pole.gauge, 0),rotation=rotation,type='평행틀'))