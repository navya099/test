"""표준 DXF 레이어/문자 스타일/치수 스타일 상수."""
from __future__ import annotations


# ═══════════════════════════════════════════════════════════
# 표준 레이어 (사내 규격)
# ═══════════════════════════════════════════════════════════
# CZ-: 공통 일반
LAYER_CENTERLINE   = "CZ-CNTL"        # 중심선
LAYER_DIM          = "CZ-DIMS"        # 치수
LAYER_TEXT         = "CZ-TEXT"        # 일반 문자
LAYER_TEXT_TITLE   = "CZ-TEX1"        # 제목 문자
LAYER_TEXT_SUB     = "CZ-TEX2"        # 부제목
LAYER_TEXT_SMALL   = "CZ-TEX3"        # 작은 문자
LAYER_SYMB         = "CZ-SYMB"        # 심볼(블록)
LAYER_HIDDEN       = "CZ-HIDL"        # 숨은선
LAYER_CUT          = "CZ-CUTL"        # 절단선
LAYER_HATCH        = "CZ-PATT"        # 해치 패턴
LAYER_LINE         = "CZ-LIN1"        # 일반선

# CR-: 노선/터널
LAYER_TUNNEL       = "CR-TUNL"        # 터널 내공
LAYER_TUNNEL_NEW   = "CR-TUNL-NEWC"   # 신규 터널(강조)
LAYER_GROUND       = "CR-GRND"        # 지반선
LAYER_BORE         = "CR-BORE"        # 보링
LAYER_BRIDGE       = "CR-BRDG"        # 교량
LAYER_TEXT_ROUTE   = "CR-TEXT"        # 노선 문자

# CS-: 공통 구조
LAYER_CONCRETE     = "CS-CONC-MAJR"   # 콘크리트(실선)
LAYER_CONC_HIDDEN  = "CS-CONC-MINR"   # 콘크리트(숨은선)
LAYER_CONC_REF     = "CS-CONC-REFR"   # 콘크리트 참조
LAYER_REBAR        = "CS-RBAR"        # 철근
LAYER_REBAR_MAJOR  = "CS-RBAR-MAJR"   # 철근 실선
LAYER_REBAR_MINOR  = "CS-RBAR-MINR"   # 철근 점선
LAYER_STEEL        = "CS-STEL"        # 강재
LAYER_STEEL_MAJOR  = "CS-STEL-MAJR"   # 강재 실선
LAYER_STEEL_MINOR  = "CS-STEL-MINR"   # 강재 점선
LAYER_SHOTCRETE    = "CS-SCRT"        # 숏크리트
LAYER_PIPE         = "CS-PIPE"        # 파이프
LAYER_TABLE_LINE   = "CS-TABL-LIN1"   # 테이블 외곽
LAYER_TABLE_INNER  = "CS-TABL-LIN2"   # 테이블 내부
LAYER_NOTE         = "CS-NOTE"        # 노트
LAYER_LEADER_LINE  = "CS-LEAL"        # 인출선
LAYER_LEADER_TEXT  = "CS-LEAT"        # 인출문자

# CX-: 도각/기타
LAYER_BORDER       = "CX-BORD"        # 도각(표제란)
LAYER_PAPER        = "CX-PAPR"        # 여백/뷰포트
LAYER_MISC         = "CX-MISC"        # 기타(방위표 등)

# CF-: 궤도/시설
LAYER_RAIL         = "CF-RAIL"        # 철도(궤도)
LAYER_VENT         = "CF-VENT"        # 환기구

# CC-: 지반
LAYER_GND_GENERAL  = "CC-GRND"        # 지반선
LAYER_ROCK_SOFT    = "CC-ROCK-SOFT"   # 연암
LAYER_ROCK_HARD    = "CC-ROCK-HARD"   # 경암
LAYER_ROCK_WEATH   = "CC-ROCK-WETH"   # 풍화암

LAYER_SAFE = LAYER_MISC     # ★ 안전박스는 일반선 레이어로
LAYER_HIDL = LAYER_HIDDEN   # 이미 있음

# ═══════════════════════════════════════════════════════════
# 표준 문자 스타일 (GulimChe, 크기 계층)
# ═══════════════════════════════════════════════════════════
STYLE_T100 = "T100"   # 대제목 h=10
STYLE_T70  = "T70"    # 부제목 h=7
STYLE_T50  = "T50"    # 소제목 h=5
STYLE_T35  = "T35"    # 보조제목 h=3.5
STYLE_T25  = "T25"    # 일반문자 h=2.5
STYLE_T20  = "T20"    # 작은문자 h=2
STYLE_STD  = "Standard"


# 문자 높이 (mm) — 스타일과 함께 사용
HEIGHT_T100 = 1000.0
HEIGHT_T70  = 700.0
HEIGHT_T50  = 500.0
HEIGHT_T35  = 350.0
HEIGHT_T25  = 250.0
HEIGHT_T20  = 200.0


# ═══════════════════════════════════════════════════════════
# 표준 치수 스타일
# ═══════════════════════════════════════════════════════════
DIMSTYLE_1_100 = "구조도면_0100"   # 1:100 스케일 (dimscl=1000, dimtxt=250)
DIMSTYLE_1_1   = "DIM-1"          # 1:1 스케일 (dimscl=1, dimtxt=3)
DIMSTYLE_STD   = "Standard"


# ═══════════════════════════════════════════════════════════
# 표준 해치 패턴
# ═══════════════════════════════════════════════════════════
HATCH_CONCRETE   = "N-CONCR01"   # 철근콘크리트
HATCH_PLAIN      = "N-CONCP01"   # 무근콘크리트
HATCH_SAND       = "N-SANDS01"   # 모래
HATCH_GRAVEL     = "N-GRAVLD03"  # 자갈


# ═══════════════════════════════════════════════════════════
# 도각 크기 (A1 x 2배, 표준 DXF 기준)
# ═══════════════════════════════════════════════════════════
SHEET_W = 84000.0
SHEET_H = 59400.0
SHEET_MARGIN = 2000.0


# ═══════════════════════════════════════════════════════════
# 단위 변환 (엔진은 m, DXF는 mm)
# ═══════════════════════════════════════════════════════════
MM = 1000.0    # 1 m = 1000 mm


def m_to_mm(v: float) -> float:
    return v * MM


def mm_to_m(v: float) -> float:
    return v / MM