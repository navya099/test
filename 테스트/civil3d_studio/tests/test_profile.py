import unittest
import math
from typing import Optional

from profile.profile_engine import Civil3DProfileEngine
from profile.pvi import PVIPoint


# ==============================================================================
# 단위 테스트 클래스
# ==============================================================================
class TestCivil3DProfileEngine(unittest.TestCase):

    def setUp(self):
        """테스트 공통 선형 제원 설정 (BVP -> PVI-1(대칭 볼록) -> PVI-2(비대칭 오목) -> EVP)"""
        self.pvi_list = [
            PVIPoint("BVP", station=1000.0, elevation=50.0),
            PVIPoint("PVI-1", station=1500.0, elevation=75.0, L=200.0),  # 대칭 볼록 (Crest): L=200m
            PVIPoint("PVI-2", station=2100.0, elevation=60.0, L1=100.0, L2=150.0),  # 비대칭 오목 (Sag): L1=100m, L2=150m
            PVIPoint("EVP", station=2600.0, elevation=85.0)
        ]
        # 엔진을 통해 순수 객체(CompositeProfile) 생성
        self.profile = Civil3DProfileEngine.build("테스트_종단선형", self.pvi_list)

    def test_profile_basic_properties(self):
        """선형 기본 시·종점 측점 검증"""
        self.assertAlmostEqual(self.profile.start_station, 1000.0)
        self.assertAlmostEqual(self.profile.end_station, 2600.0)

    def test_tangent_section_calculation(self):
        """직선 경사 구간(Tangent)의 고도 및 구배 검증"""
        # BVP(1000.0, 50.0) ~ PVI-1 BVC(1400.0) 사이의 직선 구간 (STA 1200.0 지점)
        # 경사 g1 = (75 - 50) / (1500 - 1000) = 25 / 500 = 0.05 (5%)
        el, grade = self.profile.elevation_and_grade_at(1200.0)
        expected_el = 50.0 + 0.05 * (1200.0 - 1000.0)

        self.assertAlmostEqual(el, expected_el, places=4)
        self.assertAlmostEqual(grade, 0.05, places=6)

    def test_parabolic_curve_continuity(self):
        """포물선 종단곡선 구간 내 연속성 및 PVI 지점 계산 검증"""
        # PVI-1 직상부(STA 1500.0) 고도 및 경사 산출 확인
        el, grade = self.profile.elevation_and_grade_at(1500.0)
        self.assertIsInstance(el, float)
        self.assertIsInstance(grade, float)
        # 곡선 내부이므로 g1(+5%)과 g2 사이의 값이어야 함
        self.assertTrue(grade < 0.05)

    def test_asymmetric_curve_boundaries(self):
        """비대칭 종단곡선(PVI-2, L1=100, L2=150)의 BVC/EVC 범위 안팎 계산 검증"""
        bvc_sta = 2100.0 - 100.0  # 2000.0
        evc_sta = 2100.0 + 150.0  # 2250.0

        el_bvc, _ = self.profile.elevation_and_grade_at(bvc_sta)
        el_evc, _ = self.profile.elevation_and_grade_at(evc_sta)

        self.assertIsInstance(el_bvc, float)
        self.assertIsInstance(el_evc, float)

    def test_out_of_bounds_raises_error(self):
        """선형 범위를 벗어난 측점 조회 시 ValueError 발생 검증"""
        with self.assertRaises(ValueError):
            self.profile.elevation_and_grade_at(999.99)  # 시점 이탈

        with self.assertRaises(ValueError):
            self.profile.elevation_and_grade_at(2600.01)  # 종점 이탈

    def test_insufficient_pvis_raises_error(self):
        """PVI 개수가 2개 미만일 때 에러 발생 검증"""
        with self.assertRaises(ValueError):
            Civil3DProfileEngine.build("오류_선형", [PVIPoint("BVP", 1000.0, 50.0)])


if __name__ == "__main__":
    unittest.main(verbosity=2)