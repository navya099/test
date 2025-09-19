from enum import Enum

class SpiralType(Enum):
    """Civil 3D SpiralType enum (원문 Case 스타일 유지)."""

    Clothoid = 256
    SineHalfWave = 257
    JapaneseCubic = 258
    Bloss = 259
    CubicParabola = 260
    Sinusoidal = 261
    BiQuadratic = 262
    NSWCubic = 264

    OffsetClothoid = 832
    OffsetHalfWaveLenDimnTangent = 833
    OffsetJapaneseCubic = 834
    OffsetBloss = 835
    OffsetCubicParabola = 836
    OffsetSinusoidal = 837
    OffsetBiQuadratic = 838
    OffsetHalfWaveLenDimnTangent2 = 839

    OffsetInvalidSpiralType = 268435455
