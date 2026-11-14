import pytest

from alignment.alignment import Alignment
from alignment.pipoint import PIPoint


def create_sample_alignment():

    pi_list = [
        PIPoint(
            name='BP',
            easting=0.0,
            northing=0.0,
        ),
        PIPoint('EP',
            easting=1000.0,
            northing=0.0,
        ),
    ]

    return Alignment.create(
        name="TEST",
        pi_list=pi_list,
        start_station=0.0,
    )


def create_curve_alignment():

    pi_list = [
        PIPoint('BP',
            easting=0.0,
            northing=0.0,
        ),
        PIPoint('IP1',
            easting=1000.0,
            northing=0.0,
            R=400.0,
            L1=100.0,
            L2=100.0,
        ),
        PIPoint('EP',
            easting=1000.0,
            northing=1000.0,
        ),
    ]

    return Alignment.create(
        name="CURVE",
        pi_list=pi_list,
        start_station=0.0,
    )


def test_create_straight_alignment():

    al = create_sample_alignment()

    assert al is not None
    assert len(al.entities) == 1


def test_create_requires_two_pi():

    pi_list = [
        PIPoint('BP',
            easting=0.0,
            northing=0.0,
        )
    ]

    with pytest.raises(ValueError):
        Alignment.create(
            name="TEST",
            pi_list=pi_list,
        )


def test_straight_alignment_station():

    al = create_sample_alignment()

    assert al.starting_station == pytest.approx(0.0)
    assert al.ending_station == pytest.approx(1000.0)


def test_point_location_on_tangent():

    al = create_sample_alignment()

    e, n = al.point_location(500.0)

    assert e == pytest.approx(500.0, abs=0.001)
    assert n == pytest.approx(0.0, abs=0.001)


def test_point_location_with_offset():

    al = create_sample_alignment()

    e, n = al.point_location(
        station=500.0,
        offset=10.0,
    )

    assert e == pytest.approx(500.0, abs=0.001)

    # 현재 설계
    # +offset = 우측
    assert n == pytest.approx(-10.0, abs=0.001)


def test_station_offset_inverse():

    al = create_sample_alignment()

    sta, off, _, _ = al.station_offset(
        500.0,
        -10.0,
    )

    assert sta == pytest.approx(500.0, abs=0.01)
    assert off == pytest.approx(10.0, abs=0.01)


def test_point_location_out_of_range():

    al = create_sample_alignment()

    with pytest.raises(ValueError):
        al.point_location(-1.0)

    with pytest.raises(ValueError):
        al.point_location(1001.0)


def test_alignment_with_curve():

    al = create_curve_alignment()

    assert len(al.entities) > 1

    assert al.starting_station == pytest.approx(0.0)

    assert al.ending_station > 1000.0


@pytest.mark.parametrize(
    "station",
    [0, 50, 100, 200, 500, 900]
)
def test_round_trip(station):

    al = create_sample_alignment()

    e, n = al.point_location(station)

    sta2, off, _, _ = al.station_offset(e, n)

    assert sta2 == pytest.approx(
        station,
        abs=0.01,
    )

    assert off == pytest.approx(
        0.0,
        abs=0.01,
    )


def test_start_station_offset():

    pi_list = [
        PIPoint('BP',0.0, 0.0),
        PIPoint('EP',1000.0, 0.0),
    ]

    al = Alignment.create(
        name="TEST",
        pi_list=pi_list,
        start_station=1000.0,
    )

    assert al.starting_station == pytest.approx(1000.0)
    assert al.ending_station == pytest.approx(2000.0)


def test_point_location_at_start():

    al = create_sample_alignment()

    e, n = al.point_location(
        al.starting_station
    )

    assert e == pytest.approx(0.0)
    assert n == pytest.approx(0.0)


def test_point_location_at_end():

    al = create_sample_alignment()

    e, n = al.point_location(
        al.ending_station
    )

    assert e == pytest.approx(1000.0)
    assert n == pytest.approx(0.0)


def test_station_offset_round_trip_with_offset():

    al = create_sample_alignment()

    station = 500.0
    offset = 20.0

    e, n = al.point_location(
        station=station,
        offset=offset,
    )

    sta2, off2, _, _ = al.station_offset(
        e,
        n,
    )

    assert sta2 == pytest.approx(
        station,
        abs=0.01,
    )

    assert off2 == pytest.approx(
        offset,
        abs=0.01,
    )


def test_left_turn_curve():

    pi_list = [
        PIPoint('BP',
            easting=0.0,
            northing=0.0,
        ),
        PIPoint('IP1',
            easting=1000.0,
            northing=0.0,
            R=400.0,
            L1=100.0,
            L2=100.0,
        ),
        PIPoint('EP',
            easting=1000.0,
            northing=-1000.0,
        ),
    ]

    al = Alignment.create(
        name="LEFT",
        pi_list=pi_list,
    )

    assert len(al.entities) > 1

    assert al.ending_station > 0.0


def test_arc_without_spiral():

    pi_list = [
        PIPoint('BP',
            easting=0.0,
            northing=0.0,
        ),
        PIPoint('IP1',
            easting=1000.0,
            northing=0.0,
            R=400.0,
            L1=0.0,
            L2=0.0,
        ),
        PIPoint('EP',
            easting=1000.0,
            northing=1000.0,
        ),
    ]

    al = Alignment.create(
        name="NOSPIRAL",
        pi_list=pi_list,
    )

    assert len(al.entities) >= 2


def test_s_curve():

    pi_list = [
        PIPoint('BP',
            easting=0.0,
            northing=0.0,
        ),
        PIPoint('IP1',
            easting=1000.0,
            northing=0.0,
            R=500.0,
            L1=100.0,
            L2=100.0,
        ),
        PIPoint('IP2',
            easting=1500.0,
            northing=500.0,
            R=500.0,
            L1=100.0,
            L2=100.0,
        ),
        PIPoint('EP',
            easting=2500.0,
            northing=500.0,
        ),
    ]

    al = Alignment.create(
        name="SCURVE",
        pi_list=pi_list,
    )

    assert len(al.entities) > 4


@pytest.mark.parametrize(
    "station",
    [0, 100, 300, 500, 800]
)
def test_curve_round_trip(station):

    al = create_curve_alignment()

    if station > al.ending_station:
        return

    e, n = al.point_location(station)

    sta2, off, _, _ = al.station_offset(e, n)

    assert sta2 == pytest.approx(
        station,
        abs=0.1,
    )

    assert off == pytest.approx(
        0.0,
        abs=0.1,
    )