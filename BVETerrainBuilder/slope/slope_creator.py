import meshio
import numpy as np

from coordinate_utils import convert_coordinates
from srtm30 import SrtmDEM30

from shapely import Polygon

class SlopeBuilder:
    def __init__(self, mesh):
        self.mesh = mesh

    def add_slope(self, track_mesh, dem, slope_ratio, side="left"):
        track_edges = track_mesh.points  # mesh에서 좌표 꺼내기
        slope_side = []
        n = len(track_edges)

        for i in range(n):
            x, y, z = track_edges[i]

            # 1. 해당 지점의 법선 벡터(Normal Vector) 계산
            # 현재 점과 다음 점(또는 이전 점)을 이용하여 진행 방향의 수직 벡터를 구함
            nx, ny = self._compute_normal_vector(track_edges, i, side)

            # 2. 성토/절토 판정 (선로 바로 옆 지면 높이 확인)
            is_cut = self._is_cut(x, y, z, nx, ny, dem)

            # 3. 이진 탐색으로 Daylight Point(교점) 찾기
            fx, fy, fz = self._find_daylight_point(x, y, z, nx, ny, slope_ratio, is_cut, dem)
            slope_side.append((fx, fy, fz))

        # 4. 메쉬 생성 (기존 로직 유지)
        return self._build_mesh(track_edges, slope_side)

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

    def _is_cut(self, x, y, z, nx, ny, dem):
        lon, lat = convert_coordinates([x + nx * 0.1, y + ny * 0.1], 5186, 4326)
        dem_z = dem.strm.get_elevation(lon, lat) + 100
        return z < dem_z

    def _find_daylight_point(self, x, y, z, nx, ny, slope_ratio, is_cut, dem):
        low, high = 0.0, 500.0
        for _ in range(15):
            mid = (low + high) / 2
            curr_x, curr_y = x + nx * mid, y + ny * mid
            slope_z = z + (mid / slope_ratio) if is_cut else z - (mid / slope_ratio)
            lon, lat = convert_coordinates([curr_x, curr_y], 5186, 4326)
            curr_dem_z = dem.strm.get_elevation(lon, lat) + 100

            if is_cut:
                if slope_z < curr_dem_z:
                    low = mid
                else:
                    high = mid
            else:
                if slope_z > curr_dem_z:
                    low = mid
                else:
                    high = mid

        final_dist = (low + high) / 2
        fx, fy = x + nx * final_dist, y + ny * final_dist
        lon, lat = convert_coordinates([fx, fy], 5186, 4326)
        fz = dem.strm.get_elevation(lon, lat) + 100
        return fx, fy, fz

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

    def extract_daylight_points(self, slope_l, slope_r):
        """사면의 끝점을 추출하여 폴리곤 경계 생성"""
        # 1. 각 사면의 끝점(Daylight Points)들 추출
        n_half_l = len(slope_l.points) // 2
        n_half_r = len(slope_r.points) // 2
        l_daylight = slope_l.points[n_half_l:]
        r_daylight = slope_r.points[n_half_r:]

        return l_daylight, r_daylight

    def create_polygon(self, l_daylight, r_daylight):
        # 왼쪽 끝점과 오른쪽 끝점을 역순으로 이어 붙여 닫힌 루프 생성
        poly_coords = np.concatenate([l_daylight[:, :2], r_daylight[::-1, :2]])

        return Polygon(poly_coords)