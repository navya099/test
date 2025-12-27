from controller.dialogs import DialogService
from controller.mainrunner import MainRunner
from controller.prerunsetup import PreRunSetup
from controller.state import AppState


class AppController:
    def __init__(self, dialogs: DialogService):
        self.state = AppState()
        self.dialogs = dialogs
        self._logger = None

    def set_alignment(self, value):
        self.state.alignment_type = value
        self.log(f"노선 종류 선택됨: {value}")

    def set_logger(self, logger_func):
        self._logger = logger_func

    def log(self, msg):
        if self._logger:
            self._logger(msg)

    def select_structure_excel(self):
        path = self.dialogs.select_excel_file()

        if not path:
            self.log("❌ 엑셀 파일 선택 취소")
            return False

        self.state.structure_excel_path = path
        self.log(f"엑셀 파일 선택됨: {path}")
        return True

    def select_directory(self):
        path = self.dialogs.select_directory()

        if not path:
            self.log("❌ 대상 디렉토리 선택 취소")
            return False

        self.state.target_directory = path
        self.log(f"대상 디렉토리 선택됨: {path}")
        return True

    def run(self):
        #사전작업
        setup = PreRunSetup(
            dialogs=self.dialogs,
            state=self.state,
            logger=self.log
        )

        if not setup.run():
            return

        runner = MainRunner(
            state=self.state,
            logger=self.log,
            generator_type=self.state.posttype
        )
        runner.run()
