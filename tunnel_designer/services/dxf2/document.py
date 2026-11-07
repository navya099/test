# core/models.py 파일 맨 아래에 추가
from dataclasses import dataclass, field


@dataclass
class DocumentParams:
    """
    도면 작성에 필요한 레이아웃 파라미터.
    TunnelParams(터널 기하)와는 독립적.
    """
    # ═══ 도곽 / 표제란 ═══
    design_name: str = "터널 설계"
    construction_name: str = "터널 시공"
    supervisor: str = ""
    contractor: str = ""
    location: str = "본선"
    direction: str = "오기(현) 000km000.00~000km000.00"
    drawing_code: str = "TUN-001"
    scale: str = "1:100"

    # ═══ 도곽 확대 배율 (터널 좌표에 영향 없음) ═══
    @property
    def scale_multiplier(self) -> float:
        """
        ★ 도곽만 확대하는 배율.
        - "1:100" → ×100 (841 → 84,100mm)
        - "1:50"  → ×50  (841 → 42,050mm)
        - "1:200" → ×200 (841 → 168,200mm)
        - "1:1"   → ×1   (841mm 그대로)
        """
        try:
            _, num = self.scale.split(":")
            return float(num)
        except (ValueError, AttributeError):
            return 100.0

    # ═══ 도곽 배치 원점 (확대 후 중앙) ═══
    @property
    def base_x(self) -> float:
        """확대된 도곽의 X 중심."""
        return 841.0 * self.scale_multiplier / 2.0

    @property
    def base_y(self) -> float:
        """확대된 도곽의 Y 중심."""
        return 594.0 * self.scale_multiplier / 2.0

    # ═══ 치수 스타일 ═══
    @property
    def dimstyle(self) -> str:
        """도곽_A1.dxf의 치수 스타일."""
        return "구조도면_0100"