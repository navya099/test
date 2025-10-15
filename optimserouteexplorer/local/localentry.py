import pandas as pd

from ga.ga import GeneticAlgorithm
from visual.visualgraphic import visualize_routes_with_button


def main():
    # 예: 위도, 경도 입력을 공백으로 구분
    # 위도, 경도 입력을 공백으로 구분
    try:
        start = tuple(map(float, input('시작 점 경위도 입력 (예: 37.5,127.1): ').split(',')))
        end = tuple(map(float, input('끝 점 경위도 입력 (예: 37.5,127.1): ').split(',')))
    except ValueError as e:
        print("입력이 잘못되었습니다:", e)
        return

    ga = GeneticAlgorithm(start, end, n_candidates=30, n_generations=10)
    final_population = ga.evolve()
    top10 = final_population[:10]

    df = pd.DataFrame([{
        "ID": i,
        "노선연장": round(a.length, 1),
        "공사비": round(a.cost, 1),
        "교량갯수": a.bridge_count,
        "터널갯수": a.tunnel_count,
        "곡선갯수": a.radius_count,
        "기울기갯수": a.grades_count,
        "최급기울기": a.max_grade,
        "최소곡선반경": a.min_radius
    } for i, a in enumerate(top10)])

    df.to_excel("ga_top10_alignments.xlsx", index=False)
    print("GA 기반 Excel 저장 완료!")

    visualize_routes_with_button(top10, start, end, top_n=10)