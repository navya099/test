from util import *
from loggermodule import logger
from polemodule import *
from dataloader import *
from filemodule import *
from bvemodule import *
from wiremodule import WirePositionManager


class MainProcess:
    def __init__(self, design_params, file_paths):
        self.design_params = design_params
        self.file_paths = file_paths

    def run(self):
        """✅ 등록된 모든 프로세스를 실행"""
        try:
            loader = DataLoader(self.design_params, self.file_paths)
            logger.debug(f'정보 : DataLoader 실행 완료')
            pole_processor = PolePositionManager(loader.params)
            pole_processor.run()
            logger.debug(f'정보 : PolePositionManager 실행 완료')
            bracket_manager = BracketManager(loader.params, pole_processor.poledata)
            bracket_manager.run()
            logger.debug(f'정보 : BracketManager 실행 완료')
            mastmanager = MastManager(loader.params, pole_processor.poledata)
            mastmanager.run()
            logger.debug(f'정보 : MastManager 실행 완료')
            wiremanager = WirePositionManager(loader.params, pole_processor.poledata)
            wiremanager.run()
            csvmanager = BVECSV(pole_processor.poledata,  wiremanager.wiredata)
            csvmanager.create_pole_csv()
            csvmanager.create_csvtotxt()
            csvmanager.create_wire_csv()
            csvmanager.create_csvtotxt()
            logger.debug(f'정보 : BVECSV 실행 완료')
            '''
            obj = ObjectSaver(bracket_manager)
            logger.debug(f'정보 : 테스트용 객체 저장 실행 완료')
            obj.save_to_txt('c:/temp/object_data.txt')  # 텍스트 파일 저장
            obj.save_to_json('c:/temp/object_data.json')  # json 파일 저장
            '''
            logger.debug(f'정보 : 모든 프로세스 실행 완료')
        except Exception as ex:
            logger.error(f'에러 : {ex}', exc_info=True)
