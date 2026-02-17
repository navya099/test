from core.bracket.bracket_data import BracketDATA
from core.bracket.helper_bracket_create import BracketCreator
from core.equipment.equipment_data import EquipmentDATA
from core.mast.mastdata import Mast
from core.pole.curve_section_processor import CurveSectionProcessor
from core.pole.straight_section_processor import StraightSectionProcessor


class TunnelSectionProcessor:
    @staticmethod
    def process(pole, dataprocessor, idxlib):
        rotation = 180 if pole.side == 'L' else 0
        mast_index = dataprocessor.get_mast_index(pole.structure)
        mast_name = idxlib.get_name(mast_index)

        feeder_idx = dataprocessor.get_feeder_insulator_idx(pole.structure)
        feeder_name = idxlib.get_name(feeder_idx)

        current_curve = '직선' if pole.radius == 0 else '곡선'
        if pole.radius == 0:
            StraightSectionProcessor.process(pole, dataprocessor, idxlib, current_curve, rotation, bracket_flip=True, stagger_flip=True)
        else:
            CurveSectionProcessor.process(pole, dataprocessor, idxlib, current_curve, rotation ,True)

        # 터널 특수 규칙 적용
        gauge = pole.gauge
        pole.gauge *= -1
        pole.next_gauge *= -1
        mast = Mast(name=mast_name, index=mast_index, offset=pole.gauge, rotation=rotation)

        rotation = 180 if pole.side == 'R' else 0
        equipment = EquipmentDATA(name=feeder_name, index=feeder_idx,
                                  offset=(gauge, 0), rotation=rotation,
                                  type='급전선설비')
        pole.mast = mast
        pole.equipments.append(equipment)