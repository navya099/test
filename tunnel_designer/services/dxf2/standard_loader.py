"""표준 DXF 로드 → 도곽/스타일/블록 유지, 형상만 삭제."""
from __future__ import annotations
from pathlib import Path

import ezdxf
from ezdxf.document import Drawing


# 표준 DXF 위치 (프로젝트 루트 기준)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STANDARD_DXF = _PROJECT_ROOT / "assets" / "도곽.dxf"


# ═══════════════════════════════════════════════════════════
# 유지할 레이어 (도곽/표제란 관련)
# ═══════════════════════════════════════════════════════════
KEEP_LAYERS = {
    "CX-BORD", "CX-PAPR", "CX-MISC",
    "0", "Defpoints",
}

# ═══════════════════════════════════════════════════════════
# 삭제할 레이어 (표준 예시 형상들)
# ═══════════════════════════════════════════════════════════
DELETE_LAYERS = {
    # 터널/지반 예시
    "CR-TUNL", "CR-TUNL-NEWC", "CR-BRDG", "CR-BRDG-NEWC",
    "CR-GRND", "CR-BORE",
    "CC-GRND", "CC-ROCK-SOFT", "CC-ROCK-HARD", "CC-ROCK-WETH",
    # 구조 예시
    "CS-CONC-MAJR", "CS-CONC-MINR", "CS-CONC-REFR",
    "CS-RBAR", "CS-RBAR-MAJR", "CS-RBAR-MINR", "CS-RBAR-EREC",
    "CS-STEL", "CS-STEL-MAJR", "CS-STEL-MINR",
    "CS-SCRT", "CS-PIPE", "CS-NOTE", "CS-LEAL", "CS-LEAT",
    "CS-TABL-LIN1", "CS-TABL-LIN2",
    "CS-TABL-TEX1", "CS-TABL-TEX2", "CS-TEXT",
    "CS-XXXX",
    # 공통 예시
    "CZ-BASE", "CZ-CUTL", "CZ-TEXT", "CZ-SYMB",
    "CZ-TEX0", "CZ-TEX1", "CZ-TEX2", "CZ-TEX3",
    "CZ-DIMS", "CZ-CNTL", "CZ-HIDL", "CZ-LIN1", "CZ-MACL",
    "CZ-PATT",
    # 시설 예시
    "CF-RAIL", "CF-VENT",
    "CE-SLOP-NATR",
    # 기타
    "T100", "T70", "T50", "T35", "T25", "T20",
    "CEN", "CONC", "CONC1", "REBAR1", "REBAR2", "REBAR3",
    "REBARD", "REBARD1", "DIM", "DIM1", "SYM", "SYM1",
    "_BAR_MARK_TXT", "_BAR_MARK_LNE", "BAR_TICK",
    "A_2", "A_6",
    "CS-DIML", "CS-DIMT", "CS-CNTL",
    "CS-MISC", "CS-SYMB", "CS-SYMB-LIN3",
    "CX-BORD" if False else "",  # (CX-BORD는 유지)
}

# 빈 문자열은 실수 방지용 제거
DELETE_LAYERS.discard("")


# ═══════════════════════════════════════════════════════════
# 유지할 블록 (표제란/도곽/심볼)
# ═══════════════════════════════════════════════════════════
KEEP_BLOCKS = {
    "*Model_Space", "*Paper_Space",
    # 표준 심볼 블록 (필요 시 재사용)
    "CZASCNT",      # 중심선
    "CZELWA1",      # 수위표고
    "CZELWA3",      # 수위 3
    "CZELWA3-DESL", # 수위 상세
    "CZHEGRD",      # 지반 표시
    "CZHPGRV",      # 자갈/호박돌
    "CZHPRCN",      # 철근콘크리트
    "CZDIRF1",      # 유수방향
    "CZSECM4",      # 단면기호
    "CZSIDE2",      # 좌우측
    "CSBNUM1",      # 철근번호
    "CSHBEMC",      # H형강 실선
    "CSHBEMH",      # H형강 파선
    "CRBRDGN",      # 교량
    "CESLOPE",      # 자연사면
    "BAR_MARK_BLOCK", "BAR_TICK", "B_DOT",
    "_Dot", "_Dot1", "방위",
    # 치수 스타일 블록
    "*D17", "*D18", "*D19", "*D20",
}


