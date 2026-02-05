from model.rail import RailData
from utils.polenamer import PoleNameBuilder


class PoleResolver:
    def __init__(self, install):
        self.install = install

    @staticmethod
    def resolve(install, idxlib):
        for pole in install.poles:
            name = PoleNameBuilder.build(pole)
            index = idxlib.get_index(name)
            pole.display_name = name
            pole.index = index
            pole.base_rail = install.rails[index]