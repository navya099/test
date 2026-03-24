# controller/dialogs.py
from abc import ABC, abstractmethod

class DialogService(ABC):
    @abstractmethod
    def select_file(self, title, file_ext) -> str | None:
        pass

    @abstractmethod
    def select_directory(self, title) -> str | None:
        pass

    @abstractmethod
    def select_option_list(self, option_list: list[str]) -> str | None:
        pass

    @abstractmethod
    def open_offset_setting(self) -> dict[str, str] | None:
        pass

    @abstractmethod
    def oepn_track_setting(self) -> dict[str, str] | None:
        pass
