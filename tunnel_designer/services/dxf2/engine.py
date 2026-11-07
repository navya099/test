"""표준 DXF 기반 도면 작성 공통 엔진."""
from __future__ import annotations

from ezdxf.document import Drawing

from core.models import TunnelParams
from services.dxf2.document import DocumentParams
from services.dxf2.standard_loader import load_standard_template
from services.dxf2.title_block import (
    build_title_values, fill_title_block,
)
from services.dxf2.layers import (
    DIMSTYLE_1_100, STYLE_T25, HEIGHT_T25,
    LAYER_DIM, LAYER_TEXT,
)


# ═══════════════════════════════════════════════════════════
# 도면 생성 오케스트레이션
# ═══════════════════════════════════════════════════════════
def write_document(
    path: str,
    params: TunnelParams,
    doc_params: DocumentParams | None = None,  # ★ 신규
    builder_fn=None,
    *,
    title_overrides: dict | None = None,
):
    """
    1. 표준 DXF 템플릿 로드 (도곽/표제란/스타일/블록 그대로)
    2. 표제란 자동 채움 (타입에 맞춰)
    3. 타입별 빌더 호출 (형상 + 치수 + 문자)
    4. 저장

    Parameters
    ----------
    path           : 저장 경로
    params         : TunnelParams (터널 제원)
    doc_params     : 문서 파라메터
    builder_fn     : (msp, params, doc) -> None
    title_overrides: 사용자가 수정한 표제란 값 (선택)
    """
    # 1) 표준 템플릿
    if doc_params is None:
        doc_params = DocumentParams()

    # ★ 도곽 배율 적용 로드
    doc = load_standard_template(
        scale_multiplier=doc_params.scale_multiplier,
    )

    # 2) 표제란
    title_values = build_title_values(
        tunnel_type_label=_type_label(params),
        kind_label="터널 단면도",
        scale=doc_params.scale,
        design_name=doc_params.design_name,
        construction_name=doc_params.construction_name,
        supervisor=doc_params.supervisor,
        contractor=doc_params.contractor,
        location=doc_params.location,
        direction=doc_params.direction,
        drawing_code=doc_params.drawing_code,
    )
    if title_overrides:
        title_values.update(title_overrides)
    fill_title_block(doc, title_values)

    # 3) 타입별 빌더
    msp = doc.modelspace()
    builder_fn(msp, params, doc_params, doc)

    # 4) 저장
    doc.saveas(path)
    return doc

def _type_label(params: TunnelParams) -> str:
    """터널 타입 → 부타이틀 문자열."""
    try:
        kind = params.kind.value if hasattr(params.kind, "value") else str(params.kind)
    except Exception:
        kind = "터널"
    return f"{kind} 표준단면"


# ═══════════════════════════════════════════════════════════
# 치수 헬퍼 (표준 DIMENSION 엔티티)
# ═══════════════════════════════════════════════════════════
# services/dxf2/engine.py

def dim_horizontal(
    msp,
    x1: float, x2: float, y: float,
    *,
    offset: float = 1500.0,
    override_text: str | None = None,
    dimstyle: str = DIMSTYLE_1_100,
):
    """
    수평 치수 (DIMENSION 엔티티).
    ★ add_linear_dim()은 DimStyleOverride 반환 → .set_text()로 텍스트 오버라이드.
    """
    dim_override = msp.add_linear_dim(
        base=(x1, y + offset),
        p1=(x1, y),
        p2=(x2, y),
        dimstyle=dimstyle,
    )
    if override_text:
        dim_override.set_text(override_text)   # ★ .dxf 대신 .set_text()
    dim_override.render()
    return dim_override.dimension               # 실제 DIMENSION 엔티티 반환


def dim_vertical(
    msp,
    y1: float, y2: float, x: float,
    *,
    offset: float = 1500.0,
    override_text: str | None = None,
    dimstyle: str = DIMSTYLE_1_100,
):
    """수직 치수 (DIMENSION 엔티티)."""
    dim_override = msp.add_linear_dim(
        base=(x + offset, y1),
        p1=(x, y1),
        p2=(x, y2),
        angle=90,
        dimstyle=dimstyle,
    )
    if override_text:
        dim_override.set_text(override_text)
    dim_override.render()
    return dim_override.dimension


# ═══════════════════════════════════════════════════════════
# 문자 헬퍼
# ═══════════════════════════════════════════════════════════
def text_std(
    msp,
    x: float, y: float, s: str,
    *,
    style: str = STYLE_T25,
    height: float = HEIGHT_T25,
    layer: str = LAYER_TEXT,
    rotation: float = 0.0,
    align: str | None = None,
):
    """표준 문자 (GulimChe + 크기)."""
    t = msp.add_text(
        s,
        dxfattribs={
            "height": height,
            "style": style,
            "layer": layer,
            "rotation": rotation,
        },
    )
    if align:
        t.set_placement((x, y), align=align)
    else:
        t.set_placement((x, y))
    return t