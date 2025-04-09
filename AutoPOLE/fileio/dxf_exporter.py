import ezdxf
from utils.util import *


class DxfManager:
    def __init__(self, poledata=None, wiredata=None):
        self.v_scale = 0
        self.h_scale = 0
        self.poledata = poledata  # ✅ PoleDATAManager.poledata 인스턴스를 가져옴
        self.wiredata = wiredata
        self.msp = None
        self.doc = None

    def run(self):
        self.create_new_dxf()
        self.initialize_default_values()
        self.create_plan_drawing()

    def initialize_default_values(self):
        self.h_scale = 1000
        self.v_scale = 400

    def create_plan_drawing(self):
        data = self.poledata
        wiredata = self.wiredata

        for i in range(len(data.poles) - 1):
            pos = data.poles[i].pos
            post_number = data.poles[i].post_number
            mastindex = data.poles[i].mast.index
            mastname = data.poles[i].mast.name
            bracketindex = data.poles[i].Brackets[0].index
            bracketname = data.poles[i].Brackets[0].name
            current_airjoint = data.poles[i].current_airjoint
            current_structure = data.poles[i].current_structure
            current_curve = data.poles[i].current_curve
            gauge = data.poles[i].gauge
            direction = data.poles[i].direction
            pitch = 0 if direction == 'L' else 180

            pos_coord_with_offset = calculate_offset_point(vector_pos, pos_coord, gauge)
            # 전주
            msp.add_circle(pos_coord_with_offset, radius=1.5 * self.h_scale, dxfattribs={'layer': '전주', 'color': 4})

    def crate_pegging_plan_mast_and_bracket(self):
        pass

    def create_new_dxf(self):
        doc = ezdxf.new()
        msp = doc.modelspace()

        self.doc = doc
        self.msp = msp

    def draw_msp_rectangle(self, origin, width, height, layer_name='0', color=0):
        p1 = (origin[0] + width / 2, origin[1] + height / 2)  # 오른쪽 위
        p2 = (p1[0] - width, p1[1])  # 왼쪽 위
        p3 = (p2[0], p2[1] - height)  # 왼쪽 아래
        p4 = (p1[0], p3[1])  # 오른쪽 아래

        # 사각형 그리기
        self.msp.add_lwpolyline([p1, p2, p3, p4, p1], dxfattribs={'layer': layer_name, 'color': color})

