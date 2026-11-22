import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from tps_engine import TrainSpec, AdvancedUrbanTPS


@dataclass
class LandXMLSummary:
    alignment_name: str
    length_m: float
    sta_start: float
    coord_geom_count: int
    pvi_count: int
    min_radius_m: float
    min_gradient_permille: float
    max_gradient_permille: float
    design_speeds: List[Tuple[float, float]]


def _strip_ns(tag: str) -> str:
    """XML 네임스페이스 제거"""
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _parse_radius(val: str) -> float:
    if not val or val.strip().upper() == "INF":
        return float("inf")
    r = abs(float(val))
    return r if r > 0 else float("inf")


def _parse_coord_geom(coord_geom_elem: ET.Element, sta_start: float, total_len_m: int) -> Tuple[List[float], int]:
    """<CoordGeom>의 Line, Curve, Spiral을 1m 격자 곡률반경(curve_r) 배열로 변환"""
    curve_r = [float("inf")] * (total_len_m + 1)
    cursor = 0.0
    elem_count = 0

    for child in coord_geom_elem:
        tag = _strip_ns(child.tag)
        if tag not in ("Line", "Curve", "Spiral"):
            continue
        elem_count += 1

        seg_len = float(child.attrib.get("length", 0.0))
        if "staStart" in child.attrib:
            seg_start = float(child.attrib["staStart"]) - sta_start
        else:
            seg_start = cursor
        seg_end = seg_start + seg_len
        cursor = seg_end

        x_start = max(0, int(math.floor(seg_start)))
        x_end = min(total_len_m, int(math.ceil(seg_end)))

        if tag == "Line":
            for x in range(x_start, x_end + 1):
                curve_r[x] = float("inf")

        elif tag == "Curve":
            r = _parse_radius(child.attrib.get("radius", "INF"))
            for x in range(x_start, x_end + 1):
                curve_r[x] = r

        elif tag == "Spiral":
            r_start = _parse_radius(child.attrib.get("radiusStart", "INF"))
            r_end = _parse_radius(child.attrib.get("radiusEnd", "INF"))
            k_start = 0.0 if math.isinf(r_start) else 1.0 / r_start
            k_end = 0.0 if math.isinf(r_end) else 1.0 / r_end

            for x in range(x_start, x_end + 1):
                if seg_len <= 0:
                    ratio = 0.0
                else:
                    ratio = max(0.0, min(1.0, (x - seg_start) / seg_len))
                k = k_start + ratio * (k_end - k_start)
                curve_r[x] = (1.0 / k) if k > 1e-9 else float("inf")

    return curve_r, elem_count


def _parse_prof_align(prof_align_elem: ET.Element, sta_start: float, total_len_m: int) -> Tuple[List[float], int]:
    """<ProfAlign>의 PVI 및 ParaCurve를 1m 격자 구배(‰) 배열로 변환"""
    pvis: List[Tuple[float, float, float]] = []  # (dist_m, elev_m, vc_len_m)

    for child in prof_align_elem:
        tag = _strip_ns(child.tag)
        if tag not in ("PVI", "ParaCurve"):
            continue
        text = (child.text or "").strip()
        if not text:
            continue
        parts = text.split()
        sta = float(parts[0]) - sta_start
        elev = float(parts[1])
        vc_len = float(child.attrib.get("length", 0.0)) if tag == "ParaCurve" else 0.0
        pvis.append((sta, elev, vc_len))

    gradient = [0.0] * (total_len_m + 1)
    if len(pvis) < 2:
        return gradient, len(pvis)

    # 각 직선 구간 구배(‰) 계산
    seg_grades: List[float] = []
    for i in range(len(pvis) - 1):
        ds = pvis[i + 1][0] - pvis[i][0]
        de = pvis[i + 1][1] - pvis[i][1]
        g = (de / ds) * 1000.0 if abs(ds) > 1e-6 else 0.0
        seg_grades.append(g)

    # 기본 직선 구배 채우기
    for i in range(len(pvis) - 1):
        x0 = max(0, int(math.floor(pvis[i][0])))
        x1 = min(total_len_m, int(math.ceil(pvis[i + 1][0])))
        for x in range(x0, x1 + 1):
            gradient[x] = seg_grades[i]

    # 종단곡선(ParaCurve) 구간 선형 구배 보간
    for i in range(1, len(pvis) - 1):
        sta_i, _, vc_len = pvis[i]
        if vc_len <= 0:
            continue
        vc_start = sta_i - vc_len / 2.0
        vc_end = sta_i + vc_len / 2.0
        g_in = seg_grades[i - 1]
        g_out = seg_grades[i]

        x0 = max(0, int(math.floor(vc_start)))
        x1 = min(total_len_m, int(math.ceil(vc_end)))
        for x in range(x0, x1 + 1):
            ratio = max(0.0, min(1.0, (x - vc_start) / vc_len))
            gradient[x] = g_in + ratio * (g_out - g_in)

    return gradient, len(pvis)


