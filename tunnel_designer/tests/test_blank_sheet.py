"""
빈 도곽 DXF 생성 및 검증 스크립트.

실행:
    python test_blank_sheet.py

결과:
    test_output/빈도곽_YYYYMMDD_HHMMSS.dxf
    → CAD에서 열어 표준 도곽/표제란이 그대로인지 확인
"""
from __future__ import annotations
import sys
from datetime import datetime
from pathlib import Path

from services.dxf2 import get_standard_path, is_standard_available

# 프로젝트 루트를 sys.path에 추가 (services.dxf2 import를 위해)
_PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_PROJECT_ROOT))


def print_banner(title: str):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def check_standard_dxf():
    """1단계: 표준 DXF 파일 존재 확인."""
    print_banner("1단계: 표준 DXF 파일 확인")


    path = get_standard_path()
    print(f"  경로: {path}")

    if not is_standard_available():
        print(f"  ❌ 파일이 없습니다.")
        print(f"     → assets/ 폴더에 '도면표준.dxf'를 복사해주세요.")
        print(f"     → 경로: {path.parent}/")
        return False

    size_kb = path.stat().st_size / 1024
    print(f"  ✅ 파일 발견: {size_kb:.1f} KB")
    return True


def analyze_loaded_template():
    """2단계: 표준 DXF 로드 후 내용 분석."""
    print_banner("2단계: 표준 DXF 로드 및 내용 분석")

    from services.dxf2.standard_loader import load_standard_template

    doc = load_standard_template()
    msp = doc.modelspace()

    # ── 엔티티 타입별 개수 ─────────────────────────
    from collections import Counter
    entity_types = Counter(e.dxftype() for e in msp)
    print(f"\n  [ModelSpace 엔티티] 총 {sum(entity_types.values())}개")
    for t, n in sorted(entity_types.items(), key=lambda x: -x[1]):
        print(f"    {t:<12}: {n:>5}개")

    # ── 레이어 목록 ────────────────────────────────
    layers = sorted(l.dxf.name for l in doc.layers)
    print(f"\n  [레이어] 총 {len(layers)}개")
    # 주요 카테고리별 개수
    cats = {}
    for l in layers:
        prefix = l.split("-")[0] if "-" in l else "(기본)"
        cats[prefix] = cats.get(prefix, 0) + 1
    for cat, cnt in sorted(cats.items()):
        print(f"    {cat:<8}: {cnt:>3}개")

    # ── 문자 스타일 ────────────────────────────────
    styles = sorted(s.dxf.name for s in doc.styles)
    print(f"\n  [문자 스타일] 총 {len(styles)}개")
    for s in styles[:10]:
        print(f"    - {s}")
    if len(styles) > 10:
        print(f"    ... 외 {len(styles) - 10}개")

    # ── 치수 스타일 ────────────────────────────────
    dimstyles = sorted(d.dxf.name for d in doc.dimstyles)
    print(f"\n  [치수 스타일] 총 {len(dimstyles)}개")
    for d in dimstyles:
        print(f"    - {d}")

    # ── 블록 정의 ─────────────────────────────────
    blocks = sorted(b.name for b in doc.blocks)
    print(f"\n  [블록 정의] 총 {len(blocks)}개")

    # ── 표제란 ATTDEF 확인 ─────────────────────────
    attdefs = list(msp.query("ATTDEF"))
    print(f"\n  [표제란 ATTDEF] 총 {len(attdefs)}개")
    for attdef in attdefs:
        tag = attdef.dxf.get("tag", "")
        text = attdef.dxf.get("text", "")
        print(f"    {tag:<20} = '{text}'")

    # ── 모델스페이스 잔여 형상 (확인용) ───────────
    print(f"\n  [잔여 형상 확인]")
    print(f"    LINE      : {len(msp.query('LINE')):>4}개")
    print(f"    LWPOLYLINE: {len(msp.query('LWPOLYLINE')):>4}개")
    print(f"    ARC       : {len(msp.query('ARC')):>4}개")
    print(f"    HATCH     : {len(msp.query('HATCH')):>4}개")
    print(f"    INSERT    : {len(msp.query('INSERT')):>4}개")
    print(f"    DIMENSION : {len(msp.query('DIMENSION')):>4}개")

    return doc


