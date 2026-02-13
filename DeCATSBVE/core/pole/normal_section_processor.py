from core.bracket.bracket_data import BracketDATA
from core.equipment.equipment_data import EquipmentDATA
from core.mast.mastdata import Mast


class NormalSectionProcessor:
    def __init__(self):
        self.poles = []

    def process(self, pole, dataprocessor, idxlib):
        """노말구간 데이터 생성"""
        # MAST 데이터 가져오기
        mast_index, _ = dataprocessor.get_mast_type(pole.structure)
        mast_name = idxlib.get_name(mast_index)

        # 급전선 설비 인덱스 가져오기
        feeder_idx = dataprocessor.get_feeder_insulator_idx(pole.structure)
        feeder_name = idxlib.get_name(feeder_idx)

        current_curve = '직선' if pole.radius == 0 else '곡선'
        i_type_index, o_type_index = dataprocessor.get_bracket_type(pole.structure, current_curve)

        bracket_index = i_type_index if pole.base_type == 'I' else o_type_index
        bracket_name = idxlib.get_name(bracket_index)
        bracket = BracketDATA(bracket_type=pole.base_type, index=bracket_index, bracket_name=bracket_name)
        mast = Mast(name=mast_name,index=mast_index, offset=pole.gauge)
        equipment = EquipmentDATA(name=feeder_name,index=feeder_idx, offset=(pole.gauge,0))

        #pole에 기록
        pole.mast = mast
        pole.equipments.append(equipment)
        pole.brackets.append(bracket)