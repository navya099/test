import copy

class Transaction:
    def __init__(self, *objs):
        """
        objs: 트랜잭션을 적용할 여러 객체 (PoleDATA, EditablePole 등)
        """
        self._originals = objs
        self._backups = []
        self._active = False

    def __enter__(self):
        if self._active:
            raise RuntimeError("Transaction already started")
        # 모든 객체 백업
        self._backups = [copy.deepcopy(obj) for obj in self._originals]
        self._active = True
        print("Transaction started.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.abort()

    def commit(self):
        if not self._active:
            raise RuntimeError("No active transaction")
        self._backups = []
        self._active = False
        print("Transaction committed.")

    def abort(self):
        if not self._active:
            raise RuntimeError("No active transaction")
        # 모든 객체를 백업 상태로 복원
        for original, backup in zip(self._originals, self._backups):
            if isinstance(original, dict):
                original.clear()
                original.update(backup)
            elif isinstance(original, list):
                original.clear()
                original.extend(backup)
            else:
                for attr in vars(backup):
                    setattr(original, attr, getattr(backup, attr))
        self._backups = []
        self._active = False
        print("Transaction aborted.")