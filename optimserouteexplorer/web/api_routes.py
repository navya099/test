# web/api_routes.py
import pandas as pd
from flask import Blueprint, request, jsonify

from core.generate_routes import GenerateRoutes

api = Blueprint("api", __name__)

@api.route("/compute", methods=["POST"])
def compute():
    data = request.json
    start = data["start"]
    end = data["end"]

    print(f"Received start={start}, end={end}")

    generator_routes = GenerateRoutes()
    alignments = generator_routes.generate_and_rank(start, end, n_candidates=30)

    top10 = []
    for i, a in enumerate(alignments[:10]):
        top10.append({
            "ID": i,
            "노선연장": round(a.length, 1),
            "공사비": round(a.cost, 1),
            "교량갯수": a.bridge_count,
            "터널갯수": a.tunnel_count,
            "곡선갯수": a.radius_count,
            "기울기갯수": a.grades_count,
            "최급기울기": a.max_grade,
            "최소곡선반경": a.min_radius,
            "coords": [list(c) for c in a.coords],
            "fls": [list(f) for f in a.fls],
            "grounds": list(a.grounds)
        })

    # 엑셀로 저장할 때 필요한 키만 선택
    excel_keys = [
        "ID",
        "노선연장",
        "공사비",
        "교량갯수",
        "터널갯수",
        "곡선갯수",
        "기울기갯수",
        "최급기울기",
        "최소곡선반경"
    ]

    # top10은 그대로 두고, 엑셀용 데이터만 새로 만듦
    excel_data = [{k: entry[k] for k in excel_keys} for entry in top10]

    # 엑셀 저장
    df = pd.DataFrame(excel_data)
    df.to_excel("c:/temp/top10_alignments.xlsx", index=False)
    print("Excel 저장 완료!")

    return jsonify(top10)
