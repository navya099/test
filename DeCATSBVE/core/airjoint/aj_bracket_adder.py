from core.airjoint.aj_data_context import AirjointDataContext
from core.bracket.bracket_data import BracketDATA
from core.bracket.fitting_data import FittingDATA
from core.equipment.equipment_data import EquipmentDATA
from core.mast.mastdata import Mast
from core.pole.poledata import PoleDATA
from enums.airjoint_section import AirJoint
from utils.math_util import calculate_curve_angle


class AirjointBracketAdder:
    def __init__(self, params: AirjointDataContext ,dataprocessor, normal_processor, tunnel_processor):
        self.params = params
        self.prosc = dataprocessor
        self.nps = normal_processor
        self.tps = tunnel_processor

    def add_airjoint_brackets(self, pole: PoleDATA, polyline_with_sta, idxlib):
        """에어조인트 각 구간별 브래킷 추가"""
        if pole.section == AirJoint.START.value:
            # START 구간 처리
            if pole.structure == '터널':
                self.tps.process(pole, self.prosc, idxlib)
            else:
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
            self.add_f_and_aj_brackets(pole, idxlib=idxlib)

        elif pole.section == AirJoint.MIDDLE.value:
            # MIDDLE 구간 처리
            self.add_common_equipts(pole)
            self.add_aj_brackets_middle(pole, idxlib)

        elif pole.section == AirJoint.POINT_4.value:
            # POINT_4 구간 처리
            self.add_common_equipts(pole)
            self.add_f_and_aj_brackets(pole, end=True, idxlib=idxlib)

        elif pole.section == AirJoint.END.value:
            # END 구간 처리
            en = idxlib.get_name(1247)
            if pole.structure == '터널':
                self.tps.process(pole, self.prosc, idxlib)
            else:
                self.nps.process(pole, self.prosc, idxlib)
            x5, y5 = self.prosc.get_bracket_coordinates('F형_끝')
            if pole.side == 'R':
                x5 *= -1
            end_angle = calculate_curve_angle(polyline_with_sta, pole.pos, pole.next_pos, x5, pole.next_gauge)
            pole.equipments.append(EquipmentDATA(name=en, index=1247, offset=(pole.gauge,0),rotation=180 + end_angle, type='장력장치'))

    def add_f_and_aj_brackets(self, pole, end=False, idxlib=None):
        """F형 및 AJ형 브래킷을 추가하는 공통 함수"""
        f_i, f_o = self.params.f_bracket_valuse
        aj_i, aj_o = self.params.aj_bracket_values
        pole.brackets.clear()

        if not end:
            # START 구간: F → AJ
            x1, y1 = self.prosc.get_bracket_coordinates('F형_시점')
            if pole.side == 'L':
                x1 *= -1
            self.add_f_bracket(pole, f_i, idxlib, x1, y1)

            x1, y1 = self.prosc.get_bracket_coordinates('AJ형_시점')
            if pole.side == 'L':
                x1 *= -1
            self.add_aj_bracket(pole,'I', aj_i, idxlib, x1, y1)

        else:
            # END 구간: AJ → F
            x1, y1 = self.prosc.get_bracket_coordinates('AJ형_끝')
            if pole.side == 'R':
                x1 *= -1
            self.add_aj_bracket(pole,'O', aj_o, idxlib, x1, y1, end=True)

            x1, y1 = self.prosc.get_bracket_coordinates('F형_끝')
            if pole.side == 'R':
                x1 *= -1
            self.add_f_bracket(pole, f_o, idxlib, x1, y1)

    def add_f_bracket(self, pole: PoleDATA, bracket_code, idxlib, x1, y1):
        """F형 가동 브래킷 및 금구류 추가"""
        if pole.structure == '터널':
            rotation = 180 if pole.side == 'L' else 0
        else:
            rotation = 180 if pole.side == 'R' else 0

        #전차선 지지금구 F
        idx1 = self.params.contact_wire_fitting
        n1 = idxlib.get_name(idx1)
        #조가선 지지금구 F
        idx2 = self.params.messenger_wire_fittings['무효인상용']
        n2 = idxlib.get_name(idx2)

        #곡선당김금구 F
        f_list = self.params.steady_arm_fitting.get('F', [])
        idx3 = f_list[1] if len(f_list) > 1 else None

        n3 = idxlib.get_name(idx3)

        # 현재 전차선 높이
        sys_height, cw_height = self.prosc.get_contact_wire_and_massanger_wire_info(pole.structure)
        mw_height = cw_height + sys_height

        #브래킷 인상 높이
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
        self.add_bracket_fittng(bracket, idx1, n1, (x1, cw_height + y1), rotation)#전차선 지지금구 F
        self.add_bracket_fittng(bracket, idx2, n2, (x1, mw_height + h), rotation)#조가선 지지금구 F
        if idx3:
            self.add_bracket_fittng(bracket, idx3, n3, (x1, y1 + cw_height), rotation)
        # 터널구간 추가 H하수강 설치
        if pole.structure == '터널':
            self.add_bracket_fittng(bracket, self.params.mast_type, self.params.mast_name, (pole.gauge, 0),
                                    rotation)
        # PoleDATA에 브래킷 등록
        pole.brackets.append(bracket)

    def add_aj_bracket(self, pole: PoleDATA,bracket_type, bracket_code, idxlib, x1, y1, end=False):
        """AJ형 가동 브래킷 및 금구류 추가"""
        if pole.structure == '터널':
            rotation = 180 if pole.side == 'L' else 0
        else:
            rotation = 180 if pole.side == 'R' else 0
        #조가선 지지금구 에어조인트용
        idx1 = self.params.messenger_wire_fittings['에어조인트용']
        n1 = idxlib.get_name(idx1)
        #곡선당김금구
        if not end:
            idx2 = self.params.steady_arm_fitting[bracket_type][0]
        else:
            idx2 = self.params.steady_arm_fitting[bracket_type][1]

        #현재 전차선 높이
        sys_height, cw_height = self.prosc.get_contact_wire_and_massanger_wire_info(pole.structure)
        mw_height = cw_height + sys_height
        n2 = idxlib.get_name(idx2)

        bn = idxlib.get_name(bracket_code)
        # 브래킷 인상 높이
        h = self.params.f_bracket_height
        # 브래킷 추가
        bracket = BracketDATA(
            bracket_type='AJ',
            index=bracket_code,
            bracket_name=bn,
            offset=(0, y1),
            rotation=rotation
        )
        # 금구류 추가
        self.add_bracket_fittng(bracket, idx1, n1, (x1, mw_height + y1), rotation)#조가선 지지금구 에어조인트용
        self.add_bracket_fittng(bracket, idx2, n2, (x1, cw_height), rotation)#곡선당김금구
        #터널구간 추가 H하수강 설치
        if pole.structure == '터널':
            self.add_bracket_fittng(bracket, self.params.mast_type, self.params.mast_name, (pole.gauge, 0), rotation)
        # PoleDATA에 브래킷 등록
        pole.brackets.append(bracket)


    def add_aj_brackets_middle(self, pole, idxlib):
        """MIDDLE 구간에서 AJ형 브래킷 추가"""
        # 기본 브래킷 제거
        pole.brackets.clear()

        aj_i, aj_o = self.params.aj_bracket_values
        # AJ형 가동 브래킷 및 금구류 추가
        x1, y1 = self.prosc.get_bracket_coordinates('AJ형_중간1')
        if pole.side == 'L':
            x1 *= -1
        self.add_aj_bracket(pole, 'I',aj_i, idxlib, x1, y1)

        # AJ형 가동 브래킷 및 금구류 추가
        x1, y1 = self.prosc.get_bracket_coordinates('AJ형_중간2')
        if pole.side == 'R':
            x1 *= -1
        self.add_aj_bracket(pole, 'O', aj_o, idxlib, x1, y1, end=True)

    def add_common_equipts(self, pole):
        """공통 설비"""
        feederidx = self.params.feeder_idx
        feeder_name = self.params.feeder_name
        spreaderidx = self.params.spreader_idx
        spreader_name = self.params.spreader_name

        original_gauge = pole.gauge

        if pole.structure == '터널':
            # 게이지 뒤집기
            flipped_gauge = -original_gauge
            pole.gauge = flipped_gauge
            pole.next_gauge = flipped_gauge
            feeder_rotation = 180 if pole.side == 'R' else 0


            # Equipment 생성
            pole.equipments.append(
                EquipmentDATA(name=feeder_name, index=feederidx, offset=(original_gauge, 0),
                              rotation=feeder_rotation, type='급전선설비')
            )

        else:
            mast_rotation = 180 if pole.side == 'R' else 0
            feeder_rotation = mast_rotation

            # Mast 생성
            pole.mast = Mast(self.params.mast_name, self.params.mast_type, original_gauge, rotation=mast_rotation)

            # Equipment 생성
            pole.equipments.append(
                EquipmentDATA(name=feeder_name, index=feederidx, offset=(original_gauge, 0),
                              rotation=feeder_rotation, type='급전선설비')
            )
            pole.equipments.append(
                EquipmentDATA(name=spreader_name, index=spreaderidx, offset=(original_gauge, 0),
                              rotation=feeder_rotation, type='평행틀')
            )

    def add_bracket_fittng(self, bracket, idx, label, offset, rotation):
        bracket.fittings.append(FittingDATA(index=idx, label=label, offset=offset, rotation=rotation))