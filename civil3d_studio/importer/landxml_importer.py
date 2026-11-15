import xml.etree.ElementTree as ET
from typing import Tuple, Dict, List

from alignment.pipoint import PIPoint
from profile.pvi import PVIPoint


class LandXMLImporter:
    """
    Civil 3D LandXML(.xml) 파서
    - <Alignment>/<CoordGeom>에서 직선 접선 교차 연산을 통해 PI 좌표(Easting, Northing) 및 R, L1, L2 역산
    - <Profile>/<ProfAlign>에서 PVI 측점, 계획고, 종단곡선 길이 추출
    - <StaEquation>에서 파정(Station Equation) 추출
    """
    @staticmethod
    def _strip_ns(tag: str) -> str:
        return tag.split("}", 1)[-1] if "}" in tag else tag

    @staticmethod
    def _parse_xy(text: str) -> Tuple[float, float]:
        # LandXML <Start>, <End>, <PI>, <PVI>는 표준적으로 "Northing Easting" 순서로 기록됨
        parts = [float(v) for v in text.strip().split()]
        return parts[1], parts[0]  # (Easting, Northing) 반환

    @staticmethod
    def _line_intersection(p1, d1, p2, d2) -> Tuple[float, float]:
        """두 접선 직선의 교점(PI) 좌표 산출"""
        det = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(det) < 1e-10:
            return (p1[0] + p2[0]) * 0.5, (p1[1] + p2[1]) * 0.5
        t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / det
        return p1[0] + t * d1[0], p1[1] + t * d1[1]

    @classmethod
    def parse_file(cls, filepath: str) -> Dict:
        tree = ET.parse(filepath)
        root = tree.getroot()

        # 첫 번째 <Alignment> 탐색
        align_elem = None
        for elem in root.iter():
            if cls._strip_ns(elem.tag) == "Alignment":
                align_elem = elem
                break
        if align_elem is None:
            raise ValueError("LandXML 파일 내에 <Alignment> 요소가 없습니다.")

        align_name = align_elem.attrib.get("name", "LandXML_Alignment")
        start_sta = float(align_elem.attrib.get("staStart", 0.0))

        # 1. 파정(<StaEquation>) 추출
        equations = []
        for child in align_elem:
            if cls._strip_ns(child.tag) == "StaEquation":
                s_back = float(child.attrib.get("staBack", 0.0))
                s_ahead = float(child.attrib.get("staAhead", 0.0))
                equations.append((s_back, s_ahead))

        # 2. 평면 기하(<CoordGeom>) 요소 추출 -> PI 및 R, L1, L2 역산
        geom_items = []
        for child in align_elem:
            if cls._strip_ns(child.tag) == "CoordGeom":
                for g in child:
                    gtag = cls._strip_ns(g.tag)
                    if gtag in ("Line", "Curve", "Spiral"):
                        s_pt, e_pt = None, None
                        for sub in g:
                            stag = cls._strip_ns(sub.tag)
                            if stag == "Start" and sub.text:
                                s_pt = cls._parse_xy(sub.text)
                            elif stag == "End" and sub.text:
                                e_pt = cls._parse_xy(sub.text)
                        length = float(g.attrib.get("length", 0.0))
                        radius = float(g.attrib.get("radius", 0.0)) if g.attrib.get("radius") not in (None, "INF", "inf") else 0.0
                        if radius == 0.0 and gtag == "Spiral":
                            r_s = g.attrib.get("radiusStart", "INF")
                            r_e = g.attrib.get("radiusEnd", "INF")
                            r1 = 0.0 if r_s.upper() == "INF" else float(r_s)
                            r2 = 0.0 if r_e.upper() == "INF" else float(r_e)
                            radius = max(r1, r2)
                        geom_items.append({"type": gtag, "start": s_pt, "end": e_pt, "length": length, "radius": radius})

        pis: List[PIPoint] = []
        if geom_items:
            bp = geom_items[0]["start"]
            pis.append(PIPoint("BP", bp[0], bp[1], 0.0, 0.0, 0.0))

            # 직선(Line) 세그먼트들을 기준으로 인접 두 직선의 교점(PI) 및 사이의 곡선 제원(R, L1, L2) 그룹핑
            line_indices = [idx for idx, item in enumerate(geom_items) if item["type"] == "Line"]
            for k in range(len(line_indices) - 1):
                i1, i2 = line_indices[k], line_indices[k + 1]
                l_prev, l_next = geom_items[i1], geom_items[i2]

                d1 = (l_prev["end"][0] - l_prev["start"][0], l_prev["end"][1] - l_prev["start"][1])
                d2 = (l_next["end"][0] - l_next["start"][0], l_next["end"][1] - l_next["start"][1])
                pi_e, pi_n = cls._line_intersection(l_prev["end"], d1, l_next["start"], d2)

                # 두 직선 사이에 끼어 있는 완화곡선/원곡선 제원 추출
                between = geom_items[i1 + 1 : i2]
                spirals = [b["length"] for b in between if b["type"] == "Spiral"]
                arcs = [b["radius"] for b in between if b["type"] == "Curve"]

                R = arcs[0] if arcs else 0.0
                L1 = spirals[0] if len(spirals) >= 1 else 0.0
                L2 = spirals[1] if len(spirals) >= 2 else (0.0 if len(spirals) == 1 else 0.0)
                pis.append(PIPoint(f"IP-{k + 1}", pi_e, pi_n, R, L1, L2))

            ep = geom_items[-1]["end"]
            pis.append(PIPoint("EP", ep[0], ep[1], 0.0, 0.0, 0.0))

        # 3. 종단 선형(<Profile>/<ProfAlign>) 추출
        pvis: List[PVIPoint] = []
        for elem in align_elem.iter():
            if cls._strip_ns(elem.tag) == "ProfAlign":
                pvi_nodes = []
                for sub in elem:
                    stag = cls._strip_ns(sub.tag)
                    if stag in ("PVI", "ParaCurve", "UnsymParaCurve", "CircCurve") and sub.text:
                        vals = [float(v) for v in sub.text.strip().split()]
                        # LandXML PVI 텍스트 형식: "Station Elevation" (물리 측점으로 정규화)
                        raw_s = vals[0] - start_sta
                        el = vals[1]
                        l1 = l2 = 0.0
                        if stag in ("ParaCurve", "CircCurve"):
                            tot_l = float(sub.attrib.get("length", 0.0))
                            l1 = l2 = tot_l * 0.5
                        elif stag == "UnsymParaCurve":
                            l1 = float(sub.attrib.get("lengthIn", 0.0))
                            l2 = float(sub.attrib.get("lengthOut", 0.0))
                        pvi_nodes.append((stag, raw_s, el, l1, l2))

                for idx, (stag, raw_s, el, l1, l2) in enumerate(pvi_nodes):
                    name = "BVP" if idx == 0 else ("EVP" if idx == len(pvi_nodes) - 1 else f"PVI-{idx}")
                    pvis.append(PVIPoint(name, max(0.0, raw_s), el, L1=l1, L2=l2))
                break

        return {
            "name": align_name,
            "start_station": start_sta,
            "equations": equations,
            "pis": pis,
            "pvis": pvis
        }
