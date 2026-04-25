import logging

class FileController:
    def __init__(self):
        self.filepath: str = ''

    # 파일 읽기 함수
    def read_file(self, filepath):
        self.filepath = filepath
        try:
            with open(self.filepath, 'r', encoding='utf-8') as file:
                lines = file.readlines()
        except UnicodeDecodeError:
            with open(self.filepath, 'r', encoding='euc-kr') as file:
                lines = file.readlines()

        return lines