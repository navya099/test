from src.railway_alignment.core.constant_config import Config, M_VALUE_TABLE
import math

def calculate_parameters(
    radius_list: list[float],
    max_v: int = Config.DEFAULT_MAX_V,
    track_type: str = "자갈도상",
) -> list[list[float]]:
    """곡선별 [M, Z, V] 계산"""
    parameters = []
    for radius in radius_list:
        cm, cd = get_cant_limits(max_v, track_type)
        v = round(calculate_v(cm, cd, radius, max_v) / Config.V_ROUNDING) * Config.V_ROUNDING
        m = int(M_VALUE_TABLE.get(v, Config.M_FALLBACK_COEFFICIENT * v))
        m = round(m / Config.M_ROUNDING) * Config.M_ROUNDING
        z = min(Config.CANT_COEFFICIENT * v ** 2 / radius, cm)
        z = round(z / Config.Z_ROUNDING) * Config.Z_ROUNDING
        parameters.append([m, z, v])
    return parameters

# ============================================================
# 캔트/M/Z/V 계산
# ============================================================
def get_cant_limits(v: float, track_type: str) -> tuple[int, int]:
    """설계속도·도상별 (최대설정캔트, 최대부족캔트)"""
    if track_type == "자갈도상":
        if v > 400:
            raise ValueError(f"지원 범위 초과: V={v}")
        if 350 < v <= 400:
            return 180, 130
        if 250 < v <= 350:
            return 160, 80
        return 160, 100
    if track_type == "콘크리트도상":
        if v > 400:
            raise ValueError(f"지원 범위 초과: V={v}")
        return 180, 130
    raise ValueError(f"잘못된 도상 유형: {track_type}")


def calculate_v(cm: int, cd: int, radius: float, max_v: int) -> int:

    v = int(math.sqrt((cm + cd) * radius / Config.CANT_COEFFICIENT))
    return min(v, max_v)



def dictionary_cubicparabola(v: int) -> float:
    """완화곡선 미삽입 최소 곡선반경"""
    not_spiral_min_radius = {250: 24000, 200: 12000, 150: 5000, 120: 2500, 70: 600}
    cdlim = {400: 20, 350: 25, 300: 27, 250: 32, 200: 40, 150: 57, 120: 69, 100: 83, 70: 100}

    if v in not_spiral_min_radius:
        return not_spiral_min_radius[v]

    # cdlim 보간
    if v in cdlim:
        cdlim_val = cdlim[v]
    else:
        keys = sorted(cdlim)
        if v < keys[0] or v > keys[-1]:
            raise ValueError(f"속도 {v} 범위 초과 ({keys[0]}~{keys[-1]})")
        cdlim_val = None
        for i in range(len(keys) - 1):
            if keys[i] <= v <= keys[i + 1]:
                x1, y1 = keys[i], cdlim[keys[i]]
                x2, y2 = keys[i + 1], cdlim[keys[i + 1]]
                cdlim_val = y1 + (v - x1) * (y2 - y1) / (x2 - x1)
                break

    return Config.CANT_COEFFICIENT * (v ** 2 / cdlim_val)
