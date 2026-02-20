from model.rail import RailData
from utils.pole_dimention_finder import PoleDimensionFinder
from utils.polenamer import PoleNameBuilder


class PoleResolver:
    @staticmethod
    def resolve(poles, idxlib, rail_map):
        for pole in poles:
            name = PoleNameBuilder.build(pole)
            index = idxlib.get_index(name)
            pole.width = PoleDimensionFinder.find_pole_dimension(pole)
            pole.display_name = name
            pole.obj_index = index
            pole.base_rail = rail_map[pole.base_rail_index]
            if pole.length in [7,7.5,8,8.5,9]:
                pole.iscustom = False
            else:
                pole.iscustom = True