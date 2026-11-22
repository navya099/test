"""Metre-based geometry and clearance checks for conceptual bridge review."""
import math

from .alignment import DEFAULTS as ALIGNMENT_DEFAULTS, Alignment, StationProfile, bounds, separation, vertical_separation
from .horizontal import curvature
from .vertical_profile import VerticalCurve

TYPES = {"psc": "PSC 거더교", "box": "ST BOX 거더교", "arch": "아치교",
         "cable": "사장교", "ed": "ED교"}
OBSTACLE_CATEGORIES = {
    "road": "도로", "waterway": "하천", "utility": "지하 매설물",
    "rail": "철도시설물", "other": "기타 지장물",
}
TARGET_CATEGORIES = {**OBSTACLE_CATEGORIES, "gauge": "차량·건축한계"}
ACCESSORY_SIDES = {"none": (), "left": (1,), "right": (-1,), "both": (-1, 1)}

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
        {"name": "도로 통과 공간", "category": "road", "clearance_mode": "vertical", "min": [25, -18, 0], "max": [36, 18, 7]},
        {"name": "하천 검토 구역", "category": "waterway", "clearance_mode": "vertical", "min": [48, -24, -1], "max": [72, 24, 3]},
        {"name": "지하 매설물", "category": "utility", "clearance": 1.0, "min": [78, -15, -1.4], "max": [82, 15, -0.8]},
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
            category = obstacle.get("category", "other")
            if not isinstance(category, str) or category not in OBSTACLE_CATEGORIES:
                raise ValueError(f"유형 코드는 {', '.join(OBSTACLE_CATEGORIES)} 중 하나여야 합니다.")
            clearance = obstacle.get("clearance")
            result = {"name": name.strip(), "min": lo, "max": hi, "category": category}
            if "clearance_mode" in obstacle:
                mode = obstacle["clearance_mode"]
                if mode not in ("spatial", "vertical"):
                    raise ValueError("이격 방식은 spatial 또는 vertical을 입력하세요.")
                if mode == "vertical" and category not in ("road", "waterway"):
                    raise ValueError("수직 이격은 도로 또는 하천 유형에 적용할 수 있습니다.")
                result["clearance_mode"] = mode
            if clearance is not None:
                try:
                    result["clearance"] = number(clearance, 0, 100)
                except ValueError as error:
                    raise ValueError("지장물 이격은 0~100 m여야 합니다.") from error
        except ValueError as error:
            raise ValueError(f"지장물 {index}번: {error}") from error
        validated.append(result)
    return validated


def validate_profile(points, label, minimum, maximum, *, extent=None, value_label="표고"):
    if not isinstance(points, list) or len(points) == 1 or len(points) > 100:
        raise ValueError(f"{label}은 비워 두거나 2~100개의 측점으로 입력하세요.")
    profile = []
    for index, point in enumerate(points, 1):
        if not isinstance(point, list) or len(point) != 2:
            raise ValueError(f"{label} {index}행에 측점과 {value_label} 값을 입력하세요.")
        try:
            station = number(point[0], -2e6, 2e6)
            elevation = number(point[1], minimum, maximum)
        except ValueError as error:
            raise ValueError(f"{label} {index}행: {error}") from error
        if profile and station <= profile[-1][0]:
            raise ValueError(f"{label} {index}행의 측점은 이전 측점보다 커야 합니다.")
        profile.append([station, elevation])
    if profile and extent is not None:
        start, end = extent
        if profile[0][0] > start + 1e-8 or profile[-1][0] < end - 1e-8:
            raise ValueError(f"{label}은 교량 구간({start:g} ~ {end:g} m) 전체를 포함해야 합니다.")
    return profile


