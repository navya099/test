import math
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def normalize(v):
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm

def compute_chainage(start, end, center, point, radius, pitch=0, clockwise=True):
    start = np.array(start)
    end = np.array(end)
    point = np.array(point)

    if radius == 0 or center is None:
        # 직선 처리
        line_vec = end - start
        line_unit = normalize(line_vec)
        vec_to_point = point - start

        proj_length = np.dot(vec_to_point, line_unit)
        proj_point = start + line_unit * proj_length

        # 직선 범위 체크
        if proj_length < 0 or proj_length > np.linalg.norm(line_vec):
            raise ValueError("입력된 점이 직선 범위를 벗어났습니다.")

        return proj_length, tuple(proj_point)
    else:
        # 호 처리
        center = np.array(center)
        start_vec = np.array(start[:2]) - center
        point_vec = np.array(point[:2]) - center

        start_angle = math.atan2(start_vec[1], start_vec[0])
        point_angle = math.atan2(point_vec[1], point_vec[0])

        if clockwise:
            delta_angle = (start_angle - point_angle) % (2 * math.pi)
        else:
            delta_angle = (point_angle - start_angle) % (2 * math.pi)

        # 호 범위 체크 (각도가 호의 범위 내에 있는지 확인)
        if delta_angle > (length / radius):
            raise ValueError("입력된 점이 호 범위를 벗어났습니다.")

        arc_length = radius * delta_angle

        # pitch 고려 (z 변화량)
        dz = arc_length * (pitch / 1000)
        sta_point_z = start[2] + dz
        arc_point = (point_vec / np.linalg.norm(point_vec)) * radius + center
        arc_point_3d = (arc_point[0], arc_point[1], sta_point_z)

        return arc_length, arc_point_3d



def compute_arc_end_point_3d(start, direction, radius, length, pitch=0, clockwise=True):
    dir_vec = normalize(np.array(direction[:2]))  # x, y만 사용

    if radius == 0:
        # 직선 이동
        dx, dy = dir_vec * length
        dz = length * (pitch / 1000)  # 퍼밀 고려
        end_point = (start[0] + dx, start[1] + dy, start[2] + dz)
        return end_point, None
    else:
        # 호 이동
        theta = length / radius
        perp = np.array([-dir_vec[1], dir_vec[0]])
        if clockwise:
            perp = -perp

        center = np.array(start[:2]) + perp * radius
        start_vec = np.array(start[:2]) - center
        angle = -theta if clockwise else theta
        cos_t, sin_t = math.cos(angle), math.sin(angle)
        rotation_matrix = np.array([[cos_t, -sin_t], [sin_t, cos_t]])
        end_vec = rotation_matrix @ start_vec
        end_xy = center + end_vec
        dz = length * (pitch / 1000)
        end_point = (end_xy[0], end_xy[1], start[2] + dz)
        return end_point, tuple(center)

# 파라미터
start = (0, 0, 0)
direction = (0.464, 1.6346, 0.36325)
radius = 8000
length = 2500
pitch = -6  # 퍼밀
clockwise = True

# 계산
end, center = compute_arc_end_point_3d(start, direction, radius, length, pitch, clockwise)
print(f'좌표 : x={end[0]},y={end[1]},z={end[2]}')

#임의의 점 측점 찾기
point = (1044.3554380588912,2260.226618910321,-15.0)
try:
    sta, proj = compute_chainage(start, end, center, point, radius, pitch, clockwise)
    print(f"측점(sta): {sta:.3f}, 투영 좌표: {proj}")
except ValueError as e:
    print(str(e))  # 오류 메시지 출력
    
