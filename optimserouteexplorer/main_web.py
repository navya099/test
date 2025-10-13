import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS

from optimserouteexplorer.generate_lroutes import GenerateRoutes

app = Flask(__name__)
CORS(app)  # 모든 도메인에서 요청 허용

@app.route("/compute", methods=["POST"])
def compute():
    data = request.json
    start = data["start"]
    end = data["end"]

    print(f"Received start={start}, end={end}")

    # 멀티코어 후보 생성(로컬)
    genertor_routes = GenerateRoutes()
    alignments = genertor_routes.generate_and_rank(start, end, n_candidates=100)

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
            # 반드시 리스트 형태로 변환
            "coords": [list(c) for c in a.coords],
            "fls": [list(f) for f in a.fls],
            "grounds": list(a.grounds)
        })

    # Excel 저장
    df = pd.DataFrame(top10)
    df.to_excel("top10_alignments.xlsx", index=False)
    print("Excel 저장 완료!")

    return jsonify(top10)


if __name__ == "__main__":
    app.run(port=5000)
