from common.baseobjgenertor import BaseObjectGenerator
from curvepost.curve_output_manager import CURVEOutputManager
from curvepost.curve_processor import CurveProcessor
from curvepost.preprocessor import CurvePreprocessor
from infrastructure.filemanager import FileSystemService
import os
from kmpost.kmouputmanager import KMOutputManager

class CurveGenerator(BaseObjectGenerator):
    """곡선표 제너레이터"""
    def __init__(self, state, logger):
        super().__init__(state, logger)
        self.base_source_directory = 'c:/temp/curve/소스/'
        self.work_directory = 'c:/temp/curve/result/'
        self.source_directory = ''
        self.structure_processor = None
        self.info_path = self.state.info_path

    def generate(self):
        try:
            self.log("곡선표 생성 시작")
            self.prepare_directories()
            self.start_sta, self.end_sta = self.calculate_stations()
            self.load_structure_processor()
            # 전략 선택
            builder = CurvePreprocessor.get_builder(self.info_path)

            # 전처리 + ip데이터빌드
            prepare_data = builder.preprocess(self.info_path, self.state.brokenchain)
            ipdatas = builder.build(prepare_data, self.state.brokenchain)

            #object데이터 빌드
            bveproseccoer = CurveProcessor(self.source_directory, self.work_directory,
                                             self.state.target_directory, self.state.alignment_type, self.state.offset,
                                             self.state.start_index ,self.log)
            objectdatas = bveproseccoer.build(self.start_sta, self.end_sta, ipdatas, self.structure_processor)

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
        output_manager = CURVEOutputManager(
            self.work_directory,
            self.state.target_directory,
            self.state.offset,
            self.state.track_mode,
            self.state.track_direction,
            self.state.track_index
        )

        self.log("파일 저장 중...")
        post_file = os.path.join(self.work_directory, 'curve_post.txt')
        index_file = os.path.join(self.work_directory, 'curve_index.txt')
        post_data = output_manager.create_curve_post_txt(builder_results)
        output_manager.create_curve_index_txt(builder_results, index_file)
        FileSystemService.create_txt(post_file, post_data)

        self.log("파일 복사 중...")
        output_manager.copy_result_files()
