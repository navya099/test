class FileController:
    def __init__(self, path: str | None = None):
        self.path = path
        self.lines: list[str] = []

    def set_path(self, path: str):
        self.path = path

    def load(self):
        if not self.path:
            raise ValueError("파일 경로가 설정되지 않았습니다.")

        with open(self.path, 'r', encoding='utf-8') as f:
            self.lines = f.readlines()

    def get_lines(self) -> list[str]:
        return self.lines
