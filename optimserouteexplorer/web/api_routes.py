# web/api_routes.py
from flask import Blueprint, request, jsonify

from local.localentry import run_main_process


api = Blueprint("api", __name__)

@api.route("/compute", methods=["POST"])
def compute():
    data = request.json
    start = data["start"]
    end = data["end"]

    print(f"Received start={start}, end={end}")

    top10 = run_main_process(start, end, n_candidates=50, n_generations=100, top_n=10, chain=25)

    return jsonify(top10)
