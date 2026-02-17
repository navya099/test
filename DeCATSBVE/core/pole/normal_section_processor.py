from core.equipment.equipment_data import EquipmentDATA
from core.mast.mastdata import Mast
from core.pole.curve_section_processor import CurveSectionProcessor
from core.pole.straight_section_processor import StraightSectionProcessor


class NormalSectionProcessor:
    @staticmethod
    def process(pole, dataprocessor, idxlib):
        """노말구간 데이터 생성"""
        #공통변수
        flip = True if pole.side == 'R' else False
        # MAST 데이터 가져오기
        mast_index = dataprocessor.get_mast_index(pole.structure)
        mast_name = idxlib.get_name(mast_index)

        # 급전선 설비 인덱스 가져오기
        feeder_idx = dataprocessor.get_feeder_insulator_idx(pole.structure)
        feeder_name = idxlib.get_name(feeder_idx)

        #베이스타입 뒤집기
        if flip:
            rotation = 180
        else:
            rotation = 0
        if pole.radius == 0:
            current_curve = '직선'
            StraightSectionProcessor.process(pole, dataprocessor, idxlib, current_curve, rotation, stagger_flip=flip)
        else:
            current_curve ='곡선'
            CurveSectionProcessor.process(pole, dataprocessor, idxlib, current_curve, rotation)

        mast = Mast(name=mast_name,index=mast_index, offset=pole.gauge,rotation=rotation)
        equipment = EquipmentDATA(name=feeder_name,index=feeder_idx, offset=(pole.gauge,0),rotation=rotation,type='급전선설비')

        #pole에 기록
        pole.mast = mast
        pole.equipments.append(equipment)
