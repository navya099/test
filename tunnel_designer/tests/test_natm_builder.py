"""NATM 빌더 1단계 테스트 — 내공/라이닝/하단."""
import sys
from pathlib import Path

from services.dxf2.document import DocumentParams

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from datetime import datetime
from core.models import TunnelParams, TunnelType
from services.dxf2 import is_standard_available, write_document, get_builder


def main():
    print("=" * 70)
    print("NATM 빌더 1단계 테스트")
    print("=" * 70)

    if not is_standard_available():
        print("❌ 도곽.dxf 없음")
        return 1

    # 샘플 파라미터 (프로그램 기본값 기준)
    params = TunnelParams(
        kind=TunnelType.NATM,
        FL=0.0,
        R1=7.166,  top_angle=90,
        R2=5.54, r2_angle=69,
        R1_Y=1.572,
        ts=0.40, ts_slab=1,
        show_lining=True,
    )
    doc_params = DocumentParams(
        design_name="OO선 OO공구",
        construction_name="OO건설",
        supervisor="OO엔지니어링",
        contractor="OO건설",
        drawing_code="NATM-001",
        scale="1:30",
    )

    builder = get_builder(TunnelType.NATM)
    out_dir = _PROJECT_ROOT / "tests" / "test_output"
    out_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = out_dir / f"NATM_step1_{ts}.dxf"

    write_document(str(out), params, doc_params, builder)
    print(f"✅ 저장: {out}")
    print(f"   파일 크기: {out.stat().st_size / 1024:.1f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())