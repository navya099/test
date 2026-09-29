import math
import numpy as np
from modules.vector2 import Vector2


def compute_coords(chainages: list[float], theta: float, radii: list[float], pitchs: list[float],
                   start_coord: list[float], block_interval: float = 25.0) -> list[tuple[float, float]]:
    """
    BVE 좌표 계산 로직
    Arguments:
        chainages: 측점 리스트
        theta: 시작 방위각(RAD, X축 기준 반시계 방향)
        radii: 곡선반경 리스트 (부호 필수: 좌/우 구분)
        pitchs: 구배 리스트
        start_coord: 시작 좌표 [x, y]
        block_interval: 블록 간격
    Returns:
        coords_calc: 계산된 (x, y) 튜플 리스트
    """
    coords_calc = []

    # start_coord에서 단일 X, Y 좌표를 안전하게 추출
    x_new = start_coord[0]
    y_new = start_coord[1]

    dx241 = math.cos(theta)
    dy241 = math.sin(theta)
    direction = Vector2(dx241, dy241)

    y_height = 0.0

    for i in range(len(chainages) - 1):
        coords_calc.append((x_new, y_new))

        a = 0.0
        c = block_interval
        h = 0.0
        r = radii[i]
        p = pitchs[i]

        direction.normalize()

        # 1. 곡선과 구배가 모두 있는 경우
        if r != 0.0 and p != 0.0:
            d = block_interval
            s = d / math.sqrt(1.0 + p * p)
            h = s * p
            b = s / abs(r)
            c = math.sqrt(2.0 * r * r * (1.0 - math.cos(b)))

            # np.sign(r)을 이용해 곡선의 방향 반영
            a = 0.5 * np.sign(r) * b
            direction.rotate(math.cos(-a), math.sin(-a))

        # 2. 곡선만 있는 경우
        elif r != 0.0:
            d = block_interval
            b = d / abs(r)
            c = math.sqrt(2.0 * r * r * (1.0 - math.cos(b)))
            a = 0.5 * np.sign(r) * b
            direction.rotate(math.cos(-a), math.sin(-a))

        # 3. 구배만 있는 경우
        elif p != 0.0:
            d = c
            c = d / math.sqrt(1.0 + p * p)
            h = c * p

        # 좌표 업데이트
        x_new += direction.x * c
        y_new += direction.y * c
        y_height += h

        # 곡선 종료 시 반절의 각도를 마저 회전
        if a != 0.0:
            direction.rotate(math.cos(-a), math.sin(-a))

    return coords_calc
