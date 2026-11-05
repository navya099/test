"""선형 기하 계산 유틸"""

from __future__ import annotations
import math


def line_intersection(
    p1: tuple[float, float], p2: tuple[float, float],
    p3: tuple[float, float], p4: tuple[float, float],
) -> tuple[float, float] | None:
    """두 무한 직선의 교점. 평행이면 None."""
    x1, y1 = p1; x2, y2 = p2
    x3, y3 = p3; x4, y4 = p4
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-12:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


def offset_polyline_ips(
    cl_points: list[tuple[float, float]],
    offset: float,
    side: int = +1,
) -> list[tuple[float, float]]:
    """CL 폴리라인의 IP를 offset만큼 평행이동 (LWPOLYLINE OFFSET).

    Parameters
    ----------
    cl_points : list[(x, y)]
        CL 꼭짓점 리스트 (BP, IP1, IP2, ..., EP)
    offset : float
        오프셋 거리 (m, 양수)
    side : int
        +1 = 좌측 (진행 방향 +90°)
        -1 = 우측 (진행 방향 -90°)

    Returns
    -------
    list[(x, y)]
        오프셋된 IP 좌표 리스트 (BP', IP1', ..., EP')
    """
    n = len(cl_points)
    if n < 2:
        return list(cl_points)

    # 각 세그먼트의 단위 법선 벡터
    normals: list[tuple[float, float]] = []
    for i in range(n - 1):
        x1, y1 = cl_points[i]
        x2, y2 = cl_points[i + 1]
        dx = x2 - x1; dy = y2 - y1
        length = math.hypot(dx, dy)
        if length < 1e-12:
            normals.append((0.0, 0.0))
            continue
        nx = -dy / length * side
        ny = dx / length * side
        normals.append((nx, ny))

    result: list[tuple[float, float]] = []

    # 1) BP' — 첫 세그먼트 법선 오프셋
    x, y = cl_points[0]
    nx, ny = normals[0]
    result.append((x + offset * nx, y + offset * ny))

    # 2) 중간 IP'들 — 인접 세그먼트 오프셋 교점
    for i in range(1, n - 1):
        p_prev = cl_points[i - 1]
        p_curr = cl_points[i]
        p_next = cl_points[i + 1]
        n_prev = normals[i - 1]
        n_next = normals[i]

        s1_a = (p_prev[0] + offset * n_prev[0], p_prev[1] + offset * n_prev[1])
        s1_b = (p_curr[0] + offset * n_prev[0], p_curr[1] + offset * n_prev[1])
        s2_a = (p_curr[0] + offset * n_next[0], p_curr[1] + offset * n_next[1])
        s2_b = (p_next[0] + offset * n_next[0], p_next[1] + offset * n_next[1])

        inter = line_intersection(s1_a, s1_b, s2_a, s2_b)
        if inter is not None:
            result.append(inter)
        else:
            # 평행 (일직선) → 현 IP 법선 오프셋
            nx, ny = n_next
            result.append((p_curr[0] + offset * nx, p_curr[1] + offset * ny))

    # 3) EP' — 마지막 세그먼트 법선 오프셋
    x, y = cl_points[-1]
    nx, ny = normals[-1]
    result.append((x + offset * nx, y + offset * ny))

    return result