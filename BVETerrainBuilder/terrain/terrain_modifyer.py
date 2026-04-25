import meshio
import numpy as np
from scipy.spatial import cKDTree
from shapely import Polygon
from shapely.ops import triangulate
import logging
from util import interpolate_z


class TerrainModifier :
    """지형 편집 클래스"""
    def __init__(self, terrain_mesh):
        self.terrain_mesh = terrain_mesh

    def clip(self, clipping_poly):
        """지형을 경계로 clip(2d평면 경계 클리핑)"""
        vertices = self.terrain_mesh.points
        faces = self.terrain_mesh.cells[0].data

        final_vertices = []
        final_faces = []
        v_map = {}

        def get_v_idx(pt):
            pt_tuple = (round(pt[0], 8), round(pt[1], 8), round(pt[2], 8))
            if pt_tuple not in v_map:
                v_map[pt_tuple] = len(final_vertices)
                final_vertices.append(list(pt))
            return v_map[pt_tuple]

        for face in faces:
            tri_coords = vertices[face]

            tri_poly = Polygon(tri_coords[:, :2])

            # 교차 영역만 추출
            try:
                clipped_area = tri_poly.difference(clipping_poly)
            except:
                continue

            if clipped_area.is_empty:
                continue

            # Polygon 또는 MultiPolygon 처리
            # 타입별 안전 처리
            if clipped_area.geom_type == 'Polygon':
                geoms = [clipped_area]
            elif clipped_area.geom_type == 'MultiPolygon':
                geoms = clipped_area.geoms
            else:
                # LineString, GeometryCollection 등은 스킵

                logging.debug(f"Unexpected geom_type: {clipped_area.geom_type}, skip")
                continue

            for poly in geoms:
                if poly.area < 0.001:
                    continue

                # triangulate로 내부 삼각화

                tris = triangulate(poly)
                for t in tris:
                    coords_2d = np.array(t.exterior.coords)[:-1]
                    if len(coords_2d) != 3:
                        continue

                    # Z값 보간
                    f_indices = []
                    for pt_2d in coords_2d:
                        z = interpolate_z(tri_coords, pt_2d)
                        idx = get_v_idx((pt_2d[0], pt_2d[1], z))
                        f_indices.append(idx)

                    final_faces.append(f_indices)

        return meshio.Mesh(points=np.array(final_vertices),
                           cells=[("triangle", np.array(final_faces))])

    def weld(self, slope_mesh, threshold=0.1):
        """
        사면 메쉬의 끝점(Daylight)을 지형의 절단면 정점에 강제로 붙입니다.
        terrain_points: 클리핑이 완료된 지형의 정점들
        slope_mesh: add_slope로 생성된 meshio 객체
        threshold: 스냅을 허용할 최대 거리 (단위: m, 보통 10cm 내외)
        """
        slope_points = slope_mesh.points.copy()
        terrain_points = self.terrain_mesh.points
        # 1. 지형 정점들로 KD-Tree 구축 (고속 근접점 검색용)
        tree = cKDTree(terrain_points[:, :2])  # x, y 좌표만 비교

        # 2. 사면 메쉬에서 Daylight 정점들만 타겟팅
        # (보통 add_slope 로직상 정점 리스트의 뒷부분 절반이 Daylight입니다)
        n_half = len(slope_points) // 2
        daylight_indices = range(n_half, len(slope_points))

        for i in daylight_indices:
            pt = slope_points[i]
            # 3. 가장 가까운 지형 정점 찾기
            dist, idx = tree.query(pt[:2])

            if dist < threshold:
                # 4. 강제 용접 (지형의 x, y, z를 그대로 사면 정점에 이식)
                slope_points[i] = terrain_points[idx]

        return meshio.Mesh(points=slope_points, cells=slope_mesh.cells)
