import numpy as np


def get_track_edges(coords, track_width):
    """노선 중심 좌표에서 좌우 offset으로 트랙 생성"""
    left_side = []
    right_side = []
    for i in range(len(coords)):
        if i < len(coords) - 1:
            x1, y1, z1 = coords[i]
            x2, y2, z2 = coords[i + 1]
            dx, dy = x2 - x1, y2 - y1
        else:
            # 마지막 점은 이전 점과 방향 벡터 사용
            x1, y1, z1 = coords[i]
            x2, y2, z2 = coords[i - 1]
            dx, dy = x1 - x2, y1 - y2


        length = np.sqrt(dx ** 2 + dy ** 2)
        nx, ny = -dy / length, dx / length
        left_side.append((x1 + nx * track_width / 2, y1 + ny * track_width / 2, z1))
        right_side.append((x1 - nx * track_width / 2, y1 - ny * track_width / 2, z1))

    return left_side, right_side  # ✅ 둘 다 반환