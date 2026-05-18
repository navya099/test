import numpy as np
from scipy.interpolate import LinearNDInterpolator

class ExistGround:
    @staticmethod
    def extract_ground_line(terrain_mesh, center_pt, normal_vec, width=50, step=1.0):
        """
        3D Mesh로부터 2D 횡단면 데이터를 추출하는 핵심 함수

        :param terrain_mesh: meshio.Mesh 또는 정점/면 데이터
        :param center_pt: 중심점 좌표 [x, y, z]
        :param normal_vec: 진행방향 법선 벡터 (좌우 방향) [dx, dy, 0]
        :param width: 추출할 좌우 폭 (예: 50이면 좌 50m, 우 50m 총 100m)
        :param step: 샘플링 간격 (m)
        :return: (distances, elevations) 튜플
        """
        try:
            # 1. 메쉬 데이터 추출 (meshio 기준)
            points = terrain_mesh.points  # [N, 3] 배열
            x_mesh = points[:, 0]
            y_mesh = points[:, 1]
            z_mesh = points[:, 2]

            # 2. 2D 보간 함수 생성 (Scipy의 LinearNDInterpolator 사용)
            # 3D 공간의 (x, y) 좌표를 입력하면 z(고도)를 반환하는 함수입니다.
            interp_func = LinearNDInterpolator(list(zip(x_mesh, y_mesh)), z_mesh)

            # 3. 샘플링 포인트 생성
            # 법선 벡터를 단위 벡터로 정규화
            normal_vec = np.array(normal_vec[:2])  # z축 제외한 2D 평면 벡터
            norm = np.linalg.norm(normal_vec)
            if norm == 0:
                return np.array([]), np.array([])
            unit_normal = normal_vec / norm

            # 중심에서 좌(-)에서 우(+)까지 거리 생성
            distances = np.arange(-width, width + step, step)

            # 실제 좌표(X, Y) 계산
            sample_pts_x = center_pt[0] + distances * unit_normal[0]
            sample_pts_y = center_pt[1] + distances * unit_normal[1]

            # 4. 고도값 보간 (Interpolation)
            elevations = interp_func(sample_pts_x, sample_pts_y)

            # 5. 결과 필터링 (NaN 값 제거 - 메쉬 범위를 벗어난 지점)
            mask = ~np.isnan(elevations)
            return distances[mask], elevations[mask]

        except Exception as e:
            print(f"Ground extraction error: {e}")
            return np.array([]), np.array([])