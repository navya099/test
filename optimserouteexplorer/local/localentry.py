from core.run import run_process
from out.excel_report import export_excel_report
from visual.visualgraphic import visualize_routes_with_button


def main():
    # 예: 위도, 경도 입력을 공백으로 구분
    # 위도, 경도 입력을 공백으로 구분
    while True:
        try:
            start = tuple(map(float, input('시작 점 경위도 입력 (예: 37.5,127.1): ').split(',')))
            end = tuple(map(float, input('끝 점 경위도 입력 (예: 37.5,127.1): ').split(',')))
            break
        except ValueError:
            print("입력이 잘못되었습니다:")

    top10 = run_process(start, end, n_candidates=30, n_generations=50, top_n=1)
    export_excel_report(top10, "c:/temp/top10_report.xlsx")
    visualize_routes_with_button(top10, start, end, top_n=10, map_file="c:/temp/candidate_routes.html")
