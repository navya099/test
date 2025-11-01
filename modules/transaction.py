import copy

class Transaction:
    def __init__(self, obj):
        """
        obj: 트랜잭션을 적용할 원본 객체 (딕셔너리, 리스트 등)
        """
        self._original = obj
        self._backup = None
        self._active = False

    def __enter__(self):
        """with 블록 진입 시 트랜잭션 시작"""
        if self._active:
            raise RuntimeError("Transaction already started")
        self._backup = copy.deepcopy(self._original)
        self._active = True
        print("Transaction started.")
        return self  # 트랜잭션 객체 반환

    def __exit__(self, exc_type, exc_val, exc_tb):
        """with 블록 종료 시 호출: 예외 없으면 commit, 있으면 abort"""
        if exc_type is None:
            self.commit()
        else:
            self.abort()

    def commit(self):
        if not self._active:
            raise RuntimeError("No active transaction")
        self._backup = None
        self._active = False
        print("Transaction committed.")

    def abort(self):
        if not self._active:
            raise RuntimeError("No active transaction")
        # 원본 객체를 백업으로 되돌림
        if isinstance(self._original, dict):
            self._original.clear()
            self._original.update(self._backup)
        elif isinstance(self._original, list):
            self._original.clear()
            self._original.extend(self._backup)
        else:
            # 일반 객체 속성 복원
            for attr in vars(self._backup):
                setattr(self._original, attr, getattr(self._backup, attr))
        self._backup = None
        self._active = False
        print("Transaction aborted.")


polyline = {"vertex1": {"x": 1, "y": 2}, "vertex2": {"x": 3, "y": 4}}

try:
    with Transaction(polyline) as tr:
        # Vertex 1 수정
        polyline["vertex1"]["x"] = 5
        polyline["vertex2"]["y"] = 10
        # commit은 블록 끝에서 자동 호출됨
        raise RuntimeError("테스트용 예외")
except Exception as e:
    print("Error:", e)

print(polyline)
