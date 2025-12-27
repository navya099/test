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
            self.log("작업 디렉토리 확인 중...")

            FileSystemService.ensure_directory(self.work_directory, self.log)

            self.log(f"대상 디렉토리: {self.state.target_directory}")
            self.source_directory = os.path.join(
                self.base_source_directory,
                self.state.alignment_type
            )
            self.log(f"소스 경로: {self.source_directory}")

            start_sta, end_sta = self.calculate_stations()
            self.log(f"시작 측점 = {start_sta}")
            self.log(f"마지막 측점 = {end_sta}")

            self.log("구조물 정보 불러오는 중...")
            self.structure_processor = self.load_structures()

            if self.structure_processor:
                self.log("구조물 정보가 성공적으로 로드되었습니다.")
            else:
                self.log("구조물 정보가 없습니다.")

            interval = 100 if self.state.alignment_type == '도시철도' else 200
            self.log("KM Object 생성 중...")
            builder = KMObjectBuilder(start_sta, end_sta, structure_processor=self.structure_processor,
                                      alignmenttype=self.state.alignment_type,
                                      offset=self.state.offset,
                                      interval=interval,
                                      reverse_start=self.state.reverse_start,
                                      is_reverse=self.state.is_reverse)
            builder_results = builder.run()

            # Output Manager에게 위임
            output_manager = KMOutputManager(self.work_directory, self.state.target_directory, self.state.offset)
            index_datas ,post_datas = output_manager.generate_images_csv_bve(builder_results, self.source_directory, self.state.alignment_type)
            self.log("파일 저장 중...")
            output_manager.save_txt_files(index_datas, post_datas)
            self.log("파일 복사 중...")
            output_manager.copy_result_files()
            self.log("모든 작업이 완료됐습니다.")

        except Exception as e:
            self.log(f"[오류] {str(e)}")
