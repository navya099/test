from controller.dialogs import DialogService
from controller.mainrunner import MainRunner
from controller.prerunsetup import PreRunSetup
from controller.state import AppState


class AppController:
    def __init__(self, dialogs: DialogService):
        self.state = AppState()
        self.dialogs = dialogs
        self._logger = None

    def set_logger(self, logger_func):
        self._logger = logger_func

    def log(self, msg):
        if self._logger:
            self._logger(msg)

    def select_directory(self, state_attr: str, title: str):
        """공통 경로 선택 메서드"""
        path = self.dialogs.select_directory(title)
        if not path:
            self.log(f"❌ {title} 선택 취소")
            return False

        setattr(self.state, state_attr, path)
        self.log(f"{title} 선택됨: {path}")
        return True

    def select_file(self, state_attr: str, title: str, file_ext):
        """공통 파일 선택 메서드"""
        path = self.dialogs.select_file(title, file_ext=file_ext)
        if not path:
            self.log(f"❌ {title} 선택 취소")
            return False

        setattr(self.state, state_attr, path)
        self.log(f"{title} 선택됨: {path}")
        return True

    def set_structure_excelfile(self):
        self.select_file('structure_excel_path', '구조물 파일', '.xlsx')

    def set_target_directory(self):
        self.select_directory('target_directory', '대상 디렉토리')

    def set_infopath(self):
        self.select_file('info_path', 'info 파일 선택', '*.*')

    def run(self):
        #사전작업
        try:
            setup = PreRunSetup(
                dialogs=self.dialogs,
                state=self.state,
                logger=self.log
            )

            if not setup.run():
                self.log(f"사전 설정 실패")
                return

            runner = MainRunner(
                state=self.state,
                logger=self.log,
                generator_type=self.state.posttype
            )
            runner.run()
        except Exception as ex:
            self.log(f'치명적 실행 에러: {ex}')
            return

    def set_offset(self):
        result = self.dialogs.open_offset_setting()
        if result:
            self.state.offset = result
            self.log(f"오프셋 설정 완료: {result}")

    def update_state(self, gui_state: dict):
        for key, value in gui_state.items():
            setattr(self.state, key, value)
        self.log(f"상태 설정 완료")

    def set_track(self):
        result = self.dialogs.oepn_track_setting()
        if result:
            self.state.track_mode = result["mode"]
            self.state.track_direction = result["direction"]
            self.state.track_distance = result["distance"]
            self.state.track_index = result["index"]
            self.log(f"트랙 설정 완료: {result}")

