from curvedirection import CurveDirection
from curvetype import CurveType
from model.bveroutedata import BVERouteData
from model.ipdata import IPdata
from model.segment import SpiralSegment
from utils import format_distance
from vector2 import Vector2
from vector3 import to2d
import math

class CurveDrawer:
    def __init__(self ,msp):
        self.msp = msp

    def draw_curve_text_and_line(self, iplist: list[IPdata], bvedata: BVERouteData):
        for i, ip in enumerate(iplist):
            if i == 0:
                self._add_curve_block(ip.coord, 'BP', bvedata.firstblock, CurveDirection.LEFT, to2d(bvedata.directions[0]).toradian())
            elif i == len(iplist) - 1:
                self._add_curve_block(ip.coord, 'EP', bvedata.lastblock, CurveDirection.LEFT, to2d(bvedata.directions[-1]).toradian())
            else:
                if ip.curvetype == CurveType.Spiral:
                    for seg in ip.segment:
                        if isinstance(seg, SpiralSegment):
                            if seg.isstarted:
                                self._add_curve_block(seg.start_coord, 'SP', seg.start_sta, ip.curve_direction, seg.start_azimuth)
                                self._add_curve_block(seg.end_coord, 'PC', seg.end_sta, ip.curve_direction, seg.end_azimuth)
                            else:
                                self._add_curve_block(seg.start_coord, 'CP', seg.start_sta, ip.curve_direction, seg.start_azimuth)
                                self._add_curve_block(seg.end_coord, 'PS', seg.end_sta, ip.curve_direction, seg.end_azimuth)
                        else:
                            pass
                elif ip.curvetype == CurveType.Simple:
                    seg = ip.segment[0]
                    self._add_curve_block(seg.start_coord, 'BC', seg.start_sta, ip.curve_direction, seg.start_azimuth)
                    self._add_curve_block(seg.end_coord, 'EC', seg.end_sta, ip.curve_direction, seg.end_azimuth)
                else:  # Complex
                    for j, seg in enumerate(ip.segment):

                        if j == 0:
                            self._add_curve_block(seg.start_coord, 'BC', seg.start_sta, ip.curve_direction,
                                                  seg.start_azimuth)
                            self._add_curve_block(seg.end_coord, 'PCC', seg.end_sta, ip.curve_direction, seg.end_azimuth)
                        else:
                            self._add_curve_block(seg.end_coord, 'EC', seg.end_sta, ip.curve_direction,
                                                  seg.end_azimuth)
    def _add_curve_block(self, coord: Vector2, curve_type: str, sta: float, direction: CurveDirection, angle: float):
        xscale = 1 if direction == CurveDirection.RIGHT else -1
        yscale = 1 if direction == CurveDirection.RIGHT else -1
        angle = math.degrees(angle)
        block_ref = self.msp.add_blockref(
            name="곡선인출블럭",
            insert=(coord.x, coord.y),
            dxfattribs={
                "layer": "곡선인출블럭",
                "xscale": xscale,
                "yscale": yscale,
                "rotation":angle - 90
            }
        )
        block_ref.add_auto_attribs({
            "type": f'{curve_type}= ',
            "sta": format_distance(sta)
        })