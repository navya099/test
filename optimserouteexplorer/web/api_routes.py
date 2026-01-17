# web/api_routes.py
from flask import Blueprint, request, jsonify

from local.localentry import format_results
from out.excel_report import export_excel_report
from core.run import run_process

api = Blueprint("api", __name__)

@api.route("/compute", methods=["POST"])
def compute():
    data = request.json
    start = data["start"]
    end = data["end"]

    print(f"Received start={start}, end={end}")

    results = run_process(start, end, n_candidates=50, n_generations=100, top_n=10)
    top10 = format_results(results)
    export_excel_report(top10, "c:/temp/top10_report.xlsx")

    return jsonify(top10)
