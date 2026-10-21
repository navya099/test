import datetime
from time import time

import ezdxf
import numpy as np


def create_sweep_mesh(path_points, profile_2d):
    path = np.array(path_points)
    profile = np.array(profile_2d)

    num_path = len(path)
    num_prof = len(profile)

    all_vertices = []

    # --- [1단계 & 2단계] 측점별 로컬 3D 프레임(축벡터) 계산 ---
    for i in range(num_path):
        P = path[i]

        if i == 0:
            T = path[i + 1] - P
        elif i == num_path - 1:
            T = P - path[i - 1]
        else:
            T = path[i + 1] - path[i - 1]

        T /= np.linalg.norm(T)

        up_vector = np.array([0.0, 0.0, 1.0])
        if np.abs(np.dot(T, up_vector)) > 0.99:
            up_vector = np.array([0.0, 1.0, 0.0])

        N = np.cross(T, up_vector)
        N /= np.linalg.norm(N)
        B = np.cross(T, N)

        # --- [3단계] 2D 단면 점들을 해당 측점의 3D 공간으로 변환 ---
        for u, v in profile:
            world_vertex = P + (u * N) + (v * B)
            all_vertices.append(world_vertex)

    # --- [4단계] 인접한 측점의 정점들을 연결하여 사각형 면(Face) 정보 생성 ---
    faces = []
    for i in range(num_path - 1):
        for j in range(num_prof):
            p1 = i * num_prof + j
            p2 = i * num_prof + ((j + 1) % num_prof)
            p3 = (i + 1) * num_prof + ((j + 1) % num_prof)
            p4 = (i + 1) * num_prof + j

            faces.append([p1, p2, p3, p4])

    return np.array(all_vertices), faces


def save_mesh_and_path_to_dxf(filename, vertices, faces, path_points):
    """3D 메쉬(Face)와 원본 중심선(3D Polyline)을 함께 DXF 파일에 저장"""
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()

    # 1. 원본 철도 중심선 그리기 (빨간색, color=1) -> add_polyline3d 로 수정
    msp.add_polyline3d(path_points, dxfattribs={"color": 1})

    # 2. 3D 스위프 구조물 메쉬 면 그리기 (초록색 계열, color=3)
    for face in faces:
        pts = [vertices[idx] for idx in face]
        msp.add_3dface(pts, dxfattribs={"color": 3})

    doc.saveas(filename)
    print(f"DXF 파일 저장 완료 (중심선 + 메쉬): {filename}")


# ==================== 사용 예시 ====================
rail_path = [
    [20, 1, 0.5],
    [30, 3, 1.0],
    [40, 6, 1.5]
]

structural_profile = [
    [-2, -0.5],
    [2, -0.5],
    [2, 0.5],
    [-2, 0.5]
]

# 소요 시간 측정
start_time = time()

vertices, faces = create_sweep_mesh(rail_path, structural_profile)

# 중심선과 메쉬를 함께 DXF 파일로 출력
output_filename = "c:/temp/rail_path_and_sweep.dxf"
save_mesh_and_path_to_dxf(output_filename, vertices, faces, rail_path)

end_time = time()
elapsed_time = end_time - start_time

print(f"생성된 총 3D 정점 개수: {len(vertices)}")
print(f"생성된 총 3D 면(Face) 개수: {len(faces)}")
print(f"총 소요 시간: {elapsed_time:.6f}초 (밀리초: {elapsed_time * 1000:.3f}ms)")