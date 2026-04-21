import logging

from coord.coord_sampler import CoordinateProcessor
from coordinate_utils import convert_coordinates
from dem.dem import DEMProcessor
from dem.dem_exporter import DEMExporter
from terrain_manager.terrain_builder import TerrainBuilder
from track.processor import TrackProcessor
from track.track_creator import TrackCreator


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
            #좌표 샘플링
            self.xy_list, self.xyz_list = self.coord_processor.sample(read_coords=self.read_coords)
            #구간 리스트 생성
            segments = self.coord_processor.create_segments(self.read_coords,1000)
            # DEM 클래스 호출
            self.dem_processor = DEMProcessor(convert_coordinates(self.xy_list, 5186, 4326))
            #메인파이프실행
            for idx, seg in enumerate(segments, start=1):
                self._process_segment(idx, seg)

        except Exception as e:
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
        terrain_builder = TerrainBuilder(self.dem_processor, seg_coords)
        terrain_mesh = terrain_builder.build()
