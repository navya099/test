from Electric.Overhead.Pole.poletype import PoleType
from model.rail import RailData
from utils.pole_dimention_finder import PoleDimensionFinder
from utils.polenamer import PoleNameBuilder


class PoleResolver:
    @staticmethod
    def resolve(poles, idxlib, rail_map):
        standard_lengths = [7, 7.5, 8, 8.5, 9]
        for pole in poles:
            name = PoleNameBuilder.build(pole)
            index = idxlib.get_index(name)
            pole.width = PoleDimensionFinder.find_pole_dimension(pole)
            pole.display_name = name
            pole.obj_index = index
            pole.base_rail = rail_map[pole.base_rail_index]
            # 조건 세분화
            if (pole.type == PoleType.PIPE) and (pole.length in standard_lengths):
                # PIPE 타입이고 표준 길이 → 기본 폴
                pole.iscustom = False
            else:
                # 그 외 모든 경우 → 커스텀 모드 필요
                pole.iscustom = True
