from core.bracket.bracket_data import BracketDATA
from core.equipment.equipment_data import EquipmentDATA
from core.mast.mastdata import Mast


class TunnelSectionProcessor:
    def __init__(self):
        self.poles = []
    def process(self, pole, dataprocessor, idxlib):

        # MAST 데이터 가져오기
        mast_index = dataprocessor.get_mast_index(pole.structure)
        mast_name = idxlib.get_name(mast_index)

        # 급전선 설비 인덱스 가져오기
        feeder_idx = dataprocessor.get_feeder_insulator_idx(pole.structure)
        feeder_name = idxlib.get_name(feeder_idx)

        current_curve = '직선' if pole.radius == 0 else '곡선'
        i_type_index, o_type_index = dataprocessor.get_bracket_type(pole.structure, current_curve)



        # 터널구간은 브래킷을 뒤집어야함
        bracket_index = o_type_index if pole.base_type == 'I' else i_type_index
        bracket_name = idxlib.get_name(bracket_index)
        rotation = 180 if pole.side == 'L' else 0
        bracket = BracketDATA(bracket_type=pole.base_type, index=bracket_index, bracket_name=bracket_name,
                              rotation=rotation)
        #건식게이지도 뒤집어야함
        gauge = pole.gauge
        #전주는 뒤집기
        pole.gauge *= -1
        pole.next_gauge *= -1
        mast = Mast(name=mast_name, index=mast_index, offset=pole.gauge, rotation=rotation)

        # 급전선 설비는 게이지와 rotation 유지
        rotation = 180 if pole.side == 'R' else 0
        equipment = EquipmentDATA(name=feeder_name, index=feeder_idx, offset=(gauge, 0), rotation=rotation,
                                  type='급전선설비')

        # pole에 기록
        pole.mast = mast
        pole.equipments.append(equipment)
        pole.brackets.append(bracket)