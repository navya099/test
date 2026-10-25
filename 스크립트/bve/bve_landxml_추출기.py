import csv
import xml.etree.ElementTree as ET
import math
import numpy as np
from enum import Enum

class CurveDirection(Enum):
    """곡선 방향 클래스"""
    LEFT = 0
    RIGHT = 1
    NULL = 2


def calculate_simple_curve_geometry(radius: float, cl: float) -> tuple:
    """R과 CL로 단곡선 제원 계산"""
    r = abs(radius)  # 곡선반경
    ia = cl / r  # 교각 (라디안)
    tl = r * math.tan(ia / 2)  # 접선장
    m = r * (1 - math.cos(ia / 2))  # 중앙종거
    sl = r * (1 / math.cos(ia / 2) - 1)  # 외거

    return r, ia, tl, m, sl

def _to_xy(p):
    """다양한 타입을 (x, y) 튜플로 변환"""
    if hasattr(p, "x") and hasattr(p, "y"):
        return float(p.x), float(p.y)

    if isinstance(p, (tuple, list, np.ndarray)) and len(p) >= 2:
        return float(p[0]), float(p[1])

    raise TypeError(f"Unsupported type {type(p)}")


def intersection_of_two_lines(p1: any, angle1_deg: float, p2: any, angle2_deg: float) -> tuple[float, float]:
    """두 점과 각도(도 단위)로 정의된 직선의 교점 계산"""
    p1 = _to_xy(p1)
    p2 = _to_xy(p2)

    # 도(Degree)를 라디안(Radian)으로 변환 후 기울기 계산
    m1 = math.tan(math.radians(angle1_deg))
    b1 = p1[1] - m1 * p1[0]

    m2 = math.tan(math.radians(angle2_deg))
    b2 = p2[1] - m2 * p2[0]

    if math.isclose(m1, m2):
        return None  # 평행이면 교점 없음

    x = (b2 - b1) / (m1 - m2)
    y = m1 * x + b1
    return x, y

def calculate_curve_center(bc, ec, radius: float, direction: CurveDirection) -> tuple[float, float]:
    """두 점(BC, EC)과 반지름, 방향으로 원의 중심 좌표 계산"""
    bc = _to_xy(bc)
    ec = _to_xy(ec)
    dx = ec[0] - bc[0]
    dy = ec[1] - bc[1]
    d = math.hypot(dx, dy)

    if d == 0 or d > 2 * abs(radius):
        raise ValueError("Invalid BC/EC distance for given radius")

    # 중점
    mx = (bc[0] + ec[0]) / 2
    my = (bc[1] + ec[1]) / 2

    # chord의 수직거리 h
    h = math.sqrt(radius ** 2 - (d / 2) ** 2)

    # 단위 수직벡터
    ux = -dy / d
    uy = dx / d

    # 방향 선택 (1=RIGHT, 0=LEFT)
    sign = -1 if direction == CurveDirection.RIGHT else 1

    # 중심 좌표 계산
    cx = mx + sign * ux * h
    cy = my + sign * uy * h

    return cx, cy

