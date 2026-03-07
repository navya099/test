from Electric.Overhead.Pole.poletype import PoleType
from bve.pole_builder.h_beam_builder import HBEAMBuiilder
from bve.pole_builder.pipe_pole_builder import PIPEPoleBuilder
from bve.pole_builder.steel_pole_builder import SteelPoleBuilder


class POLEBuilderFactory:
    _builder_map = {
        PoleType.PIPE: PIPEPoleBuilder,
        PoleType.H_BEAM: HBEAMBuiilder,
        PoleType.STEEL: SteelPoleBuilder,
    }

    @classmethod
    def create_builder(cls, pole_type: PoleType, length_m: float, diameter: float):
        builder_class = cls._builder_map.get(pole_type, PIPEPoleBuilder)
        return builder_class(length_m, diameter)