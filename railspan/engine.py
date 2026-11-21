"""Straight-alignment, metre-based geometry for conceptual bridge review."""
import math

TYPES = {"psc": "PSC 거더교", "box": "ST BOX 거더교", "arch": "아치교",
         "cable": "사장교", "ed": "ED교"}
EXAMPLE = {
    "kind": "psc", "start": 0, "spans": [30, 50, 30], "width": 11,
    "deck": 15, "ground": 0, "rise": 12, "tracks": 2, "clearance": 0.5,
    "obstacles": [
        {"name": "도로 통과 공간", "min": [25, -18, 0], "max": [36, 18, 7]},
        {"name": "하천 검토 구역", "min": [48, -24, -1], "max": [72, 24, 3]},
        {"name": "지하 매설물", "min": [78, -15, -1.4], "max": [82, 15, -0.8]},
    ],
}


def span_ranges(start, end, nominal):
    """Even temporary spans, each <= nominal. Never create tiny leftover span."""
    n = max(1, math.ceil((end-start)/nominal - 1e-10))
    return [(start+(end-start)*i/n, start+(end-start)*(i+1)/n) for i in range(n)]


def number(value, low, high):
    if type(value) not in (int, float) or not low <= value <= high:
        raise ValueError(f"숫자 입력 범위는 {low} ~ {high}입니다.")
    return value


