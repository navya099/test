from enums.poletype import PoleType
from model.rail import RailData
from resolver.polebase_resolver import PoleBaseResolver
from utils.pole_dimention_finder import PoleDimensionFinder
from utils.polenamer import PoleNameBuilder


class PoleResolver:
    index_dic = {}
    indexes = set()
    next_index = None  # 빔과 겹치지 않도록 별도 범위 시작

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

            #기초 리졸버
            PoleBaseResolver.resolve(pole, idxlib)

    @staticmethod
    def set_start_index(value: int, is_reset_idx):
        if PoleResolver.next_index is None or is_reset_idx:
            PoleResolver.next_index = value
            PoleResolver.index_dic.clear()
            PoleResolver.indexes.clear()
            # 필요하다면 초기화 로직 추가