"""표준 DXF의 표제란 ATTDEF → TEXT 변환."""
from __future__ import annotations
from datetime import datetime

import ezdxf
from ezdxf.document import Drawing
from ezdxf.enums import TextEntityAlignment


def build_title_values(
    tunnel_type_label: str,
    kind_label: str = "터널 단면도",
    scale: str = "1:100",
    design_name: str = "",
    construction_name: str = "",
    supervisor: str = "",
    contractor: str = "",
    drawer: str = "",
    reviewer: str = "",
    confirmer: str = "",
    location: str = "",
    direction: str = "",
    drawing_code: str = "",
) -> dict:
    """표준 ATTDEF tag → 값 매핑 (기존과 동일)."""
    today = datetime.now().strftime("%Y-%m-%d")
    return {
        "TB_MTITIL": kind_label,
        "TB_STITL": tunnel_type_label,
        "TD_DNAME_TOP": location or "본선",
        "TD_DNAME_MAIN": kind_label,
        "TD_DNAME_BOT": direction or "오기(현) 000km000.00~000km000.00",
        "TD_DNAME": design_name or "터널 설계",
        "TD_CNAME": construction_name or "터널 시공",
        "TD_CSCOMP": supervisor or "",
        "TD_CCOMP": contractor or "",
        "TD_DWGCODE": drawing_code or "TUN-001",
        "SCALE": scale,
        "TR_RDAT1": today,
    }


def fill_title_block(doc: Drawing, values: dict):
    """
    ★ ATTDEF를 TEXT로 변환하여 실제 표시.
    1. ModelSpace의 ATTDEF를 찾음
    2. 값 매칭 후 ATTDEF 삭제 + TEXT 엔티티 생성
    3. BLOCK 안에 ATTDEF가 있으면 그건 그대로 (나중에 INSERT 시 표시)
    """
    msp = doc.modelspace()
    converted = 0

    attdefs_to_convert = []
    for attdef in msp.query("ATTDEF"):
        tag = attdef.dxf.get("tag", "")
        if tag in values:
            attdefs_to_convert.append((attdef, values[tag]))

    for attdef, new_value in attdefs_to_convert:
        # ATTDEF의 위치, 높이, 스타일, 회전, 정렬 정보 복사
        insert = attdef.dxf.insert
        height = attdef.dxf.get("height", 250.0)
        style = attdef.dxf.get("style", "Standard")
        rotation = attdef.dxf.get("rotation", 0.0)
        layer = attdef.dxf.get("layer", "CX-BORD")
        color = attdef.dxf.get("color", 256)

        # 정렬 위치 (있으면 사용)
        align_pt = attdef.dxf.get("align_point", None)
        halign = attdef.dxf.get("halign", 0)
        valign = attdef.dxf.get("valign", 0)

        # ATTDEF 삭제
        msp.delete_entity(attdef)

        # TEXT 엔티티 생성 (값 표시)
        if new_value:  # 빈 문자열이면 표시 안 함
            txt = msp.add_text(
                new_value,
                dxfattribs={
                    "height": height,
                    "style": style,
                    "layer": layer,
                    "rotation": rotation,
                    "color": color,
                },
            )
            # 정렬 설정
            if align_pt is not None:
                from ezdxf.enums import TextEntityAlignment
                align_map = {
                    (0, 0): TextEntityAlignment.LEFT,
                    (1, 0): TextEntityAlignment.CENTER,
                    (2, 0): TextEntityAlignment.RIGHT,
                    (0, 1): TextEntityAlignment.BOTTOM_LEFT,
                    (1, 1): TextEntityAlignment.BOTTOM_CENTER,
                    (2, 1): TextEntityAlignment.BOTTOM_RIGHT,
                    (0, 2): TextEntityAlignment.TOP_LEFT,
                    (1, 2): TextEntityAlignment.TOP_CENTER,
                    (2, 2): TextEntityAlignment.TOP_RIGHT,
                    (0, 3): TextEntityAlignment.MIDDLE_LEFT,
                    (1, 3): TextEntityAlignment.MIDDLE_CENTER,
                    (2, 3): TextEntityAlignment.MIDDLE_RIGHT,
                }
                alignment = align_map.get((halign, valign), TextEntityAlignment.LEFT)
                txt.set_placement(align_pt, align=alignment)
            else:
                txt.set_placement(insert)
        converted += 1

    return converted