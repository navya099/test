from Electric.Overhead.Pole.poletype import PoleType
from model.rail import RailData
from utils.pole_dimention_finder import PoleDimensionFinder
from utils.polenamer import PoleNameBuilder


class PoleBaseResolver:

    @staticmethod
    def resolve(pole, idxlib):
        index = idxlib.get_index(pole.base.name)
        pole.base.index = index
