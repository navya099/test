from math_utils import calculate_destination_coordinates
from .alignment import Alignment
from .rail import Rail
from vector2 import Vector2
from vector3 import Vector3
import math
import numpy as np

class AlignmentCalculator:
    def __init__(self):
        self.alignments: list[Alignment] = []

    def create_mainline(self, coords):
        """x,y,z,좌표 리스트로부터 선형생성"""
        name='자선'
        raildata = []
        for i, coord in enumerate(coords):
            current_station = i * 25
            rail = Rail(station=current_station,railindex=0, rail_x=0.0, rail_y=0.0,object_index=0)
            coord = Vector3(coord[0], coord[1], coord[2])
            rail.coord = coord
            raildata.append(rail)
        al = Alignment.from_raildata(name, raildata)
        return al

    def calculate_otherline_coordinates(self, alignments: list[Alignment]):
        # 자선 찾기
        main_alignment = next((a for a in alignments if a.name == '자선'), None)
        if not main_alignment:
            print('자선이 존재하지 않습니다.')
            return alignments

        # station -> mainrail dict 생성
        mainrail_map = {rail.station: rail for rail in main_alignment.raildata}

        for al in alignments:
            if al.name == '자선':
                continue  # 자선 스킵
            for rail in al.raildata:
                mainrail = mainrail_map.get(rail.station)
                if not mainrail:
                    continue
                # 좌표 변환
                #평면좌표
                angle = mainrail.direction.todegree() + (90 if rail.rail_x < 0 else -90)
                newcoord = calculate_destination_coordinates(
                    Vector2(mainrail.coord.x, mainrail.coord.y),
                    bearing=angle,
                    distance=abs(rail.rail_x)
                )
                new_z = mainrail.coord.z + rail.rail_y
                rail.coord = Vector3(newcoord[0], newcoord[1], new_z)
