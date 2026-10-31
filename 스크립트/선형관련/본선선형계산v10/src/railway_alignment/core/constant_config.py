# ============================================================
# 상수 정의
# ============================================================
import tempfile
from pathlib import Path


class Config:
    """프로그램 전역 상수"""

    # 파일 경로 (사용자 환경에 맞게 변경 가능)
    OUTPUT_DIR = Path(tempfile.gettempdir()) / "railway_alignment"
    DXF_FILENAME = "본선평면선형.dxf"
    REPORT_FILENAME = "alignmentreport.xlsx"
    CIVIL3D_FILENAME = "AlignmentExample.xlsx"
    TOTAL_COORD_FILENAME = "total_coord.txt"
    INCREMENTAL_REPORT_FILENAME = "Incremental_Station_Report"

    # 기본값
    DEFAULT_UNIT = 20
    DEFAULT_START_STA = 0.0
    DEFAULT_DESIGN_SPEED = 250
    DEFAULT_SCALE = 1000
    DEFAULT_MAX_V = 250

    # 계산 상수
    CANT_COEFFICIENT = 11.8       # 캔트 계산 계수
    M_FALLBACK_COEFFICIENT = 7.31  # M값 폴백 계수
    M_ROUNDING = 50
    V_ROUNDING = 10
    Z_ROUNDING = 10
    COORD_PRECISION = 4
    KM_PRECISION = 2
    DIMENSION_PRECISION = 3

    # 파일 저장 재시도
    SAVE_MAX_RETRIES = 100
    SAVE_RETRY_DELAY = 1

    # DXF 색상
    COLOR_RED = 1
    COLOR_WHITE = 7
    COLOR_BYLAYER = 9

    @classmethod
    def ensure_output_dir(cls) -> Path:
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        return cls.OUTPUT_DIR


# 설계속도별 M값 테이블
M_VALUE_TABLE: dict[int, float] = {
    70: 600,
    120: 900,
    150: 1100,
    200: 1450,
    250: 1850,
    300: 2200,
    350: 2550,
    400: 2950,
}
