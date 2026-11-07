# alignment/calculoatr.py (AlignmentCalculator)
import logging
import math
from alignment.alignment import Alignment
from alignment.rail import Rail
from math_utils import calculate_destination_coordinates
from vector2 import Vector2
from vector3 import Vector3

logger = logging.getLogger(__name__)
MAIN_TRACK_NAME = '자선'


class AlignmentCalculator:
    def create_mainline(self, coords, start_station: int = 0, interval: int = 25):
        """★ 버그 수정: start_station을 받아 절대 측점 생성"""
        raildata = []
        for i, c in enumerate(coords):
            station = start_station + i * interval
            rail = Rail(station=station, railindex=0, rail_x=0.0, rail_y=0.0, object_index=0)
            rail.coord = Vector3(c[0], c[1], c[2])
            raildata.append(rail)
        return Alignment.from_raildata(MAIN_TRACK_NAME, raildata)

    def calculate_otherline_coordinates(self, alignments: list[Alignment]) -> None:
        main_alignment = next((a for a in alignments if a.name == MAIN_TRACK_NAME), None)
        if not main_alignment:
            raise ValueError("자선이 alignments에 존재하지 않습니다.")

        mainrail_map = {rail.station: rail for rail in main_alignment.raildata}

        for al in alignments:
            if al.name == MAIN_TRACK_NAME:
                continue
            for rail in al.raildata:
                mainrail = mainrail_map.get(rail.station)
                if not mainrail:
                    continue
                # ★ 버그 수정: bearing에 라디안(toradian) 적용
                angle_rad = mainrail.direction.toradian() + (math.pi / 2 if rail.rail_x < 0 else -math.pi / 2)

                new_x, new_y = calculate_destination_coordinates(
                    Vector2(mainrail.coord.x, mainrail.coord.y),
                    bearing_rad=angle_rad,
                    distance=abs(rail.rail_x)
                )
                new_z = mainrail.coord.z + rail.rail_y
                rail.coord = Vector3(new_x, new_y, new_z)