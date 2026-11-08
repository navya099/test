# bveauto/decorators.py
import functools
import time


def log_errors(name: str, reraise: bool = False):
    """try/except + 로그 패턴을 데코레이터로 추출.

    reraise=True 면 파이프라인이 중단되도록 예외를 다시 던진다.
    """
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(self, ctx, log):
            log(f"{'-' * 5} {name} 시작 {'-' * 5}")
            start = time.time()
            try:
                result = fn(self, ctx, log)
                elapsed = time.time() - start
                log(f"{name} 완료 ({elapsed:.2f}s)")
                return result
            except Exception as e:
                log(f"[{name}] 오류: {e}")
                if reraise:
                    raise
        return wrapper
    return deco