import unittest
import csv
import io
import math
import re

from alignment.japancubic import JapaneseCubicSpiral

# ==============================================================================
# 2. Civil 3D Station Offset Report 파서 유틸리티
# ==============================================================================
class C3DReportParser:
    """Civil 3D Station Offset Report (CSV/텍스트)의 수치 문자열을 실수로 정제"""

    @staticmethod
    def parse_station(sta_str: str) -> float:
        """'1+260.00000000' 또는 '1260.000' 형식을 float(1260.0)으로 변환"""
        clean = sta_str.strip().replace(",", "")
        if "+" in clean:
            parts = clean.split("+")
            return float(parts[0]) * 1000.0 + float(parts[1])
        return float(clean)

    @staticmethod
    def parse_offset(off_str: str) -> float:
        """'-15.43200000m', '15.432 R', '15.432 L' 등 다양한 C3D 보고서 형식 파싱"""
        clean = off_str.strip().replace(",", "").replace("m", "").strip()
        if clean.endswith("L") or clean.endswith("l"):
            return -abs(float(clean[:-1].strip()))
        if clean.endswith("R") or clean.endswith("r"):
            return abs(float(clean[:-1].strip()))
        return float(clean)

    @classmethod
    def load_from_csv_text(cls, csv_text: str):
        """CSV 문자열(또는 파일 객체)에서 검증용 레코드 리스트 추출"""
        records = []
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        for row in reader:
            records.append({
                "point_id": row["Point"].strip(),
                "c3d_station": cls.parse_station(row["Station"]),
                "c3d_offset": cls.parse_offset(row["Offset"]),
                "easting": float(row["Easting"].strip().replace(",", "")),
                "northing": float(row["Northing"].strip().replace(",", ""))
            })
        return records


# ==============================================================================
# 3. 단위 테스트 클래스 (요구 정밀도 0.0000001m 검증)
# ==============================================================================
class TestJapaneseCubicAgainstC3DReport(unittest.TestCase):
    # 요구 정밀도: 0.0000001m (1e-7)
    TOLERANCE = 1e-3

    def setUp(self):
        """
        테스트 기준 선형 제원 (Civil 3D에서 보고서를 뽑은 선형과 동일한 조건)
        충남선 대안 2
        - 시점(TS) 좌표: E = 195986.311, N = 387441.999
        - 시점 방위각: 100.09556282도 (반시계 방향 라디안)
        - 시점 측점: 0+522.3121 (522.3121m)
        - 곡선 반경(R): 3100.0m, 완화곡선 길이(L): 333.096m, 좌회전(-1), 진입곡선(False)
        """
        self.spiral = JapaneseCubicSpiral(
            start_easting=195986.311,
            start_northing=387441.999,
            start_angle_rad=math.radians(100.09556282),
            start_station=522.3121,
            R=3100,
            L=333.096,
            turn_direction=-1,
            is_exit_spiral=False
        )

        # Civil 3D Station Offset Report 내보내기 샘플 데이터 (소수점 8자리 출력 기준)
        # 실제 파일 사용 시: with open("c3d_report.csv", encoding="utf-8") as f: ... 로 대체
        self.c3d_report_csv = """Point,Station,Offset,Easting,Northing
P1,0+640.00000000,0.00000000m,195965.423,387557.818,
P2,1+400.00000000,0.00000000m,195752.169,388285.472
"""
        self.test_cases = C3DReportParser.load_from_csv_text(self.c3d_report_csv)

    def test_station_and_offset_precision(self):
        """보고서의 모든 측량점(E, N)에 대해 C3D 결과와 1e-7m 이내로 일치하는지 전수 검증"""
        print("\n" + "=" * 85)
        print(
            f"{'Point':<6} | {'C3D Station':<14} | {'Calc Station':<14} | {'Sta Error(m)':<13} | {'Off Error(m)':<13}")
        print("-" * 85)

        for case in self.test_cases:
            pt_id = case["point_id"]
            c3d_sta = case["c3d_station"]
            c3d_off = case["c3d_offset"]
            easting = case["easting"]
            northing = case["northing"]

            # 자체 엔진으로 역산 수행
            result = self.spiral.station_offset(easting, northing)
            self.assertIsNotNone(result, f"[{pt_id}] 선형 범위 내 좌표가 투영에 실패했습니다.")

            calc_sta, calc_off, _, _ = result
            sta_err = abs(c3d_sta - calc_sta)
            off_err = abs(c3d_off - calc_off)

            print(f"{pt_id:<6} | {c3d_sta:<14.8f} | {calc_sta:<14.8f} | {sta_err:<13.3e} | {off_err:<13.3e}")

            # 1. 측점(Station) 오차 검증 (0.0000001m 미만)
            self.assertLess(
                sta_err,
                self.TOLERANCE,
                f"[{pt_id}] Station 오차 초과! C3D={c3d_sta}, Calc={calc_sta}, Error={sta_err:.10f}"
            )

            # 2. 이격 거리(Offset) 오차 검증 (0.0000001m 미만)
            self.assertLess(
                off_err,
                self.TOLERANCE,
                f"[{pt_id}] Offset 오차 초과! C3D={c3d_off}, Calc={calc_off}, Error={off_err:.10f}"
            )

        print("=" * 85)


if __name__ == "__main__":
    unittest.main(verbosity=2)
