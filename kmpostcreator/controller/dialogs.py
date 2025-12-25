# controller/dialogs.py
from abc import ABC, abstractmethod

class DialogService(ABC):
    @abstractmethod
    def select_excel_file(self) -> str | None:
        pass

    @abstractmethod
    def select_directory(self) -> str | None:
        pass

    @abstractmethod
    def select_alignment(self) -> str | None:
        pass
