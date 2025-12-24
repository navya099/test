from Electric.Overhead.Structure.beamtype import BeamType


class Beam:
    """
    빔 클래스
    Attributes:
        beamtype: 빔 종류
        length: 빔 길이
    """
    def __init__(self):
        self.beamtype: BeamType = BeamType.H_BEAM
        self.length: float = 0.0