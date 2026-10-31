"""
CLI 진입점
===========
두 가지 모드:
  1) GUI 모드   — railway-alignment (tkinter)
  2) CLI 모드   — railway-alignment-cli (헤드리스, 파일 배치 처리)

예:
    # GUI
    railway-alignment

    # CLI: 파일 직접 지정
    railway-alignment-cli input.txt --unit 20 --speed 250 -o ./output

    # python -m 호출
    python -m railway_alignment
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from pathlib import Path

from src.railway_alignment.core.constant_config import Config
from src.railway_alignment.gui.app import AlignmentApp
from src.railway_alignment.service.alignment_service import AlignmentService, AlignmentInput

logger = logging.getLogger(__name__)


# ============================================================
# GUI 모드
# ============================================================
def main_gui() -> None:
    """tkinter GUI 실행"""
    import tkinter as tk

    root = tk.Tk()
    AlignmentApp(root)
    root.mainloop()


# ============================================================
# CLI 모드
# ============================================================
def main_cli(argv: list[str] | None = None) -> int:
    """헤드리스 CLI 실행

    Returns:
        종료 코드 (0=성공, 1=오류)
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="[%(levelname)s] %(message)s",
    )

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error("입력 파일이 존재하지 않습니다: %s", input_path)
        return 1

    try:
        raw_lines = _read_alignment_file(input_path)
        if not raw_lines:
            logger.error("파일이 비어 있거나 파싱할 수 없습니다.")
            return 1

        service = AlignmentService()
        result = service.calculate(AlignmentInput(
            raw_lines=raw_lines,
            unit=args.unit,
            start_sta=args.start_sta,
            design_speed=args.speed,
            ballast=args.ballast,
        ))

        if args.dxf:
            service.export_dxf(scale=args.scale)

        _print_summary(result)
        return 0

    except Exception as e:
        logger.exception("계산 실패: %s", e)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="railway-alignment-cli",
        description="철도 평면선형 계산 CLI",
    )
    parser.add_argument("input", help="IP 데이터 텍스트 파일 경로")
    parser.add_argument(
        "--unit", type=int, default=Config.DEFAULT_UNIT,
        help=f"측점 간격 (기본 {Config.DEFAULT_UNIT})",
    )
    parser.add_argument(
        "--start-sta", type=float, default=Config.DEFAULT_START_STA,
        help=f"시작 측점 (기본 {Config.DEFAULT_START_STA})",
    )
    parser.add_argument(
        "--speed", type=int, default=Config.DEFAULT_DESIGN_SPEED,
        help=f"설계 속도 (기본 {Config.DEFAULT_DESIGN_SPEED})",
    )
    parser.add_argument(
        "--ballast", choices=["자갈도상", "콘크리트도상"], default="자갈도상",
        help="도상 유형",
    )
    parser.add_argument(
        "--dxf", action="store_true",
        help="DXF 도면도 함께 출력",
    )
    parser.add_argument(
        "--scale", type=int, default=Config.DEFAULT_SCALE,
        help=f"DXF 축척 (기본 {Config.DEFAULT_SCALE})",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="상세 로그",
    )
    return parser


def _read_alignment_file(path: Path) -> list[list[str]]:
    """UTF-8 → EUC-KR 폴백 읽기"""
    for encoding in ("utf-8", "euc-kr"):
        try:
            with open(path, "r", encoding=encoding) as f:
                return list(csv.reader(f))
        except UnicodeDecodeError:
            logger.warning("%s 인코딩 실패, 다음 시도...", encoding)
    return []


def _print_summary(result) -> None:
    """결과 요약 출력"""
    print("\n" + "=" * 60)
    print(f"  선형 계산 완료")
    print("=" * 60)
    print(f"  IP 개수    : {len(result.curves)}")
    print(f"  측점 개수  : {sum(len(sg[0]) for sg in result.station_groups)}")
    print(f"  출력 폴더  : {Config.OUTPUT_DIR}")
    print("-" * 60)
    for label, path in [
        ("Excel 보고서", result.report_path),
        ("Civil3D", result.civil3d_path),
        ("전체 좌표", result.total_coord_path),
        ("증분 보고서", result.incremental_report_path),
        ("DXF", result.dxf_path),
    ]:
        if path:
            exists = "✓" if Path(path).exists() else "✗"
            print(f"  {exists} {label:<12}: {path}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    sys.exit(main_cli())