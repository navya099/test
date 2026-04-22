import shutil
import os

class FolderManager:
    """폴더 관리 클래스"""
    def __init__(self):
        self.folder = None

    @staticmethod
    def create(path):
        """폴더 생성"""
        shutil.rmtree("C:/temp/OBJ", ignore_errors=True) #기존 폴더 삭제
        os.makedirs("C:/temp/OBJ", exist_ok=True) #폴더 생성