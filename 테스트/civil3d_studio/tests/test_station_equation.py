import pytest

from alignment.station.equation_manager import StationEquationManager


@pytest.fixture
def empty_manager():

    return StationEquationManager(
        start_station=0.0,
        total_physical_length=1000.0,
    )


@pytest.fixture
def sample_manager():

    mgr = StationEquationManager(
        start_station=0.0,
        total_physical_length=1000.0,
    )

    # Gap
    mgr.add_equation_by_back(
        station_back=300.0,
        station_ahead=350.0,
    )

    # Overlap
    mgr.add_equation_by_back(
        station_back=700.0,
        station_ahead=620.0,
    )

    return mgr


# =============================================================================
# 기본 생성
# =============================================================================

def test_create_manager(empty_manager):

    assert empty_manager.start_station == 0.0
    assert empty_manager.total_length == 1000.0

    assert len(empty_manager.equations) == 0
    assert len(empty_manager.regions) == 1


# =============================================================================
# 방정식 없는 상태
# =============================================================================

@pytest.mark.parametrize(
    "raw",
    [0.0, 100.0, 500.0, 1000.0]
)
def test_raw_to_display_no_equation(
    empty_manager,
    raw
):

    display, region = empty_manager.raw_to_display(raw)

    assert display == pytest.approx(raw)
    assert region == 0


@pytest.mark.parametrize(
    "display",
    [0.0, 100.0, 500.0, 1000.0]
)
def test_display_to_raw_no_equation(
    empty_manager,
    display
):

    raw = empty_manager.display_to_raw(display)

    assert raw == pytest.approx(display)


# =============================================================================
# format_station
# =============================================================================

def test_format_station():

    assert (
        StationEquationManager.format_station(1250.5)
        == "1+250.500"
    )


def test_format_station_negative():

    assert (
        StationEquationManager.format_station(-1250.5)
        == "-1+250.500"
    )


# =============================================================================
# Gap 방정식
# =============================================================================

def test_gap_equation_creation(sample_manager):

    assert len(sample_manager.equations) == 2


def test_gap_station_is_missing(sample_manager):

    results = sample_manager.display_to_raw_all(
        320.0
    )

    assert results == []


def test_gap_display_to_raw_raises(sample_manager):

    with pytest.raises(ValueError):
        sample_manager.display_to_raw(
            320.0
        )


# =============================================================================
# Overlap 방정식
# =============================================================================

def test_overlap_returns_two_matches(sample_manager):

    results = sample_manager.display_to_raw_all(
        650.0
    )

    assert len(results) == 2


def test_overlap_region1(sample_manager):

    raw = sample_manager.display_to_raw(
        650.0,
        region_index=1,
    )

    assert raw == pytest.approx(600.0)


def test_overlap_region2(sample_manager):

    raw = sample_manager.display_to_raw(
        650.0,
        region_index=2,
    )

    assert raw == pytest.approx(680.0)


# =============================================================================
# add_equation_by_raw
# =============================================================================

def test_add_equation_by_raw():

    mgr = StationEquationManager(
        total_physical_length=1000.0
    )

    mgr.add_equation_by_raw(
        raw_station=300.0,
        station_ahead=350.0,
    )

    eq = mgr.equations[0]

    assert eq.raw_station == pytest.approx(300.0)
    assert eq.station_back == pytest.approx(300.0)
    assert eq.station_ahead == pytest.approx(350.0)


# =============================================================================
# Region 생성
# =============================================================================

def test_region_count(sample_manager):

    assert len(sample_manager.regions) == 3


def test_first_region(sample_manager):

    region = sample_manager.regions[0]

    assert region["raw_start"] == pytest.approx(0.0)
    assert region["raw_end"] == pytest.approx(300.0)


def test_last_region(sample_manager):

    region = sample_manager.regions[-1]

    assert region["raw_start"] == pytest.approx(650.0)
    assert region["raw_end"] == pytest.approx(1000.0)


# =============================================================================
# raw -> display
# =============================================================================

def test_raw_to_display_before_gap(sample_manager):

    display, region = sample_manager.raw_to_display(
        100.0
    )

    assert display == pytest.approx(100.0)
    assert region == 0


def test_raw_to_display_after_gap(sample_manager):

    display, region = sample_manager.raw_to_display(
        400.0
    )

    assert display == pytest.approx(450.0)
    assert region == 1


def test_raw_to_display_after_overlap(sample_manager):

    display, region = sample_manager.raw_to_display(
        800.0
    )

    assert display == pytest.approx(770.0)

    assert region == 2


# =============================================================================
# 범위 예외
# =============================================================================

def test_raw_to_display_invalid_low(
    empty_manager
):

    with pytest.raises(ValueError):
        empty_manager.raw_to_display(
            -1.0
        )


def test_raw_to_display_invalid_high(
    empty_manager
):

    with pytest.raises(ValueError):
        empty_manager.raw_to_display(
            1001.0
        )


def test_add_equation_invalid_location():

    mgr = StationEquationManager(
        total_physical_length=1000.0
    )

    with pytest.raises(ValueError):
        mgr.add_equation_by_raw(
            raw_station=0.0,
            station_ahead=100.0,
        )

    with pytest.raises(ValueError):
        mgr.add_equation_by_raw(
            raw_station=1000.0,
            station_ahead=1100.0,
        )


# =============================================================================
# Round Trip
# =============================================================================

@pytest.mark.parametrize(
    "raw_station",
    [
        50.0,
        200.0,
        400.0,
        550.0,
        800.0,
        950.0,
    ]
)
def test_round_trip(
    sample_manager,
    raw_station,
):

    display, region = (
        sample_manager.raw_to_display(
            raw_station
        )
    )

    raw2 = sample_manager.display_to_raw(
        display,
        region_index=region,
    )

    assert raw2 == pytest.approx(
        raw_station,
        abs=0.001,
    )