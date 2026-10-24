# local/localentry.py
"""
로컬 파이프라인.

- compute: 순수 계산 (웹/로컬 공유)
- run_main_process: 로컬 전용 (계산 + 파일 출력 + BVE)

웹(api_routes) 은 compute 만 사용 → 부수효과 없음.
"""
import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path

from core.bve.bve_process import BVEProcess
from core.run import run_process
from out.excel_report import export_excel_report
from out.out_ga import format_top10
from visual.visualgraphic import visualize_routes_with_button

logger = logging.getLogger(__name__)


@dataclass
class ProcessResult:
    """GA 결과 컨테이너."""
    top: list[dict]
    raw: list


# ------------------------------------------------------------------
# 순수 계산 (웹/로컬 공유)
# ------------------------------------------------------------------
def compute(start, end, n_candidates, n_generations, top_n, chain) -> ProcessResult:
    """GA 실행 + 결과 포맷팅. 파일 I/O 없음."""
    results = run_process(start, end, n_candidates, n_generations, chain)
    top = format_top10(results, top_n)
    return ProcessResult(top=top, raw=results)


# ------------------------------------------------------------------
# 로컬 전용 부수효과
# ------------------------------------------------------------------
def export_excel(top: list[dict], path: Path) -> None:
    """엑셀 리포트 출력."""
    path.parent.mkdir(parents=True, exist_ok=True)
    export_excel_report(top, str(path))
    logger.info("엑셀 리포트: %s", path)


def export_visualization(top: list[dict], start, end, top_n: int, path: Path) -> None:
    """folium HTML 시각화."""
    path.parent.mkdir(parents=True, exist_ok=True)
    visualize_routes_with_button(
        top, start=start, end=end, top_n=top_n, map_file=str(path)
    )
    logger.info("시각화 HTML: %s", path)


def run_bve(raw_results: list) -> None:
    """BVE 변환 (결과 없으면 생략)."""
    if not raw_results:
        logger.warning("BVE 생략: 결과 없음")
        return
    BVEProcess(raw_results[0]).run()


# ------------------------------------------------------------------
# 로컬 파이프라인 (기존 run_main_process 대체)
# ------------------------------------------------------------------
def run_main_process(start, end, n_candidates, n_generations, top_n, chain,
                     output_dir: Path | None = None) -> list[dict]:
    """
    로컬 파이프라인: 계산 → 엑셀 → 시각화 → BVE.

    Args:
        output_dir: 출력 디렉토리 (기본: OS 임시 디렉토리/mapviz)
    """
    result = compute(start, end, n_candidates, n_generations, top_n, chain)

    if output_dir is None:
        output_dir = Path(tempfile.gettempdir()) / "mapviz"

    export_excel(result.top, output_dir / "top10_report.xlsx")
    export_visualization(
        result.top, start, end, top_n, output_dir / "candidate_routes.html"
    )
    run_bve(result.raw)

    return result.top