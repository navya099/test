from model.bveroutedata import BVERouteData
import math

from utils import format_distance


class StationDrawer:
    def __init__(self, msp):
        self.msp = msp

    def draw_station_marker(self, bvedata: BVERouteData):
        for station in bvedata.stations:
            angle = math.degrees(station.direction)
            coord = station.coord
            block_ref = self.msp.add_blockref(
                name="정거장중심표",
                insert=(coord.x, coord.y),
                dxfattribs={
                    "layer": "정거장중심표",
                    "rotation": angle + 90
                }
            )
            block_ref.add_auto_attribs({
                "name": f'{station.name}정거장',
                "sta": f'OO기(현){format_distance(station.station)}'
            })