def generate_blank_sheet(doc, output_dir: Path):
    """3단계: 표제란만 채워서 빈 도곽 DXF 저장."""
    print_banner("3단계: 빈 도곽 DXF 생성")

    from services.dxf2.title_block import (
        build_title_values, fill_title_block,
    )

    # 표제란 값 설정 (테스트용)
    test_values = build_title_values(
        tunnel_type_label="NATM 표준단면 (테스트)",
        kind_label="터널 단면도",
        scale="1:100",
        design_name="OO선 OO공구 노반 실시설계",
        construction_name="OO선 OO공구 노반 시공",
        supervisor="OO엔지니어링",
        contractor="OO건설",
        drawing_code="TEST-NATM-001",
        location="본선",
        direction="오기(현) 000km000.00~000km000.00",
    )
    filled = fill_title_block(doc, test_values)
    print(f"\n  표제란 필드 채움: {filled}개")

    # 저장
    output_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = output_dir / f"빈도곽_{ts}.dxf"
    doc.saveas(str(out_path))

    size_kb = out_path.stat().st_size / 1024
    print(f"\n  ✅ 저장 완료: {out_path}")
    print(f"     파일 크기: {size_kb:.1f} KB")

    return out_path


def verify_saved_file(out_path: Path):
    """4단계: 저장된 파일 재로드 검증."""
    print_banner("4단계: 저장된 파일 재로드 검증")

    import ezdxf
    doc = ezdxf.readfile(str(out_path))
    msp = doc.modelspace()

    # 1) 표제란 값 확인
    print("\n  [표제란 값 확인]")
    expected = {
        "TB_MTITIL": "터널 단면도",
        "TB_STITL": "NATM 표준단면 (테스트)",
        "SCALE": "1:100",
        "TD_DWGCODE": "TEST-NATM-001",
    }
    ok = True
    for attdef in msp.query("ATTDEF"):
        tag = attdef.dxf.get("tag", "")
        text = attdef.dxf.get("text", "")
        if tag in expected:
            match = text == expected[tag]
            mark = "✅" if match else "❌"
            print(f"    {mark} {tag:<15} = '{text}'")
            if not match:
                print(f"         (기대값: '{expected[tag]}')")
                ok = False

    # 2) 도곽 폴리라인 확인 (CX-BORD 레이어)
    print("\n  [도곽 확인 (CX-BORD 레이어)]")
    cx_bord_lines = [
        e for e in msp
        if e.dxf.get("layer", "") == "CX-BORD"
    ]
    print(f"    CX-BORD 엔티티: {len(cx_bord_lines)}개")

    # 3) 도각 크기 확인 ($EXTMAX)
    print("\n  [도면 크기]")
    header = doc.header
    extmin = header.get("$EXTMIN", (0, 0, 0))
    extmax = header.get("$EXTMAX", (0, 0, 0))
    print(f"    EXTMIN: ({extmin[0]:.0f}, {extmin[1]:.0f})")
    print(f"    EXTMAX: ({extmax[0]:.0f}, {extmax[1]:.0f})")

    # 4) 레이어 유지 확인
    print("\n  [표준 레이어 유지 확인]")
    required_layers = [
        "CX-BORD", "CZ-CNTL", "CZ-DIMS", "CZ-TEXT",
        "CS-CONC-MAJR", "CR-TUNL", "CF-RAIL",
    ]
    for lname in required_layers:
        try:
            doc.layers.get(lname)
            print(f"    ✅ {lname}")
        except Exception:
            print(f"    ❌ {lname} (누락)")
            ok = False

    # 5) 문자 스타일 유지 확인
    print("\n  [표준 문자 스타일 유지 확인]")
    required_styles = ["T20", "T25", "T35", "T50", "T70", "T100"]
    for sname in required_styles:
        try:
            doc.styles.get(sname)
            print(f"    ✅ {sname}")
        except Exception:
            print(f"    ❌ {sname} (누락)")
            ok = False

    # 6) 치수 스타일 유지 확인
    print("\n  [표준 치수 스타일 유지 확인]")
    try:
        ds = doc.dimstyles.get("구조도면_0100")
        print(f"    ✅ 구조도면_0100 "
              f"(dimscl={ds.dxf.dimscale}, dimtxt={ds.dxf.dimtxt})")
    except Exception:
        print(f"    ❌ 구조도면_0100 (누락)")
        ok = False

    return ok


