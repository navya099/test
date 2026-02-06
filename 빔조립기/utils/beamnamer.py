from Electric.Overhead.Structure.beamtype import BeamType
from utils.funtion import format_meter


class BeamNameBuilder:
    @staticmethod
    def build(beam) -> str:
        t = beam.type
        length = format_meter(beam.length)  # str
        return f'{t.value}-{length}m'

