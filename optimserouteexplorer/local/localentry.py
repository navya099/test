
from core.bve.bve_process import BVEProcess
from core.run import run_process
from out.excel_report import export_excel_report
from out.out_ga import format_top10
from visual.visualgraphic import visualize_routes_with_button

def process_routes(start, end, n_candidates=30, n_generations=50):
    """GA 실행 및 결과 반환"""
    results = run_process(start, end, n_candidates=n_candidates, n_generations=n_generations)
    return results


def format_results(results, top_n=10):
    """상위 10개 결과 포맷팅"""
    return format_top10(results, top_n=top_n)


def export_results(top10):
    """결과를 다양한 포맷으로 출력"""
    export_excel_report(top10, "c:/temp/top10_report.xlsx")

def visulalize(top10, start, end, top_n=10):
    visualize_routes_with_button(top10, start=start, end=end, top_n=top_n,
                                 map_file="c:/temp/candidate_routes.html")


def run_main_process(start, end, n_candidates, n_generations, top_n):

    # 2. 원본 처리
    results = process_routes(start, end, n_candidates=n_candidates, n_generations=n_generations)

    # 3. 포맷팅
    top10 = format_results(results, top_n=top_n)

    # 4. 출력
    export_results(top10)

    #5 #시각화
    visulalize(top10, start, end, top_n=top_n)

    #6. BVE 변환 (필요 시)
    bve_processor = BVEProcess(results[0])
    bve_processor.run()