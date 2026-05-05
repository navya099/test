import os

class PathResolver:
    BASE_PATH = r"D:\BVE\루트\Railway\Object\철도표준라이브러리\전철전력"

    @classmethod
    def resolve(cls, names: list[str]) -> list[str]:
        return [
            os.path.join(cls.BASE_PATH, f"{name}.csv")
            for name in names
        ]
