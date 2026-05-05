from pathlib import Path

class FileLocator:
    def __init__(self, root_dir):
        self.root = Path(root_dir)
        self.cache = {}  # name -> fullpath

    def find(self, filename: str) -> str | None:
        if not filename.endswith(".csv"):
            filename += ".csv"

        # 캐시 히트
        if filename in self.cache:
            return self.cache[filename]

        for path in self.root.rglob(filename):
            self.cache[filename] = str(path)
            return str(path)

        return None
