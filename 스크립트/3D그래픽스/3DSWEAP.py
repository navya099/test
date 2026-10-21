import datetime
from time import time  # time() 함수 사용을 위한 임포트 추가

import numpy as np


def create_sweep_mesh(path_points, profile_2d):
    """
    path_points: N개의 (X, Y, Z) 철도 중심선 좌표 리스트
    profile_2d:  M개의 (u, v) 단면 정점 좌표 리스트 (예: 사각형의 네 꼭짓점)
    """
    path = np.array(path_points)
    profile = np.array(profile_2d)

    num_path = len(path)
    num_prof = len(profile)

    all_vertices = []

    # --- [1단계 & 2단계] 측점별 로컬 3D 프레임(축벡터) 계산 ---
    for i in range(num_path):
        P = path[i]

        # 진행 방향 벡터 (Tangent) 계산
        if i == 0:
            T = path[i + 1] - P
        elif i == num_path - 1:
            T = P - path[i - 1]
        else:
            T = path[i + 1] - path[i - 1]

        T /= np.linalg.norm(T)  # 단위 벡터화

        # 임의의 기준 벡터와 외적하여 수직인 축(Normal, Binormal) 구하기
        up_vector = np.array([0.0, 0.0, 1.0])
        if np.abs(np.dot(T, up_vector)) > 0.99:  # 선형이 완전히 수직일 경우 예외처리
            up_vector = np.array([0.0, 1.0, 0.0])

        N = np.cross(T, up_vector)
        N /= np.linalg.norm(N)
        B = np.cross(T, N)  # 세 축(T, N, B)이 서로 직교함

        # --- [3단계] 2D 단면 점들을 해당 측점의 3D 공간으로 변환 ---
        for u, v in profile:
            # 로컬 (u, v) 좌표를 3D 공간 상의 (X, Y, Z)로 매핑
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


# ==================== 사용 예시 ====================
# 1. 3D 선형 점들
rail_path = [
    [20, 1, 0.5],
    [30, 3, 1.0],
    [40, 6, 1.5]
]

# 2. 2D 사각형 단면
structural_profile = [
    [-2, -0.5],
    [2, -0.5],
    [2, 0.5],
    [-2, 0.5]
]

# 소요 시간 측정
start_time = time()

vertices, faces = create_sweep_mesh(rail_path, structural_profile)

end_time = time()
elapsed_time = end_time - start_time

print(f"생성된 총 3D 정점 개수: {len(vertices)}")
print(f"생성된 총 3D 면(Face) 개수: {len(faces)}")
print(f"총 소요 시간: {elapsed_time:.6f}초 (밀리초: {elapsed_time * 1000:.3f}ms)")