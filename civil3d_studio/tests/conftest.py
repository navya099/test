import math
import pytest
from dataclasses import dataclass
from typing import List

from corridor.engine import Corridor3DEngine


class MockAlignment:
    """직선 평면 선형: STA 0 → 1000, offset 좌표는 단순 회전 변환"""
    def __init__(self, total_length: float = 1000.0):
        self.total_length = total_length

    def point_location(self, station: float, offset: float = 0.0):
        # 진행방향 = +Easting 축, offset은 +Northing 축
        return (station, offset)


class MockProfile:
    """종단: 일정 구배(+2%) 가정"""
    def __init__(self, grade: float = 0.02, base_el: float = 40.0):
        self.grade = grade
        self.base_el = base_el

    def elevation_at(self, station: float) -> float:
        return self.base_el + self.grade * station

    def elevation_and_grade_at(self, station: float):
        return self.elevation_at(station), self.grade


class MockOffsetAlignment:
    """일정 폭 차선"""
    def __init__(self, offset_val: float):
        self.offset_val = offset_val

    def get_offset_at(self, station: float):
        return self.offset_val


class MockSuperelevation:
    """일정 편경사(-2%)"""
    def __init__(self, l_slope: float = -0.02, r_slope: float = -0.02):
        self.l_slope = l_slope
        self.r_slope = r_slope

    def get_slopes(self, station: float):
        return self.l_slope, self.r_slope

    # 실제 gui.py는 get_slopes_at을 사용할 수 있음
    def get_slopes_at(self, station: float):
        return self.get_slopes(station)


# ── Fixtures ──
@pytest.fixture
def mock_alignment():
    return MockAlignment(total_length=1000.0)


@pytest.fixture
def mock_profile():
    return MockProfile(grade=0.02, base_el=40.0)


@pytest.fixture
def mock_left_lane():
    return MockOffsetAlignment(-3.5)


@pytest.fixture
def mock_right_lane():
    return MockOffsetAlignment(+3.5)


@pytest.fixture
def mock_superelevation():
    return MockSuperelevation(l_slope=-0.02, r_slope=-0.02)


@pytest.fixture
def flat_terrain(mock_profile):
    """평평한 지반: base_profile_func과 동일 (설계고 = 지반고 → Daylight 없음)"""
    from surface.surface import ExistingGroundTerrain
    return ExistingGroundTerrain(base_profile_func=mock_profile.elevation_at)


@pytest.fixture
def engine(mock_alignment, mock_profile, mock_left_lane, mock_right_lane,
           mock_superelevation, flat_terrain):
    return Corridor3DEngine(
        name="테스트_코리더",
        alignment=mock_alignment,
        profile=mock_profile,
        left_offset_align=mock_left_lane,
        right_offset_align=mock_right_lane,
        superelevation_table=mock_superelevation,
        terrain=flat_terrain,
        structures=[],
    )