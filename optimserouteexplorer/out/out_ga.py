# out/out_ga.py
"""
GA 최종 후보를 웹/엑셀용 dict 로 변환.

직렬화 계약:
- 반환 dict 는 원시 타입만 (list/float/int/str/None) 포함
- shapely LineString, numpy 배열/스칼라, 커스텀 객체는 변환 후 포함
- collections 는 station 별 구조 요약(list[dict]) 으로 변환
"""
import logging

import numpy as np
from shapely import LineString

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# 직렬화 헬퍼
# ------------------------------------------------------------------
def _jsonable(v):
    """numpy/shapely 를 원시 타입으로 변환."""
    if v is None:
        return None
    if isinstance(v, dict):
        return {k: _jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    if isinstance(v, LineString):
        return [[float(x), float(y)] for x, y in v.coords]
    if isinstance(v, np.generic):
        return v.item()
    if isinstance(v, np.ndarray):
        return v.tolist()
    if isinstance(v, (str, int, float, bool)):
        return v
    # 그 외 객체는 문자열로 (직렬화 보장)
    return str(v)


def _summarize_structures(structure_collection, station_list) -> list[dict]:
    """
    structure_collection 을 station 별 구조 요약(list[dict]) 으로 변환.
    visualgraphic 이 dict 기반으로 사용할 수 있게.
    """
    if structure_collection is None or not station_list:
        return []

    out = []
    for sta in station_list:
        try:
            stype = structure_collection.get_structure_type_at(sta)
        except Exception:
            stype = None
        try:
            s = structure_collection.find_containing(sta)
        except Exception:
            s = None

        out.append({
            "station": _jsonable(sta),
            "type": str(stype) if stype is not None else None,
            "name": getattr(s, "name", None) if s is not None else None,
            "length": float(getattr(s, "length", 0.0)) if s is not None else 0.0,
        })
    return out


# ------------------------------------------------------------------
# 메인
# ------------------------------------------------------------------
def format_top10(population, top_n: int) -> list[dict]:
    """GA 최종 후보를 웹/엑셀용 dict 로 변환 (직렬화 가능 보장)."""
    if not population:
        return []

    top = []
    for i, cand in enumerate(population[:top_n]):
        plan_full = cand.get("plan_full") or {}
        profile = cand.get("profile") or {}
        result = cand.get("result") or {}
        radius_list = cand.get("radius_list") or []

        linestring = plan_full.get("linestring")
        length = float(linestring.length) if linestring is not None else None

        bridges = result.get("bridges") or []
        tunnels = result.get("tunnels") or []
        slopes = profile.get("slopes") or []

        collections = _summarize_structures(
            result.get("structure_collection"),
            plan_full.get("station_list", []),
        )

        top.append({
            "ID": i,
            "노선연장": length,
            "공사비": (
                round(float(cand["cost"]), 1)
                if cand.get("cost") is not None else None
            ),
            "교량갯수": len(bridges),
            "터널갯수": len(tunnels),
            "곡선갯수": len(radius_list),
            "기울기갯수": len(slopes),
            "최급기울기": (max(slopes) * 1000.0) if slopes else 0.0,
            "최소곡선반경": min(radius_list) if radius_list else None,
            "fitness": _jsonable(cand.get("fitness")),
            "score": _jsonable(cand.get("score")),
            "coords": [
                [float(c[1]), float(c[0])]
                for c in plan_full.get("wgs_coords", [])
            ],
            "fls": _jsonable(profile.get("fg_profile")),
            "grounds": _jsonable(profile.get("eg_profile")),
            "station_list": _jsonable(plan_full.get("station_list", [])),
            "collections": collections,
        })
    return top