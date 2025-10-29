
import json
import math
from point2d import Point2d
from data.curve_segment import CurveSegment
from data.segment_collection import SegmentCollection
from math_utils import degrees_to_dms


def _segment_to_dict(cl):
    """Segment 객체를 JSON-friendly dict로 변환"""
    seg_data = {
        "type": cl.type.name,
        "start_sta": cl.start_sta,
        "end_sta": cl.end_sta,
        "prev_index": cl.prev_index,
        "current_index": cl.current_index,
        "next_index": cl.next_index,
        "length": cl.length,
        "start_coord": {"x": cl.start_coord.x, "y": cl.start_coord.y},
        "end_coord": {"x": cl.end_coord.x, "y": cl.end_coord.y},
        "start_azimuth": cl.start_azimuth,
        "end_azimuth": cl.end_azimuth,
    }
    if isinstance(cl, CurveSegment):
        seg_data.update({
            "IA": degrees_to_dms(math.degrees(cl.internal_angle)),
            "radius": cl.radius,
            "ip_coord": {"x": cl.ip_coordinate.x, "y": cl.ip_coordinate.y},
            "tangent_length": cl.tangent_length,
            "external_secant": cl.external_secant,
            "middle_oridante": cl.middle_oridante,
            "direction": cl.direction.name,
        })
    return seg_data


def _group_to_dict(group, index):
    """Group 객체를 JSON-friendly dict로 변환"""
    def _coord_to_dict(pt):
        return {"x": pt.x, "y": pt.y} if pt is not None else None

    return {
        "group_index": index,
        "radius": getattr(group, "radius", None),
        "bp_coord": _coord_to_dict(getattr(group, "bp_coordinate", None)),
        "ip_coord": _coord_to_dict(getattr(group, "ip_coordinate", None)),
        "ep_coord": _coord_to_dict(getattr(group, "ep_coordinate", None)),
        "num_segments": len(group.segments) if hasattr(group, "segments") else None,
        "segment_types": [seg.type.name for seg in getattr(group, "segments", [])],
    }



def _save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def _save_txt(data, path):
    with open(path, "w", encoding="utf-8") as f:
        for cl in data:
            f.write(f"\n=== 항목 ===\n")
            for k, v in cl.items():
                f.write(f"{k}: {v}\n")


def _compare_json(before, after):
    """JSON 데이터 비교 후 변경된 값만 diff dict로 반환"""
    diffs = []
    for i, (b, a) in enumerate(zip(before, after)):
        seg_diff = {"index": i, "changes": {}}
        for key in a.keys():
            if b.get(key) != a.get(key):
                seg_diff["changes"][key] = {"before": b.get(key), "after": a.get(key)}
        if seg_diff["changes"]:
            diffs.append(seg_diff)
    return diffs


def test_segment_collection_update(output_format="json", diff_test=True, file_path=''):
    """
    SegmentCollection 테스트 + diff 비교 + 그룹 정보 출력
    output_format: "json" | "txt"
    diff_test: True일 때 before/after 비교 수행
    """
    coords = [
        Point2d(0, 0),
        Point2d(100, 0),
        Point2d(150, 50),
        Point2d(546, 1535),
    ]
    radii = [50, 30, 40]

    collection = SegmentCollection()
    collection.create_by_pi_coords(coords, radii)

    # === 1️⃣ Before 상태 ===
    before_segments = [_segment_to_dict(cl) for cl in collection.segment_list]
    before_groups = [_group_to_dict(g, i) for i, g in enumerate(collection.groups)]

    # === 변경 ===
    new_ip = Point2d(120, 20)
    collection.update_pi_by_index(new_ip, 1)
    new_r = 100
    collection.update_radius_by_index(new_r, 1)

    # === 2️⃣ After 상태 ===
    after_segments = [_segment_to_dict(cl) for cl in collection.segment_list]
    after_groups = [_group_to_dict(g, i) for i, g in enumerate(collection.groups)]

    # === 3️⃣ Diff 계산 ===
    diff_segments = _compare_json(before_segments, after_segments) if diff_test else []
    diff_groups = _compare_json(before_groups, after_groups) if diff_test else []

    # === 4️⃣ 저장 ===
    if output_format == "json":
        _save_json(before_segments, file_path + "before_segments.json")
        _save_json(after_segments, file_path + "after_segments.json")
        _save_json(before_groups, file_path + "before_groups.json")
        _save_json(after_groups, file_path + "after_groups.json")

        if diff_segments:
            _save_json(diff_segments, file_path + "diff_segments.json")
        if diff_groups:
            _save_json(diff_groups, file_path + "diff_groups.json")
    else:
        _save_txt(before_segments, file_path + "before_segments.txt")
        _save_txt(after_segments, file_path + "after_segments.txt")
        _save_txt(before_groups, file_path + "before_groups.txt")
        _save_txt(after_groups, file_path + "after_groups.txt")

        if diff_segments:
            _save_txt(diff_segments, file_path + "diff_segments.txt")
        if diff_groups:
            _save_txt(diff_groups, file_path + "diff_groups.txt")

    print("✅ 테스트 완료")
    print("   → before/after/diff (segments + groups) 저장됨")

def test_current_collection(collection, file_path):
    # === 4️⃣ 저장 ===
    segments = [_segment_to_dict(cl) for cl in collection.segment_list]
    groups = [_group_to_dict(g, i) for i, g in enumerate(collection.groups)]
    _save_json(segments, file_path + "segments.json")
    _save_json(groups, file_path + "groups.json")


    print("   → before/after/diff (segments + groups) 저장됨")
# ===== 실행 예시 =====
if __name__ == "__main__":
    out_path = "c:/temp/"
    test_segment_collection_update(output_format="json", diff_test=True, file_path=out_path)
