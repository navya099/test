import logging

from coord.coord_sampler import CoordinateProcessor
from coordinate_utils import convert_coordinates
from dem.dem import DEMProcessor
from folder_manger.foleder_manger import FolderManager
from mesh.mesh_modifier import MeshModifier
from out.output_manger import OutputExporter
from plot.plot import MeshPlotter
from slope.slope_manager import SlopeManager
from terrain.terrain_assembler import TerrainAssembler
from terrain.terrain_builder import TerrainBuilder
from track.processor import TrackProcessor

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
            logging.info('구간별 Shapefile 저장')
            OutputExporter.save_shapefile(segments)

            logging.info('구간별 QML 생성')
            OutputExporter.save_qml(segments)


            logging.info(f'전체 작업 완료')

        except Exception as e:
            logging.info(f'작업 도중 실패')
            logging.critical(e)
            raise e

    def _process_segment(self, idx, seg):
        """세그먼트별 파이프라인"""
        logging.debug(f"Segment {idx} 처리 시작")

        #세그먼트 필터링 좌표리스트
        seg_coords = CoordinateProcessor.filter_coords_by_segment(self.read_coords, seg)
        logging.info(f"Segment {idx} coords: {len(seg_coords)}")

        if len(seg_coords) < 2:
            #세그먼트 길이 부족시
            logging.warning(f'Segment {idx}  len coords two points')
            return

        #트랙빌더
        track_manager = TrackProcessor(seg_coords)
        track_mesh = track_manager.build_track()

        #지형 빌더
        terrain_builder = TerrainBuilder(self.dem_processor, seg)
        terrain_mesh = terrain_builder.build()

        #사면 빌더
        slope_manger = SlopeManager(self.dem_processor)
        slope_left, slope_right = slope_manger.build_slopes(track_mesh, slope_ratio=1.5)

        logging.debug(f"Slope Left vertices: {slope_left.points.shape}")
        logging.debug(f"Slope Left faces : {slope_left.cells[0].data.shape}")
        logging.debug(f"Slope Right vertices: {slope_right.points.shape}")
        logging.debug(f"Slope Right faces: {slope_right.cells[0].data.shape}")

        #계획지표면 생성(사면 외곽선 추출 및 지형 클리핑
        terrain_assembler = TerrainAssembler(self.dem_processor, slope_manger)
        clipped_terrain, fixed_slope_left, fixed_slope_right = terrain_assembler.build(idx, slope_left, slope_right, terrain_mesh)

        logging.debug(f"Clipped terrain points: {len(clipped_terrain.points)}")
        logging.debug(f"Clipped terrain faces: {len(clipped_terrain.cells[0].data)}")


        """#평행이동
        track_mesh = MeshModifier(track_mesh).translate(self.xyz_list[idx - 1])
        fixed_slope_left = MeshModifier(fixed_slope_left).translate(self.xyz_list[idx - 1])
        fixed_slope_right = MeshModifier(fixed_slope_right).translate(self.xyz_list[idx - 1])
        clipped_terrain = MeshModifier(clipped_terrain).translate(self.xyz_list[idx - 1])
        """

        #저장
        # 3. 결과 저장 (clipped_terrain 사용)
        OutputExporter.save_obj_with_groups(f"c:/temp/obj/segment_{idx}.obj",
                             clipped_terrain.points, clipped_terrain.cells[0].data,
                             track_mesh.points, track_mesh.cells[0].data, fixed_slope_left, fixed_slope_right)

        logging.info(f"병합된 지표면 저장 완료: segment_{idx}")

        # PYVISTA 시각화
        MeshPlotter.plot_multiple_meshes(
            [
                (clipped_terrain.points, clipped_terrain.cells[0].data, "orange", "Clipped Terrain")
            ]
        )
