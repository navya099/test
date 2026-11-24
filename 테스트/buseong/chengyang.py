import trimesh
import numpy as np
from shapely.geometry import Polygon

# ==========================================
# 1. 입력 데이터 (이미지에서 도출한 가상의 제약 조건)
# ==========================================
track_angle_deg = 45  # 선로 각도 (이미지 기준 대략 45도)
track_width = 8.0  # 선로 폭 (복선 기준 약 8m)
station_length = 60  # 역사 길이 (승강장 길이에 맞춤)
station_width = 25.0  # 역사 폭 (선로 양옆으로 나갈 여유 공간)
station_height = 12.0  # 역사 높이 (선로 위로 띄우는 높이 포함)


# ==========================================
# 2. 매스 생성 엔진
# ==========================================
def generate_bridge_station_mass(angle, t_width, s_length, s_width, s_height):
    meshes = []

    # 2-1. 승강장 매스 (선로와 평행하게 생성)
    platform = trimesh.creation.box(extents=[s_length * 1.5, t_width + 4, 1.5])

    # 2-2. 역사 본체 매스 (선로를 가로지르는 Bridge 형태)
    # 선로 위를 지나가야 하므로, 하부를 비우기 위해 층고를 띄움
    station_body = trimesh.creation.box(extents=[s_width, s_length, 6.0])
    station_body.apply_translation([0, 0, s_height])  # 선로 위로 띄우기

    # 2-3. 코어 타워 (양쪽 대지로 내려가는 수직 동선)
    core_left = trimesh.creation.box(extents=[8, 8, s_height])
    core_left.apply_translation([-s_width / 2 + 4, 0, s_height / 2])

    core_right = trimesh.creation.box(extents=[8, 8, s_height])
    core_right.apply_translation([s_width / 2 - 4, 0, s_height / 2])

    # 2-4. 지붕 (캐노피 - 전체를 덮는 얇은 판)
    roof = trimesh.creation.box(extents=[s_width + 10, s_length + 20, 0.5])
    roof.apply_translation([0, 0, s_height + 6.0 + 1.5])

    # 2-5. 모든 매스 합치기 (Union)
    bridge_mass = trimesh.boolean.union([station_body, core_left, core_right, roof])

    # 2-6. 선로 각도에 맞춰 전체 회전 (Z축 기준)
    rotation_matrix = trimesh.transformations.rotation_matrix(
        np.radians(angle), [0, 0, 1]
    )
    bridge_mass.apply_transform(rotation_matrix)
    platform.apply_transform(rotation_matrix)

    meshes.extend([bridge_mass, platform])
    return trimesh.Scene(meshes)


# ==========================================
# 3. 실행 및 결과 저장
# ==========================================
if __name__ == "__main__":
    scene = generate_bridge_station_mass(
        track_angle_deg, track_width, station_length, station_width, station_height
    )

    # GLB 파일로 저장 (Blender, 웹 뷰어에서 확인 가능)
    scene.export("virtual_route_station.glb")
    print("✅ 가상 노선 역사 매스 생성 완료: virtual_route_station.glb")