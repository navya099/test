# web/api_routes.py
"""GA 계산 API. 순수 compute 만 호출 (부수효과 없음)."""
import logging

from flask import Blueprint, jsonify, request

from local.localentry import compute

logger = logging.getLogger(__name__)
api = Blueprint("api", __name__)

# 자원 보호 상한
MAX_CANDIDATES = 200
MAX_GENERATIONS = 500
MAX_CHAIN = 100
MIN_CANDIDATES = 3
MIN_GENERATIONS = 1


def _error(msg: str, status: int = 400):
    return jsonify(error="bad_request", message=msg), status


@api.route("/compute", methods=["POST"])
def compute_route():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _error("JSON body required")

    start = data.get("start")
    end = data.get("end")
    if start is None or end is None:
        return _error("'start' and 'end' are required")

    # 좌표 검증 (2개 숫자 리스트)
    for name, v in (("start", start), ("end", end)):
        if not (isinstance(v, (list, tuple)) and len(v) == 2):
            return _error(f"'{name}' must be [lat, lon]")
        try:
            float(v[0]); float(v[1])
        except (TypeError, ValueError):
            return _error(f"'{name}' must contain numbers")

    # 파라미터 (기본값 + 상한 클램프)
    try:
        n_candidates = int(data.get("n_candidates", 50))
        n_generations = int(data.get("n_generations", 100))
        top_n = int(data.get("top_n", 10))
        chain = int(data.get("chain", 25))
    except (TypeError, ValueError):
        return _error("numeric parameters required")

    n_candidates = max(MIN_CANDIDATES, min(n_candidates, MAX_CANDIDATES))
    n_generations = max(MIN_GENERATIONS, min(n_generations, MAX_GENERATIONS))
    chain = max(1, min(chain, MAX_CHAIN))
    top_n = max(1, min(top_n, n_candidates))

    logger.info(
        "compute start=%s end=%s n_candidates=%d n_generations=%d chain=%d",
        start, end, n_candidates, n_generations, chain,
    )

    try:
        result = compute(
            start=tuple(start), end=tuple(end),
            n_candidates=n_candidates,
            n_generations=n_generations,
            top_n=top_n,
            chain=chain,
        )
    except Exception:
        logger.exception("compute 실패")
        return jsonify(error="internal_error"), 500

    return jsonify(result=result.top)