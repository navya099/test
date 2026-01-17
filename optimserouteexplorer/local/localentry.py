from core.bve.bve_process import BVEProcess
from core.run import run_process
from out.bve_export import BVEExporter
from out.excel_report import export_excel_report
from out.out_ga import format_top10
from visual.visualgraphic import visualize_routes_with_button


def get_input_points():
    """사용자 입력을 받아 시작점과 끝점 좌표 반환"""
    while True:
        try:
            start = tuple(map(float, input('시작 점 경위도 입력 (예: 37.5,127.1): ').split(',')))
            end = tuple(map(float, input('끝 점 경위도 입력 (예: 37.5,127.1): ').split(',')))
            return start, end
        except ValueError:
            print("입력이 잘못되었습니다. 다시 입력하세요.")


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


def main():
    # 1. 입력
    start, end = get_input_points()

    # 2. 원본 처리
    results = process_routes(start, end, n_candidates=10, n_generations=10)

    # 3. 포맷팅
    top10 = format_results(results, top_n=10)

    # 4. 출력
    export_results(top10)

    #5 #시각화
    visulalize(top10, start, end, top_n=10)

    #6. BVE 변환 (필요 시)
    bve_processor = BVEProcess(results[0])
    bve_processor.run()