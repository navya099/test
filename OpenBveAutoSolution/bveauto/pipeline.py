# bveauto/pipeline.py
from typing import Callable

from .context import BuildContext
from .steps.base import Step


class Pipeline:
    def __init__(self, steps: list[Step], log: Callable[[str], None]):
        self.steps = steps
        self.log = log

    def run(self, ctx: BuildContext) -> None:
        """전체 실행. 예외 발생 시 즉시 중단."""
        for step in self.steps:
            step.run(ctx, self.log)
        self.log("전체 작업 완료")

    def run_until(self, ctx: BuildContext, name: str) -> None:
        """name 단계까지 실행 (GUI 버튼용)."""
        for step in self.steps:
            step.run(ctx, self.log)
            if step.name == name:
                return
        raise ValueError(f"알 수 없는 단계: {name}")

    def run_single(self, ctx: BuildContext, name: str) -> None:
        """특정 단계 하나만 실행."""
        for step in self.steps:
            if step.name == name:
                step.run(ctx, self.log)
                return
        raise ValueError(f"알 수 없는 단계: {name}")

    def names(self) -> list[str]:
        return [s.name for s in self.steps]