from util import *
from loggermodule import logger
from polemodule import *
from dataloader import *


class MainProcess:
    def __init__(self, design_params, file_paths):

        self.design_params = design_params
        self.file_paths = file_paths
        logger.info(f'정보 : MainProcess 초기화 완료')

    def run(self):
        try:
            loader = DataLoader(self.design_params, self.file_paths)
            logger.debug(f'정보 : DataLoader 초기화 완료')
            # poleprocessor = PolePositionManager(loader)
            logger.debug(f'정보 : PolePositionManager 초기화 완료')
        except Exception as ex:
            logger.error(f'에러 : {ex}',exc_info= True)