def print_manual_check_guide(out_path: Path):
    """5단계: CAD에서 수동 검증 안내."""
    print_banner("5단계: CAD 수동 검증 가이드")

    print(f"""
  파일: {out_path}

  다음 항목을 CAD에서 확인하세요:

  ┌─ 도곽 ─────────────────────────────────────────┐
  │ ☐ A1 도곽 외곽선이 있는가? (84m × 59.4m)       │
  │ ☐ 내부 여백선이 있는가?                         │
  │ ☐ 표제란이 우측 하단에 있는가?                  │
  └────────────────────────────────────────────────┘

  ┌─ 표제란 ───────────────────────────────────────┐
  │ ☐ "터널 단면도" (주타이틀, 큰 글씨)             │
  │ ☐ "NATM 표준단면 (테스트)" (부타이틀)           │
  │ ☐ "OO선 OO공구 노반 실시설계"                   │
  │ ☐ "OO엔지니어링" "OO건설" 등                    │
  │ ☐ "1:100", "TEST-NATM-001"                      │
  └────────────────────────────────────────────────┘

  ┌─ 레이어 ──────────────────────────────────────┐
  │ ☐ CX-BORD, CZ-CNTL, CZ-DIMS 등                 │
  │ ☐ CS-CONC-MAJR, CR-TUNL, CF-RAIL 등             │
  └────────────────────────────────────────────────┘

  ┌─ 문자 스타일 ─────────────────────────────────┐
  │ ☐ T20, T25, T35, T50, T70, T100 스타일이 존재  │
  │ ☐ 굴림체(GulimChe)로 표시됨                    │
  └────────────────────────────────────────────────┘

  ┌─ 치수 스타일 ─────────────────────────────────┐
  │ ☐ "구조도면_0100" 스타일이 존재                │
  │ ☐ 화살표 색상: 빨강, 문자 색상: 초록            │
  └────────────────────────────────────────────────┘

  ⚠️ 주의: 표준 도곽/표제란의 예시 형상(터널단면 등)은
     삭제됩니다. 도각 틀과 표제란 필드만 남습니다.
""")


# ═══════════════════════════════════════════════════════════
# 메인
# ═══════════════════════════════════════════════════════════
def main():
    print("\n" + "█" * 70)
    print("  빈 도곽 DXF 생성 및 검증")
    print("█" * 70)

    # 1단계: 파일 존재
    if not check_standard_dxf():
        return 1

    # 2단계: 로드 및 분석
    try:
        doc = analyze_loaded_template()
    except Exception as e:
        print(f"\n  ❌ 로드 실패: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # 3단계: 빈 도곽 DXF 생성
    output_dir = _PROJECT_ROOT / "test_output"
    try:
        out_path = generate_blank_sheet(doc, output_dir)
    except Exception as e:
        print(f"\n  ❌ 저장 실패: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # 4단계: 재로드 검증
    try:
        ok = verify_saved_file(out_path)
    except Exception as e:
        print(f"\n  ❌ 검증 실패: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # 5단계: 수동 검증 안내
    print_manual_check_guide(out_path)

    # 최종 요약
    print_banner("최종 결과")
    if ok:
        print("  ✅ 자동 검증 통과!")
        print(f"  📁 {out_path}")
        print(f"\n  다음 단계: CAD에서 위 체크리스트를 수동 검증하세요.")
        return 0
    else:
        print("  ⚠️ 일부 항목 실패 — 위 ❌ 목록을 확인하세요.")
        return 1


if __name__ == "__main__":
    sys.exit(main())