def validate_plan(rows, start=None, end=None):
    if not isinstance(rows, list) or len(rows) > 100:
        raise ValueError("평면 선형 구간은 최대 100개까지 입력할 수 있습니다.")
    plan = []
    previous = start
    total_turn = 0
    for index, row in enumerate(rows, 1):
        if not isinstance(row, list) or len(row) not in (2, 3):
            raise ValueError(f"평면 선형 {index}행은 ‘끝 측점, 반경’ 또는 ‘끝 측점, 시작 반경, 끝 반경’으로 입력하세요.")
        stop = number(row[0], -2e6, 2e6)
        radii = [number(value, -1e6, 1e6) for value in row[1:]]
        if (previous is not None and stop - previous < 1e-6) or (end is not None and stop > end + 1e-8):
            raise ValueError(f"평면 선형 {index}행 끝 측점은 이전 측점보다 크고 교량 종점 이하여야 합니다.")
        if any(radius and abs(radius) < 60 for radius in radii):
            raise ValueError(f"평면 선형 {index}행 곡선 반경의 절댓값은 60 m 이상이어야 합니다.")
        if len(radii) == 2 and (radii[0] == radii[1] or radii[0] * radii[1] < 0):
            raise ValueError(f"평면 선형 {index}행의 완화곡선 반경은 서로 달라야 하며 좌·우 방향을 한 구간에서 바꿀 수 없습니다.")
        if plan and (len(row) == 3 or len(plan[-1]) == 3) and plan[-1][-1] != radii[0]:
            raise ValueError(f"측점 {previous:g} m에서 완화곡선과 인접 구간의 접속 반경이 같아야 합니다.")
        if previous is not None:
            total_turn += (stop - previous) * sum(abs(curvature(radius)) for radius in radii) / len(radii)
        plan.append([stop, *radii])
        previous = stop
    if plan and end is not None:
        if abs(previous - end) > 1e-8:
            raise ValueError(f"마지막 평면 선형 구간은 교량 종점({end:g} m)에서 끝나야 합니다.")
        plan[-1][0] = end
    if total_turn > math.pi / 2 + 1e-12:
        raise ValueError("평면 선형의 누적 절대 회전각은 90도 이하여야 합니다.")
    return plan


def build_vertical_curves(rows, profile):
    if not isinstance(rows, list) or len(rows) > 98:
        raise ValueError("종단곡선은 최대 98개까지 입력할 수 있습니다.")
    station_indices = {station: index for index, (station, _) in enumerate(profile)}
    lengths = {}
    for row in rows:
        if not isinstance(row, list) or len(row) != 2:
            raise ValueError("종단곡선은 변곡점 측점과 길이로 입력하세요.")
        station = number(row[0], -2e6, 2e6)
        length = number(row[1], .01, 4e6)
        if station in lengths:
            raise ValueError(f"측점 {station:g} m의 종단곡선을 중복 입력했습니다.")
        index = station_indices.get(station)
        if index is None or not 0 < index < len(profile) - 1:
            raise ValueError(f"측점 {station:g} m는 종단 선형의 내부 변곡점이어야 합니다.")
        lengths[station] = length

    curves = []
    for station, length in sorted(lengths.items()):
        index = station_indices[station]
        before, vip, after = profile[index-1:index+2]
        start, end = station-length/2, station+length/2
        if start < before[0] or end > after[0]:
            raise ValueError(f"측점 {station:g} m 종단곡선이 인접 변곡점 범위를 벗어납니다.")
        if curves and curves[-1].end > start:
            raise ValueError(f"측점 {station:g} m 종단곡선이 이전 곡선과 겹칩니다.")
        incoming = (vip[1]-before[1])/(station-before[0])
        outgoing = (after[1]-vip[1])/(after[0]-station)
        curves.append(VerticalCurve(start, end, vip[1]+incoming*(start-station), incoming, outgoing))
    return curves, sorted(lengths.items())


def check_profile_height(profile, terrain, start, end):
    breakpoints = sorted({start, end, *(s for s in profile.breakpoints + terrain.breakpoints if start < s < end)})

    def difference(station):
        return profile.at(station) - terrain.at(station)

    def validate(station, height):
        if not 4 - 1e-8 <= height <= 150 + 1e-8:
            raise ValueError(f"측점 {station:g} m의 슬래브와 지반 표고 차({height:.3f} m)는 4~150 m여야 합니다.")

    heights = [difference(station) for station in breakpoints]
    for station, height in zip(breakpoints, heights):
        validate(station, height)
    if profile.curves:
        # The height difference is at most quadratic between consecutive breakpoints.
        for a, b, za, zb in zip(breakpoints, breakpoints[1:], heights, heights[1:]):
            midpoint = difference((a+b)/2)
            quadratic = 2 * ((za-midpoint) + (zb-midpoint))
            if abs(quadratic) > 1e-10:
                ratio = (za-zb+quadratic)/(2*quadratic)
                if 0 < ratio < 1:
                    station = a + ratio*(b-a)
                    validate(station, difference(station))


