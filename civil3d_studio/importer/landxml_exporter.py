import xml.etree.ElementTree as ET
from typing import Tuple, Dict, List

from alignment.alignment import Alignment
from alignment.arc import ArcSegment
from alignment.japancubic import JapaneseCubicSpiralSegment
from alignment.pipoint import PIPoint
from alignment.station.equation_manager import StationEquationManager
from profile.profile import Profile
from profile.pvi import PVIPoint
from alignment.line import LineSegment

class LandXMLExporter:
    """
    Civil 3D 표준 LandXML 1.2(.xml) 내보내기 엔진
    - 평면 선형(<Alignment>/<CoordGeom>: Line, Spiral, Curve) 생성 (Northing Easting 표준 순서 준수)
    - 파정(<StaEquation>) 및 종단 선형(<Profile>/<ProfAlign>: PVI, ParaCurve, UnsymParaCurve) 생성
    """
    @classmethod
    def export_file(cls, filepath: str, h_align: Alignment, v_prof: Profile, sta_mgr: StationEquationManager):
        # 1. LandXML 루트 및 표준 메타데이터 구성
        from datetime import datetime
        now = datetime.now()
        root = ET.Element("LandXML", {
            # ✅ 수정
            "xmlns": "http://www.landxml.org/schema/LandXML-1.2",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:schemaLocation": "http://www.landxml.org/schema/LandXML-1.2 http://www.landxml.org/schema/LandXML-1.2/LandXML-1.2.xsd",
            "version": "1.2",

            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            })
        units = ET.SubElement(root, "Units")
        ET.SubElement(units, "Metric", {
            "areaUnit": "squareMeter",
            "linearUnit": "meter",
            "volumeUnit": "cubicMeter",
            "temperatureUnit": "celsius",
            "pressureUnit": "milliBars",
            "angularUnit": "decimal degrees",
            "directionUnit": "decimal degrees"
        })

        alignments = ET.SubElement(root, "Alignments")
        align_el = ET.SubElement(alignments, "Alignment", {
            "name": h_align.name,
            "length": f"{h_align.total_length:.6f}",
            "staStart": f"{sta_mgr.start_station:.6f}",
            "state": "proposed"
        })

        # 2. 파정 (<StaEquation>) 기록
        equations = getattr(sta_mgr, "equations", [])
        for eq in equations:
            # dataclass 또는 tuple 지원
            if hasattr(eq, "station_ahead"):
                ahead = eq.station_ahead
                back = eq.station_back
                raw = eq.raw_station
            else:
                back, ahead, raw = eq  # tuple 폴백
            ET.SubElement(align_el, "StaEquation", {
                "staAhead": f"{ahead:.6f}",
                "staBack": f"{back:.6f}",
                "staInternal": f"{sta_mgr.start_station + raw:.6f}"
            })

        # 3. 평면 기하 요소 (<CoordGeom>: Line, Spiral, Curve) 기록
        coord_geom = ET.SubElement(align_el, "CoordGeom")
        for ent in h_align.entities:
            se, sn = ent.start_e, ent.start_n
            ee, en, end_ang, _ = ent.end_pose
            # LandXML 표준 좌표 순서: "Northing Easting"
            start_str = f"{sn:.6f} {se:.6f}"
            end_str = f"{en:.6f} {ee:.6f}"
            import math
            dir_deg = (90.0 - math.degrees(ent.start_angle)) % 360.0


            if isinstance(ent, LineSegment):
                line_el = ET.SubElement(coord_geom, "Line", {
                    "dir": f"{dir_deg:.6f}",
                    "length": f"{ent.length:.6f}"
                })
                ET.SubElement(line_el, "Start").text = start_str
                ET.SubElement(line_el, "End").text = end_str

            elif isinstance(ent, ArcSegment):
                rot = "ccw" if ent.dir > 0 else "cw"
                curve_el = ET.SubElement(coord_geom, "Curve", {
                    "rot": rot,
                    "crvType": "arc",
                    "length": f"{ent.length:.6f}",
                    "radius": f"{ent.R:.6f}",
                    "delta": f"{math.degrees(abs(ent.sweep_angle)):.6f}"
                })
                ET.SubElement(curve_el, "Start").text = start_str
                ET.SubElement(curve_el, "Center").text = f"{ent.center_n:.6f} {ent.center_e:.6f}"
                ET.SubElement(curve_el, "End").text = end_str

            elif isinstance(ent, JapaneseCubicSpiralSegment):
                rot = "ccw" if ent.turn_dir > 0 else "cw"
                r_start = f"{ent.R:.6f}" if ent.is_exit else "INF"
                r_end = "INF" if ent.is_exit else f"{ent.R:.6f}"
                spiral_el = ET.SubElement(coord_geom, "Spiral", {
                    "length": f"{ent.L:.6f}",
                    "radiusStart": r_start,
                    "radiusEnd": r_end,
                    "rot": rot,
                    "spiType": "japaneseCubic"
                })
                ET.SubElement(spiral_el, "Start").text = start_str
                # 완화곡선 접선 교점(PI) 근사 좌표 산출
                t_len = ent.L * 0.5
                pi_e = se + t_len * math.cos(ent.start_angle)
                pi_n = sn + t_len * math.sin(ent.start_angle)
                ET.SubElement(spiral_el, "PI").text = f"{pi_n:.6f} {pi_e:.6f}"
                ET.SubElement(spiral_el, "End").text = end_str

        # 4. 종단 선형 (<Profile>/<ProfAlign>: PVI, ParaCurve, UnsymParaCurve) 기록
        if v_prof and len(v_prof.pvi_list) >= 2:
            profile_el = ET.SubElement(align_el, "Profile", {"name": f"{h_align.name}_FG"})
            prof_align = ET.SubElement(profile_el, "ProfAlign", {"name": f"{h_align.name}_Layout"})

            for idx, pvi in enumerate(v_prof.pvi_list):
                pvi_sta_val = sta_mgr.start_station + pvi.station
                pt_text = f"{pvi_sta_val:.6f} {pvi.elevation:.6f}"

                if idx == 0 or idx == len(v_prof.pvi_list) - 1:
                    ET.SubElement(prof_align, "PVI").text = pt_text
                    continue

                l1 = float(pvi.L1) if pvi.L1 is not None else (float(pvi.L) * 0.5 if pvi.L else 0.0)
                l2 = float(pvi.L2) if pvi.L2 is not None else (float(pvi.L) * 0.5 if pvi.L else 0.0)

                if l1 + l2 <= 1e-6:
                    ET.SubElement(prof_align, "PVI").text = pt_text
                elif abs(l1 - l2) <= 1e-6:
                    ET.SubElement(prof_align, "ParaCurve", {"length": f"{l1 + l2:.6f}"}).text = pt_text
                else:
                    ET.SubElement(prof_align, "UnsymParaCurve", {
                        "lengthIn": f"{l1:.6f}",
                        "lengthOut": f"{l2:.6f}"
                    }).text = pt_text

        # 들여쓰기 정렬(Python 3.9+ ET.indent) 후 UTF-8 XML 파일 저장
        if hasattr(ET, "indent"):
            ET.indent(root, space="  ")
        tree = ET.ElementTree(root)
        tree.write(filepath, encoding="utf-8", xml_declaration=True)
