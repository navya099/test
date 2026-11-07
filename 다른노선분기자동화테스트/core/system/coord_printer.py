# core/system_impl/coord_printer.py
import logging
from typing import Dict, Any

from core.constants import ComponentKey
from core.system.system import System

logger = logging.getLogger(__name__)


class CoordPrinter(System):
    """확정된 최종 제원의 계산을 바탕으로 좌표를 출력한다."""

    # 입력 데이터만 필요하고, 출력 데이터는 생성하지 않음
    requires_components = frozenset({ComponentKey.BRANCH_COORDS})
    produces_components = frozenset()  # 빈 집합으로 설정

    def execute(self, entities: Dict[str, Any], components: Dict[str, Any]) -> None:
        # ★ 수정: components 딕셔너리에서 실제 데이터를 꺼내야 함
        coords_data = components[ComponentKey.BRANCH_COORDS]

        print(f"\n--- 분기 경로 좌표 (상위 5개) ---")
        for i, p in enumerate(coords_data["points"][:5]):
            print(f"P{i}: X={p[0]:.3f}, Y={p[1]:.3f}")

        print(f"... (총 {len(coords_data['points'])}개)")
        print(f"시작점: {coords_data['start_point']}")
        print(f"끝점: {coords_data['end_point']}")

        logger.info("분기 경로 좌표 출력이 완료되었습니다.")