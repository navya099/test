from model.rail import RailData
from utils.polenamer import PoleNameBuilder


class PoleResolver:
    @staticmethod
    def resolve(poles, idxlib, rail_map):
        for pole in poles:
            name = PoleNameBuilder.build(pole)
            index = idxlib.get_index(name)
            pole.display_name = name
            pole.obj_index = index
            pole.base_rail = rail_map[pole.base_rail_index]