def arch_span(length, rise, shape, hanger_count):
    """Return normalized rib samples and uniform hanger stations."""
    hangers = [index / (hanger_count + 1) for index in range(1, hanger_count + 1)]
    samples = [index / 12 for index in range(13)]
    if shape == "circular":
        half_span = length / 2
        radius = (half_span ** 2 + rise ** 2) / (2 * rise)
        half_angle = math.asin(min(1, half_span / radius))
        samples = [0, 1, *(0.5 + radius / length * math.sin(half_angle * (index / 6 - 1))
                           for index in range(1, 12))]

        def height(t):
            if t in (0, 1):
                return 0
            x = (t - .5) * length
            return math.sqrt(max(0, radius ** 2 - x ** 2)) - (radius - rise)
    else:
        def height(t):
            return 4 * rise * t * (1 - t)

    # Include hanger anchors in the rib tessellation, skipping coincident samples.
    fractions = sorted(hangers + [t for t in samples if all(abs(t-h) > 1e-10 for h in hangers)])
    return [(t, height(t)) for t in fractions], [(t, height(t)) for t in hangers]


def generate(config):
    if not isinstance(config, dict):
        raise ValueError("프로젝트는 JSON 객체여야 합니다.")
    kind = config.get("kind")
    if kind not in TYPES:
        raise ValueError("교량 형식을 선택하세요.")
    start = number(config.get("start"), -1e6, 1e6)
    width = number(config.get("width"), 5, 40)
    ground = number(config.get("ground"), -1000, 8000)
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
    parameters = {
        "slab_thickness": ("슬래브 두께", .35, .05, 3),
        "girder_depth": ("거더 형고", 1.7 if kind == "psc" else 2.2, .2, 15),
        "cap_depth": ("코핑 높이", .65, .05, 8),
        "bearing_height": ("받침 높이", .25, .05, 3),
        "foundation_depth": ("기초 두께", 2, .1, 15),
        "foundation_length": ("기초 길이", 5, .5, 50),
        "foundation_width": ("기초 폭", width * .8, .5, 80),
    }
    dimensions = {}
    for key, (label, default, low, high) in parameters.items():
        value = config.get(key)
        try:
            dimensions[key] = default if value is None else number(value, low, high)
        except ValueError as error:
            raise ValueError(f"{label} (m): {error}") from error

    foundation_half_length = dimensions["foundation_length"] / 2
    foundation_half_width = dimensions["foundation_width"] / 2
    end = stations[-1]
    radius = number(config.get("curve_radius", 0), -1e6, 1e6)
    cant = number(config.get("cant_mm", 0), 0, 200)
    cant_points = validate_profile(config.get("cant_profile", []), "측점별 캔트", 0, 200,
                                   extent=(start, end), value_label="캔트(mm)")
    plan_rows = validate_plan(config.get("plan_segments", []), start, end)
    if not plan_rows and radius and (abs(radius) < 60 or (end-start) / abs(radius) > math.pi / 2):
        raise ValueError("곡선 반경의 절댓값은 60 m 이상이며 교량 구간의 원호각은 90도 이하여야 합니다.")
    ground_points = validate_profile(config.get("ground_profile", []), "지반선", -1000, 8000, extent=(start, end))
    elevations = (-996, 8150) if ground_points else (ground + 4, ground + 150)
    deck = number(config.get("deck"), *elevations)
    girder_top = deck - dimensions["slab_thickness"]
    girder_bottom = girder_top - dimensions["girder_depth"]
    profile = validate_profile(config.get("profile", []), "종단 선형", *elevations, extent=(start, end))
    curves, curve_inputs = build_vertical_curves(config.get("vertical_curves", []), profile)
    alignment = Alignment(start, radius, cant, deck, profile, curves, cant_profile=cant_points, plan_rows=plan_rows)
    curved = alignment.has_curve
    zero_cant = set()
    for segment in alignment.plan:
        if segment.transition:
            if not segment.radius:
                zero_cant.add(segment.start)
            if not segment.end_radius:
                zero_cant.add(segment.end)
    for current, following in zip(alignment.plan, alignment.plan[1:]):
        if current.direction != following.direction:
            zero_cant.add(current.end)
    for station in sorted(zero_cant):
        if alignment.cant.at(station) > 1e-8:
            raise ValueError(f"측점 {station:g} m에서 직선과 접속하거나 곡선 방향이 바뀌므로 캔트는 0 mm여야 합니다.")
    terrain = StationProfile(ground_points, ground)
    if ground_points or curves:
        check_profile_height(alignment.profile, terrain, start, end)
    arch = None
    if kind == "arch":
        shape = config.get("arch_shape", "parabolic")
        if shape not in ("parabolic", "circular"):
            raise ValueError("아치 축선은 포물선 또는 원호를 선택하세요.")
        hanger_count = number(config.get("arch_hanger_count", 5), 1, 24)
        if hanger_count != int(hanger_count):
            raise ValueError("리브당 행어 수는 정수로 입력하세요.")
        arch = {
            "shape": shape,
            "rise": rise,
            "rib_thickness": number(config.get("arch_rib_thickness", .65), .05, 5),
            "hanger_count": int(hanger_count),
        }

    cables = None
    if kind in ("cable", "ed"):
        height = config.get("tower_height")
        height = (rise if kind == "cable" else rise * .5) if height is None else number(height, .5, 150)
        planes = number(config.get("cable_planes", 2), 1, 2)
        count = number(config.get("cable_count", 4), 1, 12)
        if planes != int(planes) or count != int(count):
            raise ValueError("케이블 면 수와 개수는 정수로 입력하세요.")
        near = number(config.get("anchor_start_pct", 25), 1, 99)
        far = number(config.get("anchor_end_pct", 85), 1, 99)
        if near >= far:
            raise ValueError("가까운 정착점 비율은 먼 정착점 비율보다 작아야 합니다.")
        cables = {"tower_height": height, "planes": int(planes), "count": int(count),
                  "anchor_start_pct": near, "anchor_end_pct": far}
        cable_offsets = [0] if planes == 1 else [-(half - .35), half - .35]
        anchor_fractions = [(near+far)/200] if count == 1 else [
            (near + (far-near)*i/(count-1))/100 for i in range(int(count))
        ]

    tower_ids = set()
    track_centers = {}
    box("슬래브", "deck", [start, -half, girder_top], [end, half, deck])
    for index, (a, b) in enumerate(zip(stations, stations[1:]), 1):
        offsets = [-.36 * width, -.12 * width, .12 * width, .36 * width] if kind == "psc" else [0]
        for offset in offsets:
            girder_half = .4 if kind == "psc" else width * .27
            if kind == "ed":
                girder_half = width * .31
            box(f"거더 S{index}", "girder", [a, offset - girder_half, girder_bottom],
                [b, offset + girder_half, girder_top])
        if kind == "ed":
            for x, y in ((a, a + (b-a)*.18), (b - (b-a)*.18, b)):
                beam(f"변단면 헌치 S{index}", "girder",
                     [x, 0, girder_bottom - .2], [y, 0, girder_bottom - .2], .4)
        if arch is not None:
            length = b - a
            if shape == "circular" and rise > length / 2:
                raise ValueError(f"원호 아치 S{index}의 라이즈는 경간의 절반({length / 2:g} m) 이하여야 합니다.")
            rib, hangers = arch_span(length, rise, shape, arch["hanger_count"])
            for side in (-1, 1):
                y = side * (half - .35)
                points = [[a + length*t, y, deck + height] for t, height in rib]
                for first, second in zip(points, points[1:]):
                    beam(f"아치 리브 S{index}", "special", first, second, arch["rib_thickness"])
                for t, height in hangers:
                    x = a + length*t
                    beam(f"행어 S{index}", "special", [x, y, deck], [x, y, deck+height], .16)
    for index, station in enumerate(stations):
        label = f"교대 A{1 if index == 0 else 2}" if index in (0, len(stations)-1) else f"교각 P{index}"
        support = girder_bottom + (alignment.elevation_at(station) - deck)
        base_ground = terrain.at(station)
        bearing_bottom = support - dimensions["bearing_height"]
        cap_bottom = bearing_bottom - dimensions["cap_depth"]
        if cap_bottom - base_ground <= 1e-8:
            raise ValueError(f"{label} 측점 {station:g} m에 몸체를 배치할 높이가 부족합니다. "
                             "부재 치수와 슬래브·지반 표고를 확인하세요.")
        box(f"{label} 기초", "foundation",
            [station-foundation_half_length, -foundation_half_width, base_ground-dimensions["foundation_depth"]],
            [station+foundation_half_length, foundation_half_width, base_ground])
        box(label, "pier", [station-1, -half*.46, base_ground], [station+1, half*.46, cap_bottom])
        box(f"{label} 코핑", "pier", [station-1.3, -half*.93, cap_bottom],
            [station+1.3, half*.93, bearing_bottom])
        for offset in offsets:
            box(f"{label} 받침", "bearing", [station-.35, offset-.35, bearing_bottom],
                [station+.35, offset+.35, support])
        if cables is not None and (0 < index < len(stations)-1 or len(stations) == 2):
            neighbors = stations[max(0,index-1):index] + stations[index+1:index+2]
            for y in cable_offsets:
                box(f"주탑 {index+1}", "special", [station-.5, y-.3, base_ground],
                    [station+.5, y+.3, alignment.elevation_at(station)+height])
                tower_ids.add(objects[-1]["id"])
                for neighbor in neighbors:
                    for fraction in anchor_fractions:
                        x = station + fraction*(neighbor-station)
                        beam("사장 케이블" if kind == "cable" else "외부 케이블",
                             "special", [station, y, deck+height*(.65+.35*fraction)], [x, y, deck], .14)
                        if curved or profile:
                            objects[-1]["chord"] = True
    accessories = {}
    for key, label in (("rail_side", "난간"), ("walkway_side", "점검통로"), ("drain_side", "배수관로")):
        placement = config.get(key, "both")
        if not isinstance(placement, str) or placement not in ACCESSORY_SIDES:
            raise ValueError(f"{label} 설치 방향을 선택하세요.")
        accessories[key] = placement

    for key, label, default, low, high in (
        ("railing_height", "난간 높이", 1.12, .2, 5),
        ("walkway_width", "점검통로 폭", .75, .2, 6),
        ("drain_diameter", "배수관 외경", .25, .05, 3),
        ("drain_drop", "배수관 중심 하향 거리", 1, 0, 20),
        ("drain_inset", "배수관 중심 안쪽 거리", width * .05, 0, half),
    ):
        value = config.get(key)
        try:
            accessories[key] = default if value is None else number(value, low, high)
        except ValueError as error:
            raise ValueError(f"{label} (m): {error}") from error

    walk_sides = ACCESSORY_SIDES[accessories["walkway_side"]]
    rail_sides = ACCESSORY_SIDES[accessories["rail_side"]]
    drain_sides = ACCESSORY_SIDES[accessories["drain_side"]]
    walkway_width = accessories["walkway_width"]
    rail_top = deck + accessories["railing_height"]
    drain_y = half - accessories["drain_inset"]
    drain_z = deck - accessories["drain_drop"]
    if len(drain_sides) == 2 and drain_y * 2 < accessories["drain_diameter"] - 1e-8:
        raise ValueError("양쪽 배수관이 겹칩니다. 배수관의 안쪽 거리나 외경을 줄이세요.")
    for side in (-1, 1):
        edge = side * half
        if side in walk_sides:
            lo, hi = sorted((edge, edge + side * walkway_width))
            box("점검통로", "accessory", [start, lo, deck-.18], [end, hi, deck+.05])
        if side in rail_sides:
            rail_y = edge + side * ((walkway_width if side in walk_sides else 0) - .05)
            for station in stations:
                box("난간 기둥", "accessory", [station-.06, rail_y-.06, deck],
                    [station+.06, rail_y+.06, rail_top-.02])
            box("난간", "accessory", [start, rail_y-.06, rail_top-.12], [end, rail_y+.06, rail_top])
        if side in drain_sides:
            beam("배수관로", "accessory", [start, side * drain_y, drain_z],
                 [end, side * drain_y, drain_z], accessories["drain_diameter"])
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
            objects[-1].update(category="gauge", required_clearance=0, clearance_mode="spatial")
            track_centers[objects[-1]["id"]] = offset
    obstacles = validate_obstacles(config.get("obstacles"))
    for obstacle in obstacles:
        box(obstacle["name"], "context", obstacle["min"], obstacle["max"], "obstacle")
        objects[-1].update(category=obstacle["category"],
                           required_clearance=obstacle.get("clearance", clearance),
                           clearance_mode=obstacle.get("clearance_mode", "spatial"))

    cells_by_id = {}
    station_ranges = {}
    if curved or profile:
        for item in objects:
            if item["role"] == "obstacle":
                continue
            follows = item["group"] not in ("foundation", "pier", "bearing") and item["id"] not in tower_ids
            if not curved and not follows:
                continue
            station_ranges[item["id"]] = (item["min"][0], item["max"][0])
            cells = list(alignment.cells(item, track_centers.get(item["id"]), follow_profile=follows))
            item["mesh"] = [cell[2] for cell in cells]
            item["min"], item["max"] = bounds(vertex for cell in cells for vertex in cell[2])
            if "axis" in item:
                item["axis"] = [alignment.point(point, follow_profile=follows) for point in item["axis"]]
            cells_by_id[item["id"]] = cells

    def cells(item):
        return cells_by_id.get(item["id"], [(item["min"], item["max"], None)])

    findings = []
    vertical_clearances = []
    parts = [item for item in objects if item["role"] == "bridge"]
    for target in objects:
        if target["role"] == "bridge":
            continue
        limit = target["required_clearance"]
        mode = target["clearance_mode"]
        vertical = mode == "vertical"
        measure = vertical_separation if vertical else separation
        violation_threshold = max(limit, 1e-8)
        zone_minimum = math.inf
        controlling = None
        target_cells = cells(target)
        for part in parts:
            threshold = max(violation_threshold, zone_minimum) if vertical else violation_threshold
            if measure(part["min"], part["max"], target["min"], target["max"]) > threshold:
                continue
            best = math.inf
            center = None
            for lo, hi, _ in cells(part):
                if measure(lo, hi, target["min"], target["max"]) > min(best, threshold):
                    continue
                for t_lo, t_hi, _ in target_cells:
                    gap = measure(lo, hi, t_lo, t_hi)
                    if gap < best:
                        best = gap
                        center = [(max(a, min(b, c)) + max(a, min(b, d))) / 2
                                  for a, b, c, d in zip(lo, hi, t_lo, t_hi)]
            if center is None:
                continue
            violation = best <= 1e-8 or best < limit
            new_minimum = vertical and best < zone_minimum
            if not violation and not new_minimum:
                continue
            if not violation:
                status = "충족"
            elif best < -1e-8:
                status = "중첩"
            elif best <= 1e-8:
                status = "접촉"
            else:
                status = "이격 미달"
            approximate = "axis" in part or "mesh" in part or "mesh" in target
            if approximate:
                status += " 후보 (외접 상자)" if violation else " (외접 상자)"
            station = alignment.station_at(center)
            if part["id"] in station_ranges:
                lo_station, hi_station = station_ranges[part["id"]]
                station = max(lo_station, min(hi_station, station))
            entry = {
                "part": part["id"], "target": target["id"], "status": status,
                "station": round(station, 3), "category": target["category"],
                "approximate": approximate, "distance": round(best if vertical else max(0, best), 4),
                "required": limit, "clearance_mode": mode, "point": center,
            }
            if violation:
                findings.append(entry)
            if new_minimum:
                zone_minimum = best
                controlling = entry
        if vertical:
            vertical_clearances.append(controlling or {
                "target": target["id"], "category": target["category"], "required": limit,
                "status": "해당 부재 없음", "part": None, "station": None, "distance": None,
            })
    count = max(1, math.ceil((end - start) / 5)) if curved else 1
    ground_stations = sorted({start, end, *stations, *alignment.plan_breaks,
                              *(start + (end - start) * step / count for step in range(1, count)),
                              *(s for s in terrain.stations if start < s < end)})
    ground_line = [alignment.point([s, 0, terrain.at(s)], follow_profile=False)
                   for s in ground_stations]
    return {"objects": objects, "findings": findings, "vertical_clearances": vertical_clearances,
            "stations": stations,
            "length": end-start, "kind": TYPES[kind],
            "ground_line": ground_line,
            "ground_profile": ground_points, "target_categories": TARGET_CATEGORIES,
            "dimensions": dimensions, "accessories": accessories, "arch": arch, "cables": cables,
            "alignment": {"curve_radius": radius, "cant_mm": cant, "profile": profile,
                          "vertical_curves": curve_inputs, "cant_profile": cant_points,
                          "plan_segments": plan_rows},
            "missing": [] if obstacles else ["외부 지장물 데이터 미입력"]}
