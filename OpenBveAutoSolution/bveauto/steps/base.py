# bveauto/steps/base.py
from abc import ABC, abstractmethod

from ..context import BuildContext


class Step(ABC):
    name: str = ""
    requires_loaded: bool = True   # load_info 선행 필요 여부

    @abstractmethod
    def execute(self, ctx: BuildContext, log) -> None:
        """실제 작업. 예외는 그대로 던져도 됨 (pipeline에서 처리)."""

    def run(self, ctx: BuildContext, log) -> None:
        if self.requires_loaded and not ctx.loaded:
            raise RuntimeError(
                f"{self.name}: 기본 정보가 로드되지 않았습니다. InfoStep을 먼저 실행하세요."
            )
        self.execute(ctx, log)