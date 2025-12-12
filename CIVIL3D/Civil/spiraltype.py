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

    OffsetClothoid = 1048832
    OffsetHalfWaveLenDimnTangent = 1048833
    OffsetJapaneseCubic = 1048834
    OffsetBloss = 1048835
    OffsetCubicParabola = 1048836
    OffsetSinusoidal = 1048837
    OffsetBiQuadratic = 1048838
    OffsetHalfWaveLenDimnTangent2 = 1048839

    OffsetInvalidSpiralType = 268435455
