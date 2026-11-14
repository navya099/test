from typing import Dict, List, Tuple


class DXFExporter:
    @staticmethod
    def export_dxf_3d(filepath: str, feature_lines: Dict[str, List[Tuple[float, float, float]]],
                      labels: List[Tuple[float, float, str]]):
        """
        외부 라이브러리 없이 순수 Python으로 AutoCAD / Civil 3D 호환 3D POLYLINE DXF 파일 생성
        """
        lines = [
            "0", "SECTION", "2", "HEADER", "0", "ENDSEC",
            "0", "SECTION", "2", "TABLES",
            "0", "TABLE", "2", "LAYER",
            # 레이어 정의: 중심선(빨강=1), 차선/길어깨(노랑=2), 법면(녹색=3), 측점텍스트(하늘=4)
            "0", "LAYER", "2", "CL_3D", "70", "0", "62", "1", "6", "CONTINUOUS",
            "0", "LAYER", "2", "ROAD_EDGE_3D", "70", "0", "62", "2", "6", "CONTINUOUS",
            "0", "LAYER", "2", "DAYLIGHT_3D", "70", "0", "62", "3", "6", "CONTINUOUS",
            "0", "LAYER", "2", "STATION_LABELS", "70", "0", "62", "4", "6", "CONTINUOUS",
            "0", "ENDTAB", "0", "ENDSEC",
            "0", "SECTION", "2", "ENTITIES"
        ]

        # 3D POLYLINE (그룹코드 70 = 8 -> 3D Polyline 플래그) 작도
        for code, pts in feature_lines.items():
            if code == "CL":
                layer = "CL_3D"
            elif "Daylight" in code:
                layer = "DAYLIGHT_3D"
            else:
                layer = "ROAD_EDGE_3D"

            lines.extend(["0", "POLYLINE", "8", layer, "66", "1", "70", "8", "10", "0.0", "20", "0.0", "30", "0.0"])
            for x, y, z in pts:
                lines.extend([
                    "0", "VERTEX", "8", layer, "70", "32",
                    "10", f"{x:.6f}", "20", f"{y:.6f}", "30", f"{z:.6f}"
                ])
            lines.extend(["0", "SEQEND", "8", layer])

        # 주요 측점(20m 간격) TEXT 주석 작도
        for x, y, text_str in labels:
            lines.extend([
                "0", "TEXT", "8", "STATION_LABELS",
                "10", f"{x:.6f}", "20", f"{y:.6f}", "30", "0.0",
                "40", "2.5", "1", text_str
            ])

        lines.extend(["0", "ENDSEC", "0", "EOF"])

        with open(filepath, mode="w", encoding="utf-8") as f:
            f.write("\n".join(lines))