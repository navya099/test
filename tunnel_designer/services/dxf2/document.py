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

    # ═══ 도면상 터널 배치 (mm, A1 도곽 기준) ═══
    base_x: float = 42000.0     # 도면 내 터널 중심 X (A1/2)
    base_y: float = 25000.0     # 도면 내 터널 중심 Y (FL)
    scale_factor: float = 1000.0  # m → mm

    # ═══ 치수 오프셋 (mm) ═══
    dim_under_offset: float = 4500.0    # 하단 수평 치수 거리
    dim_side_offset: float = 2000.0     # 우측 수직 치수 거리
    dim_top_offset: float = 3500.0      # 상단 수평 치수 거리
    dim_gap: float = 600.0              # 치수 계층 간격

    # ═══ 재료표 위치 (FL 기준, mm) ═══
    table_offset_x: float = 15000.0     # FL에서 우측으로
    table_offset_y: float = 3000.0      # FL에서 위로
    table_width: float = 3500.0
    table_row_height: float = 500.0

    # ═══ NOTE 위치 (FL 기준, mm) ═══
    note_offset_x: float = 12000.0
    note_offset_y: float = -6500.0
    note_radius: float = 400.0
    note_text: str = "1. 내공단면적은 레일 상면을 기준으로 작성하였다."

    # ═══ 심볼 (FL 기준, mm) ═══
    # (x_offset, y_offset, label)
    symbols: list[tuple[float, float, str]] = field(
        default_factory=lambda: [
            (0.0, 4200.0, "터널"),
            (-4000.0, 3600.0, "궤도"),
            (+4000.0, 3600.0, "궤도"),
        ]
    )