# transform.py
"""mileage/lateral_offset ↔ 화면 좌표 변환. visualize.py와 동일 로직."""

SCALE_X = 1000.0        # 1 km → 1000 px
SCALE_Y = 200.0         # 1 m  → 200 px
BASE_MILEAGE = 12.0     # 화면 중앙 정렬 기준


def track_direction_sign(track):
    return -1 if track["direction"] == "down" else 1


def track_base_y(track):
    return 0.0 if track["type"] == "main" else 8.0


def node_to_scene(node, tracks_by_id):
    trk = tracks_by_id[node["track_id"]]
    sign = track_direction_sign(trk)
    x = (node["mileage"] - BASE_MILEAGE) * SCALE_X
    y = (node["lateral_offset"] + track_base_y(trk)) * SCALE_Y * sign
    return x, y


def scene_to_node(x, y, track):
    """드래그 결과를 다시 mileage/lateral_offset으로."""
    sign = track_direction_sign(track)
    mileage = x / SCALE_X + BASE_MILEAGE
    lateral = (y * sign) / SCALE_Y - track_base_y(track)
    return mileage, lateral