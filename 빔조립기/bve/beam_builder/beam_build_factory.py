from Electric.Overhead.Structure.beamtype import BeamType
from bve.beam_builder.pipe_builder import PIPEBeamBuilder
from bve.beam_builder.truss_builder import TRUSSBeamBuilder
from bve.beam_builder.truss_rahmen_builder import TrussRahmenBeamBuilder


class BeamBuilderFactory:
    _builder_map = {
        BeamType.PIPE: PIPEBeamBuilder,
        BeamType.TRUSS: TRUSSBeamBuilder,
        BeamType.TRUSS_RHAMEN: TrussRahmenBeamBuilder,
    }

    @classmethod
    def create_builder(cls, beam_type: BeamType, length_m: float):
        builder_class = cls._builder_map.get(beam_type, TRUSSBeamBuilder)
        return builder_class(length_m)