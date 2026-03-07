from Electric.Overhead.Pole.poletype import PoleType
from model.rail import RailData
from utils.pole_dimention_finder import PoleDimensionFinder
from utils.polenamer import PoleNameBuilder


class PoleResolver:
    index_dic = {}
    indexes = set()
    next_index = 1600  # 빔과 겹치지 않도록 별도 범위 시작

    @staticmethod
    def resolve(poles, idxlib, rail_map):
        standard_lengths = [7, 7.5, 8, 8.5, 9]
        standard_widths = [0.2674, 0.3185]

        for pole in poles:
            name = PoleNameBuilder.build(pole)
            pole.width = PoleDimensionFinder.find_pole_dimension(pole)
            pole.display_name = name
            pole.base_rail = rail_map[pole.base_rail_index]

            # 조건 세분화
            if (pole.type == PoleType.PIPE) and (pole.length in standard_lengths) and (pole.width in standard_widths):
                pole.iscustom = False
            else:
                pole.iscustom = True

            # 인덱스 조회 및 추가
            index = idxlib.get_index(name)
            if index is None:
                existing = [k for k, v in PoleResolver.index_dic.items() if v == name]
                if existing:
                    index = existing[0]
                else:
                    while PoleResolver.next_index in PoleResolver.indexes:
                        PoleResolver.next_index += 1
                    index = PoleResolver.next_index
                    PoleResolver.index_dic[index] = name
                    PoleResolver.indexes.add(index)
                    PoleResolver.next_index += 1

            pole.obj_index = index