def _parse_design_speeds(alignment_elem: ET.Element, sta_start: float) -> List[Tuple[float, float]]:
    """Civil 3D <Feature name='SpeedStation'> 또는 <DesignSpeed> 파싱"""
    speeds: List[Tuple[float, float]] = []

    for child in alignment_elem:
        tag = _strip_ns(child.tag)
        if tag == "Feature" and child.attrib.get("name") == "SpeedStation":
            props = {
                p.attrib.get("label"): p.attrib.get("value")
                for p in child
                if _strip_ns(p.tag) == "Property"
            }
            if "station" in props and "speed" in props:
                speeds.append((float(props["station"]) - sta_start, float(props["speed"])))
        elif tag == "DesignSpeed":
            if "station" in child.attrib and "speed" in child.attrib:
                speeds.append((float(child.attrib["station"]) - sta_start, float(child.attrib["speed"])))

    speeds.sort(key=lambda item: item[0])
    return speeds


def load_landxml_to_tps(
    xml_path: str,
    train: TrainSpec,
    alignment_name: Optional[str] = None,
    curve_speed_factor: Optional[float] = 4.5,
    apply_design_speed: bool = True,
) -> Tuple[AdvancedUrbanTPS, LandXMLSummary]:
    """
    LandXML 파일을 읽어 AdvancedUrbanTPS 인스턴스와 선형 요약 정보를 반환합니다.

    - curve_speed_factor: 곡선 제한속도 자동 산출 계수 (V_max = factor * sqrt(R), None이면 미적용)
    - apply_design_speed: XML 내 설계속도(SpeedStation)를 speed_limit에 반영할지 여부
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    alignments = [el for el in root.iter() if _strip_ns(el.tag) == "Alignment"]
    if not alignments:
        raise ValueError("LandXML 파일에 <Alignment> 요소가 없습니다.")

    target_align = alignments[0]
    if alignment_name:
        matched = [a for a in alignments if a.attrib.get("name") == alignment_name]
        if not matched:
            raise ValueError(f"선형 '{alignment_name}'을(를) 찾을 수 없습니다.")
        target_align = matched[0]

    align_name = target_align.attrib.get("name", "Unnamed")
    sta_start = float(target_align.attrib.get("staStart", 0.0))
    length_m = float(target_align.attrib.get("length", 0.0))
    total_len_m = int(round(length_m))

    tps = AdvancedUrbanTPS(train, total_length_m=total_len_m)

    # 1. 평면선형 파싱
    coord_count = 0
    for child in target_align:
        if _strip_ns(child.tag) == "CoordGeom":
            tps.curve_r, coord_count = _parse_coord_geom(child, sta_start, total_len_m)
            break

    # 2. 종단선형 파싱
    pvi_count = 0
    for child in target_align:
        if _strip_ns(child.tag) == "Profile":
            for sub in child:
                if _strip_ns(sub.tag) == "ProfAlign":
                    tps.gradient, pvi_count = _parse_prof_align(sub, sta_start, total_len_m)
                    break
            break

    # 3. 설계속도 반영
    design_speeds = _parse_design_speeds(target_align, sta_start)
    if apply_design_speed and design_speeds:
        for i, (s_dist, spd) in enumerate(design_speeds):
            next_dist = design_speeds[i + 1][0] if i + 1 < len(design_speeds) else total_len_m
            x0 = max(0, int(math.floor(s_dist)))
            x1 = min(total_len_m, int(math.ceil(next_dist)))
            for x in range(x0, x1 + 1):
                tps.speed_limit[x] = min(tps.speed_limit[x], spd)

    # 4. 곡선 반경 기반 제한속도 오버레이
    if curve_speed_factor is not None:
        for x in range(total_len_m + 1):
            r = tps.curve_r[x]
            if not math.isinf(r) and r > 0:
                v_curve = round(curve_speed_factor * math.sqrt(r), 1)
                tps.speed_limit[x] = min(tps.speed_limit[x], v_curve)

    finite_radii = [r for r in tps.curve_r if not math.isinf(r)]
    summary = LandXMLSummary(
        alignment_name=align_name,
        length_m=length_m,
        sta_start=sta_start,
        coord_geom_count=coord_count,
        pvi_count=pvi_count,
        min_radius_m=min(finite_radii) if finite_radii else float("inf"),
        min_gradient_permille=round(min(tps.gradient), 2),
        max_gradient_permille=round(max(tps.gradient), 2),
        design_speeds=design_speeds,
    )
    return tps, summary