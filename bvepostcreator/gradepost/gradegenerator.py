from common.baseobjgenertor import BaseObjectGenerator
from gradepost.preprocessor import VIPPreprocessor
from gradepost.profile_processor import ProfileProcessor
from infrastructure.filemanager import FileSystemService
import os
from kmpost.kmouputmanager import KMOutputManager

class GradeGenerator(BaseObjectGenerator):
    """기울기표 제너레이터"""
    def __init__(self, state, logger):
        super().__init__(state, logger)
        self.base_source_directory = 'c:/temp/pitch/소스/'
        self.work_directory = 'c:/temp/pitch/result/'
        self.source_directory = ''
        self.structure_processor = None
        self.pitch_info_path = self.state.info_path

    def generate(self):
        try:
            self.log("기울기표 생성 시작")
            self.prepare_directories()
            self.start_sta, self.end_sta = self.calculate_stations()
            self.load_structure_processor()
            # 전략 선택
            builder = VIPPreprocessor.get_builder(self.pitch_info_path)

            # 전처리 + vip데이터빌드
            prepare_data = builder.preprocess(self.pitch_info_path, self.state.brokenchain)
            vipdatas = builder.build(prepare_data, self.state.brokenchain)
            bveproseccoer = ProfileProcessor(self.source_directory, self.work_directory,
                                             self.state.target_directory, self.state.alignment_type, self.state.offset,
                                             self.state.start_index ,self.log)
            objectdatas = bveproseccoer.build(self.start_sta, self.end_sta, vipdatas, self.structure_processor)

            self.output_files(objectdatas)
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

    def output_files(self, builder_results):
        output_manager = KMOutputManager(
            self.work_directory,
            self.state.target_directory,
            self.state.offset,
            self.state.track_mode,
            self.state.track_direction,
            self.state.track_index
        )
        index_datas, post_datas = output_manager.generate_images_csv_bve(
            builder_results, self.source_directory, self.state.alignment_type,self.state.start_index
        )
        self.log("파일 저장 중...")
        output_manager.save_txt_files(index_datas, post_datas)
        self.log("파일 복사 중...")
        output_manager.copy_result_files()
