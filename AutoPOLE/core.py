from util import *
from loggermodule import logger
from polemodule import *
from dataloader import *


class MainProcess:
    def __init__(self, design_params, file_paths):
        self.design_params = design_params
        self.file_paths = file_paths
        self.processes = []  # ✅ 실행할 프로세스들을 리스트로 관리

    def setup_processes(self):
        """✅ 실행할 모든 프로세스를 리스트에 추가"""
        loader = DataLoader(self.design_params, self.file_paths)
        pole_processor = PolePositionManager(loader.params)
        logger.debug(f"🚀 PolePositionManager.get_pole_data() 반환값: {pole_processor.get_pole_data()}")

        bracket_manager = BracketManager(pole_processor.get_pole_data())
        #drawing_manager = DrawingManager(pole_processor)  # 도면 작성 클래스
        #wire_manager = WireManager(pole_processor)  # 전선 관리 클래스
        #output_manager = OutputManager()  # 파일 출력 클래스

        self.processes.extend([
            pole_processor,
            bracket_manager
        ])

    def run(self):
        """✅ 등록된 모든 프로세스를 실행"""
        try:
            self.setup_processes()  # 실행할 프로세스들을 등록
            for process in self.processes:
                process.run()  # 각 프로세스 실행
                logger.debug(f'정보 : {process.__class__.__name__} 실행 완료')

        except Exception as ex:
            logger.error(f'에러 : {ex}', exc_info=True)

