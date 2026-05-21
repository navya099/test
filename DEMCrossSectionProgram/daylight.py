import meshio
import numpy as np
from shapely.geometry import Polygon

from function import convert_coordinates


class SlopeManager:
    """슬로프 빌더"""
    def __init__(self, dem, terrain_mesh):
        self.dem = dem
        self.slope_builder = None
        self.terrain_mesh = terrain_mesh
    def build_slopes(self, track_edges, slope_ratio=1.5):
        #트랙 사이드
        left_side, right_side = track_edges
        #빌더 초기화
        self.slope_builder = SlopeBuilder(self.terrain_mesh)

        # 좌측 사면
        slope_left = self.slope_builder.add_slope(left_side, self.dem, slope_ratio, side="left")

        # 우측 사면
        slope_right = self.slope_builder.add_slope(right_side, self.dem, slope_ratio, side="right")

        return slope_left, slope_right

class SlopeBuilder:
    def __init__(self, mesh):
        self.mesh = mesh
        # 메쉬의 삼각형 정점 데이터 미리 추출 및 캐싱 (성능 최적화)
        self.triangles = self._prepare_triangles(mesh)

    def _prepare_triangles(self, mesh):
        # meshio에서 삼각형 face 정보와 points를 가져옴
        points = mesh.points
        for cell in mesh.cells:
            if cell.type == "triangle":
                faces = cell.data
                # Nx3x3 배열로 모든 삼각형의 (p0, p1, p2) 좌표를 한 번에 빌드
                return points[faces]
        raise ValueError("메쉬에 삼각형(triangle) 셀이 존재하지 않습니다.")

    def add_slope(self, track_edges, dem, slope_ratio, side="left"):
        slope_side = []
        n = len(track_edges)

        for i in range(n):
            x, y, z = track_edges[i]
            nx, ny = self._compute_normal_vector(track_edges, i, side)

            # [하드코어 핵심 1] 3D 사면 직선(Ray)의 방향 벡터 정의
            # 성토(+)와 절토(-) 두 방향 모두로 뻗어나가는 3D 직선을 구성하여 판정 오류 원천 차단
            hypotenuse = np.sqrt(slope_ratio ** 2 + 1.0)
            dx = nx * (slope_ratio / hypotenuse)
            dy = ny * (slope_ratio / hypotenuse)

            # 지형과 만나는 진짜 3D 교점 찾기 (성토 방향, 절토 방향 둘 다 탐색)
            ray_origin = np.array([x, y, z], dtype=np.float32)

            # 1. 위쪽(절토) 방향 레이 검사
            ray_dir_cut = np.array([dx, dy, 1.0 / hypotenuse], dtype=np.float32)
            found, hit_point = self._ray_mesh_intersect(ray_origin, ray_dir_cut)

            # 2. 아래쪽(성토) 방향 레이 검사 (위쪽에서 못 찾았을 경우)
            if not found:
                ray_dir_fill = np.array([dx, dy, -1.0 / hypotenuse], dtype=np.float32)
                found, hit_point = self._ray_mesh_intersect(ray_origin, ray_dir_fill)

            if found:
                slope_side.append(hit_point)
            else:
                # 메쉬 범위를 벗어나는 예외 상황 시 기존 이진 탐색 백업용 평사선 연산 적용
                slope_side.append((x + nx * 50, y + ny * 50, z))

        return self._build_mesh(track_edges, slope_side)

    def _ray_mesh_intersect(self, orig, direction):
        """ 모든 지형 삼각형과 직선의 교점을 조사하여 가장 가까운 교점을 반환 (O(N) 최적화 루프) """
        EPSILON = 1e-7
        closest_t = float('inf')
        closest_hit = None

        # 벡터화 연산을 위해 정점 분리
        p0 = self.triangles[:, 0, :]
        p1 = self.triangles[:, 1, :]
        p2 = self.triangles[:, 2, :]

        # Möller-Trumbore 알고리즘 배치(Batch) 연산
        edge1 = p1 - p0
        edge2 = p2 - p0

        # h = direction x edge2
        h = np.cross(direction, edge2)
        # det = edge1 . h
        det = np.einsum('ij,ij->i', edge1, h)

        # 평행한 삼각형 필터링 기법 (det가 0에 가까우면 제외)
        parallel_mask = np.abs(det) > EPSILON
        if not np.any(parallel_mask):
            return False, None

        # 역행렬식 계산
        inv_det = 1.0 / det
        s = orig - p0

        # u = inv_det * (s . h)
        u = inv_det * np.einsum('ij,ij->i', s, h)

        # q = s x edge1
        q = np.cross(s, edge1)
        # v = inv_det * (direction . q)
        v = inv_det * np.einsum('j,ij->i', direction, q)

        # t = inv_det * (edge2 . q)
        t = inv_det * np.einsum('ij,ij->i', edge2, q)

        # 삼각형 내부 조건 조건 마스킹 (u >= 0, v >= 0, u+v <= 1, t > 0)
        hit_mask = parallel_mask & (u >= 0.0) & (v >= 0.0) & (u + v <= 1.0) & (t > EPSILON)

        if np.any(hit_mask):
            valid_t = t[hit_mask]
            min_t_idx = np.argmin(valid_t)
            min_t = valid_t[min_t_idx]

            # 최종 3D 교점 좌표 산출
            hit_point = orig + direction * min_t
            return True, hit_point

        return False, None

    def _compute_normal_vector(self, track_edges, i, side):
        x, y = track_edges[i][:2]
        if i < len(track_edges) - 1:
            dx = track_edges[i + 1][0] - x
            dy = track_edges[i + 1][1] - y
        else:
            dx = x - track_edges[i - 1][0]
            dy = y - track_edges[i - 1][1]

        length = np.sqrt(dx ** 2 + dy ** 2)
        return (-dy / length, dx / length) if side == "left" else (dy / length, -dx / length)

    def _build_mesh(self, track_edges, slope_side):
        n = len(track_edges)
        vertices = np.array(track_edges + slope_side)
        faces = []
        for i in range(n - 1):
            ti, ti_next = i, i + 1
            si, si_next = i + n, i + 1 + n
            faces.append([ti, si, ti_next])
            faces.append([si, si_next, ti_next])
        return meshio.Mesh(points=vertices, cells=[("triangle", np.array(faces))])

