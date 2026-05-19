import numpy as np

from daylight import SlopeManager
from function import horizontal_distance, create_segment, filter_coords_by_segment, farthest_point
from ground import ExistGround
from terrain import TerrainBuilder
from track import get_track_edges
from visualize import SectionVisualizer


class SectionProvider:
    def __init__(self, dem_processor, structure_list, slope_ratio, read_coords, xylist, xyzlist, track_width, stations):
        self.dem_p = dem_processor
        self.structures = structure_list
        self.slope_ratio = slope_ratio
        self.read_coords = read_coords
        self.xy_list = xylist
        self.xyz_list = xyzlist
        self.track_width = track_width
        self.stations = stations
    def get_section(self, station_idx):
        """특정 인덱스의 측점을 3D Slice하여 2D 데이터로 반환"""
        try:
            #기본 변수
            station = self.stations[station_idx] #현재 측점
            center = self.xy_list[station_idx] #현재 측점 좌표 z미포함)
            centerz = self.xyz_list[station_idx] #현재 측점 좌표 z 포함)

            # 코리더 영역
            corridor = create_segment(center, buffer_x=500, buffer_y=100) #중심 좌표에서 좌우 +-500 앞뒤 100의 세미지형 생성을 위한 영역생성
            #코리더 영역으로 지형 메쉬 생성. 메쉬는 meshio.Mesh객체
            terrain_builder = TerrainBuilder(self.dem_p, corridor)
            terrain_mesh = terrain_builder.build(station_idx)

            #코리더 영역 내의 선형 좌표 필터링
            seg_coords = filter_coords_by_segment(self.xyz_list, corridor)

            # [수정 1단계] 전체 세그먼트 에지 리스트에서 '현재 측점'의 인덱스 찾아내기
            # self.xyz_list에서 현재 측점의 좌표를 기준으로 seg_coords 내의 인덱스를 매칭합니다.
            current_pt_xyz = self.xyz_list[station_idx]

            # seg_coords 내에서 현재 중심점과 x, y가 일치하는 위치(인덱스)를 찾습니다.
            current_local_idx = 0
            for i, coord in enumerate(seg_coords):
                if np.isclose(coord[0], current_pt_xyz[0]) and np.isclose(coord[1], current_pt_xyz[1]):
                    current_local_idx = i
                    break

            #트랙 생성(코리더 영역 내)
            track_edges = get_track_edges(seg_coords,self.track_width)

            # 2. 사면 생성 (해당 지점만)
            # SlopeManager 역시 Micro-Mesh 위에서만 동작하므로 매우 빠름. 반환 - 좌우 meshio.Mesh객체
            slope_manager = SlopeManager(self.dem_p, terrain_mesh)
            slope_left, slope_right = slope_manager.build_slopes(track_edges, self.slope_ratio)

            lside, rside = track_edges #트랙 엣지 좌우 사이드 분리

            # 이제 0번 인덱스가 아니라, 현재 측점에 딱 맞는 에지 좌표를 기준으로 삼습니다.
            current_lside = lside[current_local_idx]
            current_rside = rside[current_local_idx]

            # get_section 내부에서 호출 시
            # normal_vec 계산 (진행방향 벡터 [dx, dy]를 90도 회전)
            p1 = np.array(self.xy_list[station_idx])
            p2 = np.array(self.xy_list[min(station_idx + 1, len(self.xy_list) - 1)])
            direction = p2 - p1
            normal = np.array([-direction[1], direction[0]])  # 시계반대방향 90도 회전

            #디버그
            print("lside:", type(lside), lside)
            print("slope_left:", type(slope_left), slope_left)

            # --- [수정] 메쉬의 정점 인덱스 구조를 활용한 1:1 다이렉트 매칭 ---
            # SlopeBuilder가 생성한 메쉬는 points의 앞쪽 절반이 선로 에지, 뒤쪽 절반이 사면 끝점입니다.
            # 이 규칙을 활용하면 슬라이싱 노이즈 없이 완벽한 3D 교점을 즉시 가져옵니다.

            n_points_l = len(slope_left.points)
            n_half_l = n_points_l // 2

            n_points_r = len(slope_right.points)
            n_half_r = n_points_r // 2

            # 현재 측점에 정확히 매칭되는 사면 끝점(Daylight Point) 인덱스 참조
            # 뒤쪽 절반 데이터에서 현재 local 인덱스를 더해줍니다.
            slope_left_end = slope_left.points[n_half_l + current_local_idx]
            slope_right_end = slope_right.points[n_half_r + current_local_idx]

            # --- [수정] 종단 성분을 제거한 순수 횡방향 수평 거리 계산 ---
            unit_normal = normal / np.linalg.norm(normal)

            # 좌측 에지에서 좌측 사면 끝점까지의 변위 벡터 -> 법선 정사영
            v_l = np.array([slope_left_end[0] - current_lside[0], slope_left_end[1] - current_lside[1]])
            ld = abs(np.dot(v_l, unit_normal))

            # 우측 에지에서 우측 사면 끝점까지의 변위 벡터 -> 법선 정사영
            v_r = np.array([slope_right_end[0] - current_rside[0], slope_right_end[1] - current_rside[1]])
            rd = abs(np.dot(v_r, unit_normal))

            # 디버그 콘솔 출력
            print(f"[인덱스 매칭 완료] 측점 내부 인덱스: {current_local_idx}")
            print(f"정밀 ld: {ld:.4f}m, 끝점 고도: {slope_left_end[2]:.2f}m")
            print(f"정밀 rd: {rd:.4f}m, 끝점 고도: {slope_right_end[2]:.2f}m")

            # 함수 실행
            dist_g, elev_g = ExistGround.extract_ground_line(
                terrain_mesh=terrain_mesh,
                center_pt=center,  # [x, y, z]
                normal_vec=normal,
                width=50,  # 좌우 50m
                step=0.5  # 0.5m 간격으로 정밀하게 추출
            )

            section_result = {
                'station': station, #측점
                'isstructure': False, #구조물 여부
                'center': centerz, #중심 좌표 x,y,z
                'left': current_lside, #좌측 선로끝 좌표
                'right': current_rside, #우측 선로 끝 좌표
                'slope_l': [ld, slope_left_end[2]], #좌측 사면 좌표
                'slope_r': [rd, slope_right_end[2]], #우측 사면 좌표
                'left_dist': ld, #좌측 선로끝 좌표에서 좌측사면 끝까지의 수평거리
                'right_dist': rd,#우측 선로끝 좌표에서 우측사면 끝까지의 수평거리
                'ground': (dist_g, elev_g),  # ✅ 원지반선 저장,
                'slope_right_mesh': slope_right,
                'slope_left_mesh': slope_left,
                'terrain_mesh': terrain_mesh,
                'track_width': self.track_width
            }
            return section_result

        except Exception as e:
            raise e