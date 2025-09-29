from math_utils import calculate_coordinates
from model.bveroutedata import BVERouteData
from vector3 import to2d
import math

class ChainDrawer:
    def __init__(self, msp):
        self.msp = msp
    def draw_chain(self, bvedata: BVERouteData):
        #선형에 배치
        for i, coord in enumerate(bvedata.coords):
            sta = bvedata.firstblock + i * bvedata.block_interval
            angle = to2d(bvedata.directions[i]).todegree() #선형진행각도
            normalize_angle = angle + 90 #선형에 수직인 각도

            offset_coord = calculate_coordinates(coord.x, coord.y, math.radians(normalize_angle), 2)
            kmtext = f"{int(sta // 1000)}km"  # 몫만 사용
            mtext = f"{int(sta % 1000):03d}"  # 3자리로 맞춤
            #chian 선
            self.msp.add_blockref("CHAIN_TICK25", insert=(coord.x, coord.y), dxfattribs={"rotation": normalize_angle})
            # 200m 작은 원
            if sta % 200 == 0:
                self.msp.add_blockref("CHAIN_CIRCLE200", insert=(coord.x, coord.y), dxfattribs={"rotation": normalize_angle})
            if sta % 200 == 0 and sta % 1000 != 0:
                self.msp.add_text(mtext,
                    dxfattribs={
                        'insert': (offset_coord[0], offset_coord[1]),
                        'height': 3,
                        'color': 1,
                        'layer': '200문자',
                        'rotation': angle,
                        'style' : "Gulim"
                    })
            #1km원
            if sta % 1000 == 0:
                self.msp.add_blockref("CHAIN_CIRCLE1000", insert=(coord.x, coord.y), dxfattribs={"rotation": angle})
                self.msp.add_text(kmtext,
                    dxfattribs={
                        'insert': (offset_coord[0], offset_coord[1]),
                        'height': 3,
                        'color': 1,
                        'layer': 'km문자',
                        'rotation': angle,
                        'style': "Gulim"
                    })