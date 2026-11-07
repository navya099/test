# core/system_impl/result_summary.py
import math
import logging
from typing import Dict, Any

from core.constants import ComponentKey
from core.system.system import System

logger = logging.getLogger(__name__)


class ResultSummarySystem(System):
    """최종 확정된 설계 제원(Spec)을 요약하여 출력합니다."""
    requires_components = frozenset({ComponentKey.TURNOUT_SPEC})
    produces_components = frozenset()  # 출력만 하고 데이터 변경 없음

    def execute(self, entities: Dict[str, Any], components: Dict[str, Any]) -> None:
        spec = components[ComponentKey.TURNOUT_SPEC]

        result_msg = (
            f"\n=== 건넘선 설계 최종 결과 ===\n"
            f"곡선장(cl) : {spec.start_length:.1f} m\n"
            f"직선장(sl) : {spec.middle_length:.1f} m\n"
            f"반지름(R)  : {spec.radius:.2f} m\n"
            f"접선각(θ)  : {math.degrees(spec.cross_angle):.3f}°\n"
            f"==============================="
        )

        print(result_msg)
        logger.info("설계 결과 요약 출력 완료.")