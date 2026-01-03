from common.baseobjgenertor import BaseObjectGenerator
from infrastructure.filemanager import FileSystemService
import os

from kmpost.kmbuilder import KMObjectBuilder
from kmpost.kmouputmanager import KMOutputManager


class KMGenerator(BaseObjectGenerator):
    def __init__(self, state, logger):
        super().__init__(state, logger)
        self.base_source_directory = 'c:/temp/km_post/소스/'
        self.work_directory = 'c:/temp/km_post/result/'
        self.source_directory = ''
        self.structure_processor = None

    def generate(self):
        try:
            self.log("KM 생성 시작")
            self.prepare_directories()
            self.start_sta, self.end_sta = self.calculate_stations()
            self.load_structure_processor()
            builder_results = self.build_km_objects()
            self.output_files(builder_results)
            self.log("모든 작업이 완료됐습니다.")
        except Exception as e:
            self.log(f"[오류] {str(e)}")

    def prepare_directories(self):
        self.source_directory = os.path.join(self.base_source_directory, self.state.alignment_type)
        self.log(f"소스 경로: {self.source_directory}")

        FileSystemService.copy_all_files(
            self.source_directory,
            self.work_directory,
            include_extensions=['.jpg', '.png'],
            exclude_extensions=['.dxf', '.ai', '.csv'],
            is_delete_original=False
        )
        FileSystemService.ensure_directory(self.work_directory, self.log)
        self.log(f"대상 디렉토리: {self.state.target_directory}")

    def load_structure_processor(self):
        self.log("구조물 정보 불러오는 중...")
        self.structure_processor = self.load_structures()
        if self.structure_processor:
            self.log("구조물 정보가 성공적으로 로드되었습니다.")
        else:
            self.log("구조물 정보가 없습니다.")

    def build_km_objects(self):
        interval = 100 if self.state.alignment_type == '도시철도' else 200
        self.log("KM Object 생성 중...")
        builder = KMObjectBuilder(
            self.start_sta,
            self.end_sta,
            structure_processor=self.structure_processor,
            alignmenttype=self.state.alignment_type,
            offset=self.state.offset,
            interval=interval,
            reverse_start=self.state.reverse_start,
            is_reverse=self.state.is_reverse
        )
        return builder.run()

    def output_files(self, builder_results):
        output_manager = KMOutputManager(
            self.work_directory,
            self.state.target_directory,
            self.state.offset,
            self.state.is_two_track
        )
        index_datas, post_datas = output_manager.generate_images_csv_bve(
            builder_results, self.source_directory, self.state.alignment_type,self.state.start_index
        )
        self.log("파일 저장 중...")
        output_manager.save_txt_files(index_datas, post_datas)
        self.log("파일 복사 중...")
        output_manager.copy_result_files()


