import logging

from coord.coord_sampler import CoordinateProcessor
from coordinate_utils import convert_coordinates
from dem.dem import DEMProcessor
from folder_manger.foleder_manger import FolderManager
from out.output_manger import OutputExporter
from segment.segment_manager import SegmentProcessor


class MainProcessor:
    def __init__(self, read_coords, structure_list, tracks):
        self.xyz_list = None
        self.xy_list = None
        self.dem_processor = None
        self.read_coords = read_coords
        self.structure_list = structure_list
        self.tracks = tracks
        self.coord_processor = CoordinateProcessor()

    def execute(self, selected_segments=None, is_visible=False):
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
                if selected_segments and idx not in selected_segments:
                    logging.info(f"Segment {idx} 건너뜀 (선택 구간 아님)")
                    continue
                self._process_segment(idx, seg, is_visible)
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

    def _process_segment(self, idx, seg, is_visible=False):
        processor = SegmentProcessor(self.dem_processor, self.xyz_list, structure_list=self.structure_list, tracks=self.tracks, read_coords=self.read_coords)
        processor.process_segment(idx, seg, is_visible=is_visible)