def load_standard_template(scale_multiplier: float = 1.0) -> Drawing:
    """
    표준 DXF 로드 + 형상 삭제 + 도곽/표제란/스타일 유지.
    반환된 Drawing은 우리 도면의 기반이 됨.
    """
    if not STANDARD_DXF.exists():
        raise FileNotFoundError(
            f"표준 DXF 파일이 없습니다: {STANDARD_DXF}\n"
            f"assets/ 폴더에 '도면표준.dxf'를 복사해주세요.")

    doc = ezdxf.readfile(str(STANDARD_DXF))
    msp = doc.modelspace()

    # ── 1) ModelSpace의 형상 엔티티 삭제 ─────────────
    to_delete = []
    for e in msp:
        layer = e.dxf.get("layer", "")
        if layer in DELETE_LAYERS:
            to_delete.append(e)
    for e in to_delete:
        try:
            msp.delete_entity(e)
        except Exception:
            pass

    # ── 2) ModelSpace의 ATTDEF/INSERT 중 예시들 삭제 ──
    # 표제란의 ATTDEF는 유지, 예시 INSERT는 삭제
    keep_insert_blocks = {"CZSIDE2", "CZSECM4", "CZASCNT", "CZHEGRD",
                          "CZHPRCN", "CZHPGRV", "CZELWA1", "CZELWA3",
                          "CZELWA3-DESL", "CZDIRF1"}
    for e in msp.query("INSERT"):
        block_name = e.dxf.get("name", "")
        if block_name not in keep_insert_blocks and block_name in KEEP_BLOCKS:
            # 표준 심볼 예시 삽입은 제거 (필요시 사용자가 다시 삽입)
            layer = e.dxf.get("layer", "")
            if layer in DELETE_LAYERS or layer == "CZ-SYMB":
                try:
                    msp.delete_entity(e)
                except Exception:
                    pass

    # ── 3) 유지하지 않을 블록 정의 삭제 ─────────────
    block_layouts = list(doc.blocks)
    for block in block_layouts:
        name = block.name
        # 치수 스타일 블록, 표준 블록은 유지
        if name.startswith("*D") or name.startswith("*Model") or name.startswith("*Paper"):
            continue
        if name not in KEEP_BLOCKS:
            try:
                doc.blocks.delete_block(name, safe=False)
            except Exception:
                pass

    # ── 4) 표제란 관련 레이어 활성화 확인 ────────────
    for layer_name in KEEP_LAYERS:
        if layer_name not in doc.layers:
            continue

    # ── 2) 도곽/표제란 배율 확대 ───────────────
    if scale_multiplier != 1.0:
        from ezdxf.math import Matrix44
        scale_mat = Matrix44.scale(scale_multiplier)

        for entity in list(msp):
            try:
                entity.transform(scale_mat)
            except Exception:
                pass

        # LTSCALE 조정
        doc.header["$LTSCALE"] = (
                doc.header.get("$LTSCALE", 1.0) * scale_multiplier
        )

        # EXTMAX 확대
        old_extmax = doc.header.get("$EXTMAX", (841, 594, 0))
        doc.header["$EXTMAX"] = (
            old_extmax[0] * scale_multiplier,
            old_extmax[1] * scale_multiplier,
            0.0,
        )

    return doc


def is_standard_available() -> bool:
    """표준 DXF 파일 존재 여부."""
    return STANDARD_DXF.exists()


def get_standard_path() -> Path:
    return STANDARD_DXF