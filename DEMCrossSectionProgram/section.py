import numpy as np

from daylight import SlopeManager
from function import horizontal_distance, create_segment
from ground import ExistGround
from terrain import TerrainBuilder


class SectionProvider:
    def __init__(self, dem_processor, structure_list, track_edges, slope_ratio, read_coords, xylist):
        self.dem_p = dem_processor
        self.structures = structure_list
        self.track_edges = track_edges
        self.slope_ratio = slope_ratio
        self.read_coords = read_coords
        self.xy_list = xylist

    def get_section(self, station_idx):
        """특정 인덱스의 측점을 3D Slice하여 2D 데이터로 반환"""
        try:
            center = self.xy_list[station_idx]
            seg = create_segment(center, buffer_x=500, buffer_y=100)
            # 1. Micro-Mesh 범위 설정 (중심 기준 좌우 50m, 전후 5m)
            # TerrainBuilder가 이 범위를 인식하도록 수정하거나,
            # seg 데이터를 해당 범위에 맞게 crop해서 전달
            terrain_builder = TerrainBuilder(self.dem_p, seg)
            terrain_mesh = terrain_builder.build(station_idx)

            # 2. 사면 생성 (해당 지점만)
            # SlopeManager 역시 Micro-Mesh 위에서만 동작하므로 매우 빠름
            slope_manager = SlopeManager(self.dem_p, terrain_mesh)
            slope_left, slope_right = slope_manager.build_slopes([self.track_edges[0][station_idx],self.track_edges[1][station_idx]], self.slope_ratio)
            lside, rside = self.track_edges[station_idx]

            # get_section 내부에서 호출 시
            # normal_vec 계산 (진행방향 벡터 [dx, dy]를 90도 회전)
            p1 = np.array(self.xy_list[station_idx])
            p2 = np.array(self.xy_list[min(station_idx + 1, len(self.xy_list) - 1)])
            direction = p2 - p1
            normal = np.array([-direction[1], direction[0]])  # 시계반대방향 90도 회전

            ld = horizontal_distance(lside, slope_left)
            rd = horizontal_distance(rside, slope_right)

            # 함수 실행
            dist_g, elev_g = ExistGround.extract_ground_line(
                terrain_mesh=terrain_mesh,
                center_pt=self.xy_list[station_idx][1:4],  # [x, y, z]
                normal_vec=normal,
                width=50,  # 좌우 50m
                step=0.5  # 0.5m 간격으로 정밀하게 추출
            )
            return {
                'station': 'station', #측점
                'isstructure': False, #구조물 여부
                'center': center, #중심 좌표 x,y,z
                'left': lside, #좌측 선로끝 좌표
                'right': rside, #우측 선로 끝 좌표
                'left_end': slope_left, #좌측 사면 좌표
                'right_end': slope_right, #우측 사면 좌표
                'left_dist': dist_g[0], #좌측 선로끝 좌표에서 좌측사면 끝까지의 수평거리
                'right_dist': dist_g[1],#우측 선로끝 좌표에서 우측사면 끝까지의 수평거리
                'ground_profile': (dist_g, elev_g)  # ✅ 원지반선 저장
            }
        except Exception as e:
            raise e