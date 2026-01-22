import os

class PathResolver:
    BASE_PATH = "D:/다운로드/Railway/Object/철도표준도/전철전력"

    @classmethod
    def resolve(cls, names: list[str]) -> list[str]:
        return [
            os.path.join(cls.BASE_PATH, f"{name}.csv")
            for name in names
        ]
