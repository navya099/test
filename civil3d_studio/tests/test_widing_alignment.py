import pytest

from alignment.alignment import Alignment
from alignment.pipoint import PIPoint
from alignment.widing.offset_alignment import OffsetAlignment
from alignment.widing.wideing_region import WideningRegion


def create_parent():

    pis = [
        PIPoint("BP", 0.0, 0.0),
        PIPoint("EP", 1000.0, 0.0),
    ]

    return Alignment.create(
        "MAIN",
        pis,
        start_station=0.0,
    )


def test_nominal_offset():

    parent = create_parent()

    offset = OffsetAlignment(
        name="RIGHT",
        parent_alignment=parent,
        nominal_offset=3.5,
    )

    width, slope = offset.get_offset_at(500.0)

    assert width == pytest.approx(3.5)
    assert slope == pytest.approx(0.0)