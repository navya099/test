import logging

from coord.coord_sampler import CoordinateProcessor
from coordinate_utils import convert_coordinates
from corridor.corridor_section import CorridorSection
from dem.dem import DEMProcessor
from folder_manger.foleder_manger import FolderManager
from mesh.mesh_modifier import MeshModifier
from out.output_manger import OutputExporter
from plot.plot import MeshPlotter
from slope.slope_manager import SlopeManager
from terrain.terrain_assembler import TerrainAssembler
from terrain.terrain_builder import TerrainBuilder
from track.processor import TrackProcessor
from util import get_stations, get_earthwork_sections, is_bridge_tunnel


class MainProcessor:
    def __init__(self, read_coords, structure_list):
        self.xyz_list = None
        self.xy_list = None
        self.dem_processor = None
        self.read_coords = read_coords
        self.structure_list = structure_list

        self.coord_processor = CoordinateProcessor()

    def execute(self):
        logging.debug("MainProcessor 실행 시작")
        # 전체 파이프라인 실행
        try:
            #기본 폴더 준비
            obj_path = 'C:/temp/OBJ/'
            dem_path = 'C:/temp/DEM/'
            shp_path = 'C:/temp/SHP/'
            FolderManager.create(obj_path)
            FolderManager.create(dem_path)
            FolderManager.create(shp_path)

            #좌표 샘플링
            self.xy_list, self.xyz_list = self.coord_processor.sample(read_coords=self.read_coords)
            #구간 리스트 생성
            segments = self.coord_processor.create_segments(self.xy_list,1000)
            # DEM 클래스 호출
            self.dem_processor = DEMProcessor(convert_coordinates(self.xy_list, 5186, 4326))
            #메인파이프실행
            for idx, seg in enumerate(segments, start=1):
                self._process_segment(idx, seg)
            #파이프 실행 후 외부 파일로 저장
            self.dem_processor.close()  # ✅ 프로그램 종료 직전에 닫기

            # 구간별 Shapefile 저장
            logging.info('Shapefile 저장중')
            OutputExporter.save_shapefile(segments)

            logging.info('QML 저장중')
            OutputExporter.save_qml(segments)


            logging.info(f'전체 작업 완료')

        except Exception as e:
            logging.info(f'작업 도중 실패')
            logging.critical(e)
            raise e

    def _process_segment(self, idx, seg):
        """세그먼트별 파이프라인"""
        logging.info(f"Segment {idx} 처리 시작")

        #세그먼트 필터링 좌표리스트
        seg_coords = CoordinateProcessor.filter_coords_by_segment(self.read_coords, seg)

        logging.debug(f"Segment {idx} coords: {len(seg_coords)}")

        if len(seg_coords) < 2:
            #세그먼트 길이 부족시
            logging.warning(f'Segment {idx}  len coords two points')
            return

        #트랙빌더
        track_manager = TrackProcessor(seg_coords)
        track_mesh, track_edges = track_manager.build_track()
        logging.debug(
            f"Segment {idx} Track mesh points: {len(track_mesh.points)}, faces: {len(track_mesh.cells[0].data)}")

        #지형 빌더
        terrain_builder = TerrainBuilder(self.dem_processor, seg)
        terrain_mesh = terrain_builder.build()
        logging.debug(
            f"Segment {idx} Terrain mesh points: {len(terrain_mesh.points)}, faces: {len(terrain_mesh.cells[0].data)}")

        #사면 빌더
        #변경1 사면을 전체 트랙 생성에서 구조몰구간별로
        #추가 seg_coords를 구조물로 필터링
        #정보 self.read_coords의 인덱스에서 현재 좌표의 측점 계산가능
        #self.read_coords[0] = 0.0, self.read_coords[i] == 25* i

        #현재 구간의 측점 리스트
        stations = get_stations(self.read_coords, seg_coords)

        #측점 리스트에서 토공구간 분리
        earth_list = get_earthwork_sections(seg_coords, stations, self.structure_list)

        # 구조물 갯수 로그
        # 세그먼트 시작/끝 측점 계산
        seg_start_sta = stations[0]
        seg_end_sta = stations[-1]
        logging.info(f"Segment {idx} 범위: {seg_start_sta} ~ {seg_end_sta}")
        logging.debug(f"Segment {idx} stations: {stations}")

        # 교량 갯수
        bridge_count = sum(
            1 for name, start, end in self.structure_list['bridge']
            if not (end < seg_start_sta or start > seg_end_sta)
        )

        # 터널 갯수
        tunnel_count = sum(
            1 for name, start, end in self.structure_list['tunnel']
            if not (end < seg_start_sta or start > seg_end_sta)
        )

        logging.info(f"Segment {idx} 교량 갯수: {bridge_count}")
        logging.info(f"Segment {idx} 터널 갯수: {tunnel_count}")
        logging.info(f"Segment {idx} 토공 구간 갯수: {len(earth_list)}")

        #여러 토공구간 순회 처리
        slope_manger = SlopeManager(self.dem_processor, terrain_mesh)
        slope_lefts = []
        slope_rights = []
        for corridor_idx, corridor in enumerate(earth_list, start=1):
            logging.info(f"Segment {idx} Corridor {corridor_idx} 처리 시작")
            logging.debug(f"Segment {idx} Corridor {corridor_idx} indices: {corridor['indices']}")
            earth_left_side = [track_edges[0][i] for i in corridor["indices"]]
            earth_right_side = [track_edges[1][i] for i in corridor["indices"]]

            slope_left, slope_right = slope_manger.build_slopes((earth_left_side, earth_right_side), slope_ratio=1.5)
            logging.debug(
                f"Segment {idx} Slope Left {i} points: {len(slope_left.points)}, faces: {len(slope_left.cells[0].data)}")
            logging.debug(
                f"Segment {idx} Slope Right {i} points: {len(slope_right.points)}, faces: {len(slope_right.cells[0].data)}")

            slope_lefts.append(slope_left)
            slope_rights.append(slope_right)

        #계획지표면 생성(사면 외곽선 추출 및 지형 클리핑
        logging.info(f"Segment {idx} 지형 생성중")
        terrain_assembler = TerrainAssembler(self.dem_processor, slope_manger)
        clipped_terrain, fixed_slope_left, fixed_slope_right = terrain_assembler.build(idx, slope_lefts, slope_rights, terrain_mesh)

        logging.debug(f"Clipped terrain points: {len(clipped_terrain.points)}")
        logging.debug(f"Clipped terrain faces: {len(clipped_terrain.cells[0].data)}")


        #평행이동
        # 평행이동
        track_mesh = MeshModifier(track_mesh).translate(self.xyz_list[idx - 1])
        clipped_terrain = MeshModifier(clipped_terrain).translate(self.xyz_list[idx - 1])

        fixed_slope_left = [MeshModifier(sl).translate(self.xyz_list[idx - 1]) for sl in fixed_slope_left]
        fixed_slope_right = [MeshModifier(sr).translate(self.xyz_list[idx - 1]) for sr in fixed_slope_right]

        logging.debug(f"Segment {idx} translated Track points: {len(track_mesh.points)}")
        logging.debug(f"Segment {idx} translated Terrain points: {len(clipped_terrain.points)}")

        #저장
        logging.info(f"Segment {idx} 지형 저장중")
        # 3. 결과 저장 (clipped_terrain 사용)
        OutputExporter.save_obj_with_groups(f"c:/temp/obj/segment_{idx}.obj",
                             clipped_terrain.points, clipped_terrain.cells[0].data,
                             track_mesh.points, track_mesh.cells[0].data, fixed_slope_left, fixed_slope_right)

        logging.info(f"병합된 지표면 저장 완료: segment_{idx}")

        # PYVISTA 시각화
        plot_items = [
            (track_mesh.points, track_mesh.cells[0].data, "blue", "Track"),
            (clipped_terrain.points, clipped_terrain.cells[0].data, "orange", "Clipped Terrain")
        ]

        # 좌측 사면 여러 개 추가
        for i, sl in enumerate(fixed_slope_left, start=1):
            plot_items.append((sl.points, sl.cells[0].data, "green", f"Slope Left {i}"))

        # 우측 사면 여러 개 추가
        for i, sr in enumerate(fixed_slope_right, start=1):
            plot_items.append((sr.points, sr.cells[0].data, "red", f"Slope Right {i}"))

        MeshPlotter.plot_multiple_meshes(plot_items)

