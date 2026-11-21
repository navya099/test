"""Straight-alignment, metre-based geometry for conceptual bridge review."""
import math

from .alignment import DEFAULTS as ALIGNMENT_DEFAULTS, Alignment, bounds, separation

TYPES = {"psc": "PSC 거더교", "box": "ST BOX 거더교", "arch": "아치교",
         "cable": "사장교", "ed": "ED교"}
GAUGE_DEFAULTS = {
    "track_spacing": 4, "vehicle_width": 3.1, "vehicle_height": 4.3,
    "structure_width": 3.8, "structure_height": 4.9, "gauge_base": .15,
}
EXAMPLE = {
    **GAUGE_DEFAULTS,
    **ALIGNMENT_DEFAULTS,
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


def validate_obstacles(obstacles):
    if not isinstance(obstacles, list) or len(obstacles) > 100:
        raise ValueError("지장물은 최대 100개의 배열로 입력하세요.")
    validated = []
    for index, obstacle in enumerate(obstacles, 1):
        try:
            if not isinstance(obstacle, dict):
                raise ValueError("객체 형식으로 입력하세요.")
            name = obstacle.get("name")
            if not isinstance(name, str) or not 1 <= len(name.strip()) <= 100:
                raise ValueError("이름은 1~100자로 입력하세요.")
            bounds = [obstacle.get(key) for key in ("min", "max")]
            if any(not isinstance(point, list) or len(point) != 3 for point in bounds):
                raise ValueError("min/max는 [측점, 횡방향, 표고]입니다.")
            lo, hi = [[number(value, -2e6, 2e6) for value in point] for point in bounds]
            if any(a >= b for a, b in zip(lo, hi)):
                raise ValueError("각 최소값은 최대값보다 작아야 합니다.")
        except ValueError as error:
            raise ValueError(f"지장물 {index}번: {error}") from error
        validated.append({"name": name.strip(), "min": lo, "max": hi})
    return validated


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
    radius = number(config.get("curve_radius", 0), -1e6, 1e6)
    cant = number(config.get("cant_mm", 0), -200, 200)
    if radius and (abs(radius) < 60 or (end-start) / abs(radius) > math.pi / 2):
        raise ValueError("곡선 반경의 절댓값은 60 m 이상이며 교량 구간의 원호각은 90도 이하여야 합니다.")
    alignment = Alignment(start, radius, cant, deck)
    track_centers = {}
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
                        if radius:
                            objects[-1]["chord"] = True
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
    settings = {**GAUGE_DEFAULTS, **config}
    spacing = number(settings["track_spacing"], .1, 40)
    base = number(settings["gauge_base"], 0, 20)
    gauges = []
    for prefix, name in (("vehicle", "차량한계"), ("structure", "건축한계")):
        gauge_width = number(settings[f"{prefix}_width"], .1, 40)
        height = number(settings[f"{prefix}_height"], .1, 40)
        if height <= base:
            raise ValueError(f"{name} 상단 높이는 하단 높이보다 커야 합니다.")
        gauges.append((name, gauge_width / 2, height))
    if gauges[1][1] < gauges[0][1] or gauges[1][2] < gauges[0][2]:
        raise ValueError("건축한계는 차량한계를 포함해야 합니다.")
    offsets = [0] if tracks == 1 else [-spacing / 2, spacing / 2]
    for index, offset in enumerate(offsets, 1):
        for name, half_width, height in gauges:
            box(f"{index}번 선로 {name}", "envelope", [start, offset-half_width, deck+base],
                [end, offset+half_width, deck+height], "gauge")
            track_centers[objects[-1]["id"]] = offset
    obstacles = validate_obstacles(config.get("obstacles"))
    for obstacle in obstacles:
        box(obstacle["name"], "context", obstacle["min"], obstacle["max"], "obstacle")

    cells_by_id = {}
    station_ranges = {}
    if radius or cant:
        for item in objects:
            if item["role"] == "obstacle" or not radius and item["role"] != "gauge":
                continue
            station_ranges[item["id"]] = (item["min"][0], item["max"][0])
            cells = list(alignment.cells(item, track_centers.get(item["id"])))
            item["mesh"] = [cell[2] for cell in cells]
            item["min"], item["max"] = bounds(vertex for cell in cells for vertex in cell[2])
            if "axis" in item:
                item["axis"] = [alignment.point(point) for point in item["axis"]]
            cells_by_id[item["id"]] = cells

    def cells(item):
        return cells_by_id.get(item["id"], [(item["min"], item["max"], None)])

    findings = []
    parts = [item for item in objects if item["role"] == "bridge"]
    for target in objects:
        if target["role"] == "bridge":
            continue
        limit = clearance if target["role"] == "obstacle" else 0
        threshold = max(limit, 1e-8)
        for part in parts:
            if separation(part["min"], part["max"], target["min"], target["max"]) > threshold:
                continue
            best = math.inf
            center = None
            target_cells = cells(target)
            for lo, hi, _ in cells(part):
                if separation(lo, hi, target["min"], target["max"]) > min(best, threshold):
                    continue
                for t_lo, t_hi, _ in target_cells:
                    gap = separation(lo, hi, t_lo, t_hi)
                    if gap < best:
                        best = gap
                        center = [(max(a, min(b, c)) + max(a, min(b, d))) / 2
                                  for a, b, c, d in zip(lo, hi, t_lo, t_hi)]
            if best > 1e-8 and best >= limit:
                continue
            status = "중첩" if best < -1e-8 else "접촉" if best <= 1e-8 else "이격 미달"
            if "axis" in part or "mesh" in part or "mesh" in target:
                status += " 후보 (외접 상자)"
            station = alignment.station_at(center)
            if part["id"] in station_ranges:
                lo_station, hi_station = station_ranges[part["id"]]
                station = max(lo_station, min(hi_station, station))
            findings.append({"part": part["id"], "target": target["id"], "status": status,
                             "station": round(station, 3),
                             "distance": round(max(0, best), 4), "required": limit,
                             "point": center})
    return {"objects": objects, "findings": findings, "stations": stations,
            "length": end-start, "kind": TYPES[kind],
            "alignment": {"curve_radius": radius, "cant_mm": cant},
            "missing": [] if obstacles else ["외부 지장물 데이터 미입력"]}