def convert_csv_to_landxml(csv_path: str, xml_path: str):
    # 1. XML Root 및 기본 구조 생성
    root = ET.Element("LandXML", {
        "version": "1.2",
        "xmlns": "http://www.landxml.org/schema/LandXML-1.2"
    })

    units = ET.SubElement(root, "Units")
    ET.SubElement(units, "Metric", {
        "areaUnit": "squareMeter",
        "linearUnit": "meter",
        "volumeUnit": "cubicMeter",
        "temperatureUnit": "celsius",
        "pressureUnit": "milliBars",
        "diameterUnit": "millimeter",
        "angularUnit": "decimal degrees",
        "directionUnit": "decimal degrees"
    })

    alignments = ET.SubElement(root, "Alignments", {"name": ""})
    alignment = ET.SubElement(alignments, "Alignment", {
        "name": "VermouteExportedRoute",
        "length": "4",
        "staStart": "0.",
        "desc": "",
    })
    coord_geom = ET.SubElement(alignment, "CoordGeom")

    # 2. CSV 읽기
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # 3. 데이터 순회하며 Line 또는 Curve(Arc) 생성
    for i in range(len(rows) - 1):
        p1 = rows[i]
        p2 = rows[i + 1]

        radius = float(p1.get("radius", 0.0))
        sta_start = str(p1["starting_distance"])
        start_dir_x = float(p1["direction_x"])
        start_dir_y = float(p1["direction_y"])
        end_dir_x = float(p2["direction_x"])
        end_dir_y = float(p2["direction_y"])

        # 방위각 계산 (도 단위 문자열)
        start_azimuth_deg = math.degrees(math.atan2(start_dir_y, start_dir_x))
        end_azimuth_deg = math.degrees(math.atan2(end_dir_y, end_dir_x))

        # 💡 직선 구간 판단
        if abs(radius) == 0.0 or abs(radius) > 900000.0:
            line_elem = ET.SubElement(coord_geom, "Line", {"dir": str(start_azimuth_deg), "length": '25.0'})

            start_pt = ET.SubElement(line_elem, "Start")
            start_pt.text = f"{float(p1['y'])} {float(p1['x'])}"

            end_pt = ET.SubElement(line_elem, "End")
            end_pt.text = f"{float(p2['y'])} {float(p2['x'])}"

        # 💡 곡선(Arc) 구간 판단
        else:
            rot = "cw" if radius > 0 else "ccw"
            curve_direction = CurveDirection.RIGHT if radius > 0 else CurveDirection.LEFT
            abs_radius = abs(radius)
            r, ia, tl, m, sl = calculate_simple_curve_geometry(abs_radius, 25.0)

            # 좌표값을 미리 float로 변환
            p1_x, p1_y = float(p1['x']), float(p1['y'])
            p2_x, p2_y = float(p2['x']), float(p2['y'])

            # 💡 현의 길이(Chord) 계산 (시작점과 끝점 사이의 직선 거리)
            chord_length = math.hypot(p2_x - p1_x, p2_y - p1_y)

            curve_elem = ET.SubElement(coord_geom, "Curve", {
                "rot": rot,
                "chord": str(chord_length),
                "crvType": "arc",
                "delta": str(math.degrees(ia)),
                "dirEnd": str(end_azimuth_deg),
                "dirStart": str(start_azimuth_deg),
                "external": str(sl),
                "midOrd": str(m),
                "length": str(25.0),
                "radius": str(abs_radius),
                "tangent": str(tl)
            })

            # 좌표값을 float로 명시적 변환하여 전달
            p1_xy = (float(p1['x']), float(p1['y']))
            p2_xy = (float(p2['x']), float(p2['y']))

            pi = intersection_of_two_lines(p1=p1_xy, angle1_deg=start_azimuth_deg, p2=p2_xy, angle2_deg=end_azimuth_deg)
            bc = p1_xy
            ec = p2_xy
            center = calculate_curve_center(bc=bc, ec=ec, radius=radius, direction=curve_direction)

            start_pt = ET.SubElement(curve_elem, "Start")
            start_pt.text = f"{float(p1['y'])} {float(p1['x'])}"

            center_pt = ET.SubElement(curve_elem, "Center")
            center_pt.text = f"{center[1]} {center[0]}"

            end_pt = ET.SubElement(curve_elem, "End")
            end_pt.text = f"{float(p2['y'])} {float(p2['x'])}"

            pi_pt = ET.SubElement(curve_elem, "PI")
            if pi:
                pi_pt.text = f"{pi[1]} {pi[0]}"
            else:
                pi_pt.text = "0.0 0.0"

    # 4. XML 파일 저장
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    print(f"[Vermoute] LandXML (Line & Curve 혼합) 변환 완료: {xml_path}")

if __name__ == '__main__':
    convert_csv_to_landxml('c:/temp/vermoute_output/alignment.csv', 'c:/temp/vermoute_output/alignment.xml')