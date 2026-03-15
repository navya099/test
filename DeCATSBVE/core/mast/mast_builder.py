from core.mast.base.mast_base import MastBase
from core.mast.mast_accessory.accessory_builder import AccessoryBuilder
from core.mast.mast_accessory.mast_accessory import MastAccessory
from core.mast.mastdata import Mast
from core.pole.poledata import PoleDATA
from dataset.dataset_getter import DatasetGetter


class MASTBuilder:
    """전주 관련 빌더(기둥, 기초, 악세서리)"""
    @staticmethod
    def build(pole: PoleDATA, dataprocessor: DatasetGetter, idxlib, rotation: float) -> Mast:
        #기둥
        mast_index = dataprocessor.get_mast_index(pole.structure, pole.section)
        mast_name = idxlib.get_name(mast_index)

        #기초
        foundation_idx = dataprocessor.get_post_base(pole.structure)
        foundation_name = idxlib.get_name(foundation_idx)

        #교량구간 offset -> 교량은 0.381만큼 올려야함
        yoffset = MASTBuilder.get_yoffset(dataprocessor, pole.structure)
        #전주용 밴드 2개
        # 밴드
        size = 'P10' if pole.section is None else 'P12'
        accessories = []
        accessories += AccessoryBuilder.build(dataprocessor, idxlib, '가동브래킷용', size, pole.structure, rotation,
                                               pole.gauge)
        accessories += AccessoryBuilder.build(dataprocessor, idxlib, '완철용', size, pole.structure, rotation,
                                               pole.gauge)

        base = MastBase(name=foundation_name, index=foundation_idx, offset=(pole.gauge,yoffset), rotation=rotation)


        return Mast(name=mast_name, index=mast_index, offset=(pole.gauge,yoffset), rotation=rotation, base=base, accessories=accessories)

    @staticmethod
    def get_yoffset(dataprocessor, structure: str) -> float:
        speed = dataprocessor.get_design_speed()
        if speed == 150 or speed == 250:
            return 0.381 if structure == '교량' else 0
        else:
            return 0