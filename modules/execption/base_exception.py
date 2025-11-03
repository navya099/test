class BaseError(Exception):
    """모든 예외의 기본 클래스"""

    def __init__(self, message: str, code):
        super().__init__(message)
        self.code = code

    def __str__(self):
        return f"[{self.code.name}] {self.args[0]}"