def generate(config):
    if not isinstance(config, dict):
        raise ValueError("프로젝트는 JSON 객체여야 합니다.")
    kind = config.get("kind")
    if kind not in TYPES:
        raise ValueError("교량 형식을 선택하세요.")
    start = number(config.get("start"), -1e6, 1e6)
    width = number(config.get("width"), 5, 40)
    ground = number(config.get("ground"), -1000, 8000)
    deck = number(config.get("deck"), ground + 4, ground + 150)
    rise = number(config.get("rise"), 1, 150)
    tracks = number(config.get("tracks"), 1, 2)
    if tracks not in (1, 2):
        raise ValueError("단선 또는 복선을 선택하세요.")
    clearance = number(config.get("clearance"), 0, 100)
    lengths = config.get("spans")
    if not isinstance(lengths, list) or len(lengths) > 30:
        raise ValueError("경간은 최대 30개입니다.")
    stations = [start]
    for length in lengths:
        stations.append(stations[-1] + number(length, 5, 500))
    if not lengths:
        total = number(config.get("length"), 5, 1500)
        nominal = number(config.get("nominal"), 5, 500)
        stations.extend(end for _, end in span_ranges(start, start + total, nominal))
    if len(stations) > 31:
        raise ValueError("경간은 최대 30개입니다.")
    objects = []

    def box(name, group, lo, hi, role="bridge"):
        objects.append({"id": len(objects) + 1, "name": name, "group": group,
                        "role": role, "min": lo, "max": hi})

    def beam(name, group, a, b, thickness):
        radius = thickness / 2
        box(name, group, [min(x, y) - radius for x, y in zip(a, b)],
            [max(x, y) + radius for x, y in zip(a, b)])
        objects[-1]["axis"] = [a, b]
        objects[-1]["thickness"] = thickness

    half = width / 2
    depth = 1.7 if kind == "psc" else 2.2
    end = stations[-1]
    box("슬래브", "deck", [start, -half, deck - .35], [end, half, deck])
    for index, (a, b) in enumerate(zip(stations, stations[1:]), 1):
        offsets = [-.36 * width, -.12 * width, .12 * width, .36 * width] if kind == "psc" else [0]
        for offset in offsets:
            girder_half = .4 if kind == "psc" else width * .27
            if kind == "ed":
                girder_half = width * .31
            box(f"거더 S{index}", "girder", [a, offset - girder_half, deck - .35 - depth],
                [b, offset + girder_half, deck - .35])
        if kind == "ed":
            for x, y in ((a, a + (b-a)*.18), (b - (b-a)*.18, b)):
                beam(f"변단면 헌치 S{index}", "girder",
                     [x, 0, deck - .35 - depth - .2], [y, 0, deck - .35 - depth - .2], .4)
        if kind == "arch":
            for side in (-1, 1):
                y = side * (half - .35)
                points = []
                for step in range(13):
                    t = step / 12
                    points.append([a + (b-a)*t, y, deck + 4*rise*t*(1-t)])
                for first, second in zip(points, points[1:]):
                    beam(f"아치 리브 S{index}", "special", first, second, .65)
                for point in points[2:-1:2]:
                    beam(f"행어 S{index}", "special", [point[0], y, deck], point, .16)
    for index, station in enumerate(stations):
        label = f"교대 A{1 if index == 0 else 2}" if index in (0, len(stations)-1) else f"교각 P{index}"
        support = deck - .35 - depth
        box(f"{label} 기초", "foundation", [station-2.5, -half*.8, ground-2],
            [station+2.5, half*.8, ground])
        box(label, "pier", [station-1, -half*.46, ground], [station+1, half*.46, support-.9])
        box(f"{label} 코핑", "pier", [station-1.3, -half*.93, support-.9],
            [station+1.3, half*.93, support-.25])
        for offset in offsets:
            box(f"{label} 받침", "bearing", [station-.35, offset-.35, support-.25],
                [station+.35, offset+.35, support])
        if kind in ("cable", "ed") and (0 < index < len(stations)-1 or len(stations) == 2):
            height = rise if kind == "cable" else rise*.5
            neighbors = stations[max(0,index-1):index] + stations[index+1:index+2]
            for side in (-1, 1):
                y = side * (half - .35)
                box(f"주탑 {index+1}", "special", [station-.5, y-.3, ground],
                    [station+.5, y+.3, deck+height])
                for neighbor in neighbors:
                    for fraction in (.25, .45, .65, .85):
                        x = station + fraction*(neighbor-station)
                        beam("사장 케이블" if kind == "cable" else "외부 케이블",
                             "special", [station, y, deck+height*(.65+.35*fraction)], [x, y, deck], .14)
    for side in (-1, 1):
        edge = side * half
        lo, hi = sorted((edge, edge + side * .75))
        box("점검통로", "accessory", [start, lo, deck-.18], [end, hi, deck+.05])
        rail = edge + side*.70
        for station in stations:
            box("난간 기둥", "accessory", [station-.06, rail-.06, deck],
                [station+.06, rail+.06, deck+1.1])
        box("난간", "accessory", [start, rail-.06, deck+1], [end, rail+.06, deck+1.12])
        beam("배수관로", "accessory", [start, edge*.9, deck-1],
             [end, edge*.9, deck-1], .25)
    for index, offset in enumerate([0] if tracks == 1 else [-2, 2], 1):
        for name, half_width, height in (("차량한계", 1.55, 4.3), ("건축한계", 1.9, 4.9)):
            box(f"{index}번 선로 {name}", "envelope", [start, offset-half_width, deck+.15],
                [end, offset+half_width, deck+height], "gauge")
    obstacles = config.get("obstacles")
    if not isinstance(obstacles, list) or len(obstacles) > 100:
        raise ValueError("지장물은 최대 100개의 배열로 입력하세요.")
    for obstacle in obstacles:
        if not isinstance(obstacle, dict) or not isinstance(obstacle.get("name"), str) or not obstacle["name"].strip():
            raise ValueError("지장물 이름을 입력하세요.")
        bounds = [obstacle.get(key) for key in ("min", "max")]
        if any(not isinstance(point, list) or len(point) != 3 for point in bounds):
            raise ValueError("지장물의 min/max는 [측점, 횡방향, 표고]입니다.")
        lo, hi = [[number(value, -2e6, 2e6) for value in point] for point in bounds]
        if any(a >= b for a, b in zip(lo, hi)):
            raise ValueError("지장물의 각 최소값은 최대값보다 작아야 합니다.")
        box(obstacle["name"][:100], "context", lo, hi, "obstacle")

    findings = []
    for target in objects:
        if target["role"] == "bridge":
            continue
        for part in objects:
            if part["role"] != "bridge":
                continue
            gaps = [max(a-d, c-b) for a, b, c, d in zip(
                part["min"], part["max"], target["min"], target["max"])]
            distance = math.hypot(*(max(0, gap) for gap in gaps))
            limit = clearance if target["role"] == "obstacle" else 0
            if distance > 1e-8 and distance >= limit:
                continue
            status = "중첩" if max(gaps) < -1e-8 else "접촉" if distance <= 1e-8 else "이격 미달"
            if "axis" in part:
                status += " 후보 (외접 상자)"
            lo = max(part["min"][0], min(part["max"][0], target["min"][0]))
            hi = max(part["min"][0], min(part["max"][0], target["max"][0]))
            findings.append({"part": part["id"], "target": target["id"], "status": status,
                             "station": round((lo+hi)/2, 3), "distance": round(distance, 4),
                             "required": limit})
    return {"objects": objects, "findings": findings, "stations": stations,
            "length": end-start, "kind": TYPES[kind],
            "missing": [] if obstacles else ["외부 지장물 데이터 미입력"]}
