from alignment.japancubic import JapaneseCubicSpiralSegment
import math

def get_shift(radius: float, length: float):
    if length <= 0.0:
        return 0.0, 0.0, 0.0

    tmp = JapaneseCubicSpiralSegment(
        0.0,
        0.0,
        0.0,
        0.0,
        radius,
        length,
        1,
    )

    tau = tmp.tau

    dR = tmp.Yc - radius * (1.0 - math.cos(tau))
    Xm = tmp.Xc - radius * math.sin(tau)

    return tau, dR, Xm