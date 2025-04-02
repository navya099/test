from loggermodule import logger
from filemodule import TxTFileHandler
from util import *


class DataLoader:
    def __init__(self, design_params, file_paths):
        self.design_params = design_params
        self.file_paths = file_paths
        self.last_block = None
        # ✅ StringVar를 사용하여 안전하게 값 가져오기
        try:
            self.designspeed = int(taskwizard.inputs[0].get())  # 설계 속도
            self.linecount = int(taskwizard.inputs[1].get())  # 선로 개수
            self.lineoffset = float(taskwizard.inputs[2].get())  # 선로 간격
            self.poledirection = int(taskwizard.inputs[3].get())  # 전주 방향
        except ValueError as e:
            logger.error(f"입력값 오류: {e}")
            self.designspeed = 0
            self.linecount = 1
            self.lineoffset = 0.0
            self.poledirection = 0

        # ✅ 파일 경로 설정 (None 체크 포함)
        self.curve_path = taskwizard.curve_info_path.get() if taskwizard.curve_info_path else ""
        self.pitch_path = taskwizard.pitch_info_path.get() if taskwizard.pitch_info_path else ""
        self.coord_path = taskwizard.coord_info_path.get() if taskwizard.coord_info_path else ""
        self.structure_path = taskwizard.structure_path.get() if taskwizard.structure_path else ""

        # ✅ 디버깅 로그 추가 (logger 오류 수정)
        logger.info(f"""🎯 DataLoader - 파일 경로 목록:
        curve_list: {self.curve_path}
        pitch_path: {self.pitch_path}
        coord_path: {self.coord_path}
        structure_path: {self.structure_path}""")

        # ✅ 파일 로드 (빈 문자열 예외 처리 추가)
        self.txtprocessor = TxTFileHandler()

        if self.curve_path:
            self.txtprocessor.set_filepath(self.curve_path)
            self.txtprocessor.read_file_content()
            self.data = self.txtprocessor.get_data()
        else:
            logger.error("curve_info 파일 경로가 설정되지 않았습니다.")
            self.curve_plist = []
        if self.pitch_path:
            self.txtprocessor.set_filepath(self.pitch_path)
            self.txtprocessor.read_file_content()
            self.pitch_list = self.txtprocessor.get_data()
        else:
            logger.error("pitch_info 파일 경로가 설정되지 않았습니다.")
            self.pitch_list = []
        if self.coord_path:
            self.txtprocessor.set_filepath(self.coord_path)
            self.txtprocessor.read_file_content()
            self.pitch_list = self.txtprocessor.get_data()
        else:
            logger.error("pitch_info 파일 경로가 설정되지 않았습니다.")
            self.pitch_list = []
        self.last_block = find_last_block(self.data)
        logger.info(f" last_block {self.last_block}")
        self.start_km = 0
        self.end_km = self.last_block // 1000  # 마지막 측점
        logger.info(f""" start_km : {self.start_km}
                    end_km {self.last_block}""")
