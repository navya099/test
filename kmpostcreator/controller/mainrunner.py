import os

from infrastructure.filemanager import FileSystemService
from infrastructure.structuresystem import StructureProcessor
from kmpost.kmbuilder import KMObjectBuilder


class MainRunner:
    def __init__(self, state, logger):
        self.structure_list = None
        self.work_directory = ''
        self.state = state
        self.log = logger
        self.base_source_directory = 'c:/temp/km_post/소스/'  # 원본 소스 기본 경로
        self.source_directory = self.base_source_directory  # 실제 작업용 경로

    def run(self):
        try:
            self.log("작업 디렉토리 확인 중...")
            self.work_directory = 'c:/temp/km_post/result/'
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
            self.load_structures()

            if self.structure_list:
                self.log("구조물 정보가 성공적으로 로드되었습니다.")
            else:
                self.log("구조물 정보가 없습니다.")

            interval = 100 if self.state.alignment_type == '도시철도' else 200
            self.log("KM Object 생성 중...")
            builder = KMObjectBuilder(start_sta, end_sta, structure_list=self.structure_list,
                                      alignmenttype=self.state.alignment_type,
                                      offset=self.state.offset,
                                      interval=interval,
                                      source_directory=self.source_directory,
                                      work_directory=self.work_directory,
                                      target_directory=self.state.target_directory)
            index_datas, post_datas = builder.run()

            index_file = os.path.join(self.work_directory, 'km_index.txt')
            post_file = os.path.join(self.work_directory, 'km_post.txt')

            self.log(f"파일 작성: {index_file}")
            FileSystemService.create_txt(index_file, index_datas)

            self.log(f"파일 작성: {post_file}")
            FileSystemService.create_txt(post_file, post_datas)

            self.log("txt 작성이 완료됐습니다.")

            # 파일 복사
            self.log("결과 파일 복사 중...")
            FileSystemService.copy_all_files(self.work_directory, self.state.target_directory, ['.csv', '.png', '.txt', '.jpg'], ['.dxf', '.ai'])

            self.log("모든 작업이 완료됐습니다.")

        except Exception as e:
            self.log(f"[오류] {str(e)}")

    def calculate_stations(self):
        bc = self.state.brokenchain or 0
        return self.state.start_station + bc, self.state.end_station + bc

    def load_structures(self):
        processor = StructureProcessor(self.state.structure_excel_path)
        processor.process_structure(self.state.brokenchain or 0)
        self.structure_list = processor.structure_list
