# controller/controller.py
from kmpostcreator.controller.dialogs import DialogService
from kmpostcreator.controller.state import AppState
from kmpostcreator.controller.mainrunner import MainRunner

class AppController:
    def __init__(self, dialogs: DialogService):
        self.state = AppState()
        self.dialogs = dialogs
        self._logger = None

    def select_alignment(self, widget):
        widget.show_alignment_selector(self._set_alignment)

    def _set_alignment(self, value):
        self.state.alignment_type = value
        self.log(f"노선 종류 선택됨: {value}")

    def set_logger(self, logger_func):
        self._logger = logger_func

    def log(self, msg):
        if self._logger:
            self._logger(msg)

    def run(self):
        self.state.target_directory = self.dialogs.select_directory()

        runner = MainRunner(
            state=self.state,
            logger=self.log
        )
        runner.run()
