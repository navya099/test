from enum import Enum

class AlignmentEntityType(Enum):
    Line = 257
    Arc = 258
    Spiral = 259
    SpiralCurveSpiral = 260
    SpiralLineSpiral = 261
    SpiralLine = 262
    LineSpiral = 263
    SpiralCurve = 264
    CurveSpiral = 265
    SpiralSpiralCurveSpiralSpiral = 266
    MultipleSegments = 267
    SpiralCurveSpiralCurveSpiral = 268
    SpiralCurveSpiralSpiralCurveSpiral = 269
    SpiralSpiral = 270
    SpiralSpiralCurve = 271
    CurveSpiralSpiral = 272
    CurveLineCurve = 273
    CurveReverseCurve = 274
    CurveCurveReverseCurve = 275
    ReverseSpiralSpiralCurveSpiral = 276
    SpiralCurveSpiralReverseSpiral = 277
