from scipy.sparse.csgraph import structural_rank

from polemodule import BaseManager
from util import *
import os
import sys

# 현재 main.py 기준으로 상위 폴더에서 bveparser 경로 추가
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
bve_path = os.path.join(base_path, 'bveparser')
config_path = base_path + '/AutoPOLE/config/span_data.json'
if bve_path not in sys.path:
    sys.path.insert(0, bve_path)
from OpenBveApi.Math.Vectors.Vector3 import Vector3
from jsonmodule import ConfigManager
from types import MappingProxyType


class WirePositionManager(BaseManager):
    def __init__(self, params, poledata):
        super().__init__(params, poledata)
        self.spandata = SpanDatabase(get_json_spandata())
        self.wiredata = None

    def run(self):
        self.create_contact_wire()
        self.create_feeder_wire()
        self.create_af_wire()

    def create_contact_wire(self):
        data = self.poledata
        spandata = self.spandata
        wiredata = WireDataManager()  # 인스턴스 생성
        polyline_with_sta = [(i * 25, *values) for i, values in enumerate(self.coord_list)]
        for i in range(len(data.poles) - 1):
            pos = data.poles[i].pos
            next_pos = data.poles[i + 1].pos
            pos_coord, vector_pos = return_pos_coord(polyline_with_sta, pos)
            next_type = data.poles[i + 1].Brackets[0].type
            span = data.poles[i].span
            currentz = pos_coord[2]
            data.poles[i].coord = Vector3(pos_coord)
            current_structure = data.poles[i].current_structure
            contact_index = spandata.get_span_indices(self.designspeed, current_structure, 'contact', span)
            sign = -1 if data.poles[i].Brackets[0].type == 'I' else 1
            next_sign = -1 if next_type == 'I' else 1

            lateral_offset = sign * 0.2
            next_offset = next_sign * 0.2
            wiredata.wires[i].contactwire.stagger = lateral_offset

            planangle = calculate_curve_angle(polyline_with_sta, pos, next_pos, lateral_offset, next_offset)
            wiredata.wires[i].contactwire.index = contact_index
            wiredata.wires[i].contactwire.xyangle = planangle
            block = WireDATA()
            wiredata.wires.append(block)
        self.wiredata = wiredata
    def create_feeder_wire(self):
        pass

    def create_af_wire(self):
        pass


class WireDataManager:
    def __init__(self):
        self.wires = []
        wire = WireDATA()
        self.wires.append(wire)


class WireDATA:
    def __init__(self):
        self.contactwire = ContactWireElement()  # 전차선 요소
        self.feederwire = FeederWireElement()  # 급전선요소
        self.afwire = AFwireElement()  # 보호선요소


class WireElement:
    def __init__(self):
        self.name = ''  # 이름
        self.height = 0.0  # 레일면에서의 높이
        self.length = 0  # 전선 길이
        self.xyangle = 0.0  # 전선의 평면각도
        self.index = 0  # 인덱스
        self.xoffset = 0.0  # x 오프셋
        self.yoffset = 0.0  # y 오프셋
        self.yzangle = 0.0  # 전선의 종단각도


class ContactWireElement(WireElement):
    def __init__(self):
        super().__init__()
        self.systemheihgt = 0.0  # 가고 :
        self.stagger = 0.0  # 편위


class FeederWireElement(WireElement):
    def __init__(self):
        super().__init__()


class AFwireElement(WireElement):
    def __init__(self):
        super().__init__()


def get_json_spandata():
    file = config_path  # 파이선 소스 폴더내의 config폴더에서 찾기
    configmanager = ConfigManager(file)
    spandata = configmanager.config
    return spandata


class SpanDatabase:
    def __init__(self, data: dict):
        self._data = MappingProxyType(data)

    def get_speed_codes(self):
        return list(self._data.keys())

    def get_wire_types(self, speed_code):
        return list(self._data[speed_code]["wires"].keys())

    def get_span_indices(self, speed_code, structure, wire_type, span_length):
        try:
            return self._data[str(speed_code)][structure][wire_type]["span_index"][str(span_length)]
        except KeyError:
            return ()

    def get_offset(self, speed_code, wire_type, structure_type):
        try:
            return tuple(self._data[speed_code]["wires"][wire_type]["offset"][structure_type])
        except KeyError:
            return 0, 0

    def get_prefix(self, speed_code):
        return self._data[speed_code].get("prefix", "")

    @staticmethod
    def get_span_description(span_length):
        span_map = {
            45: '경간 45m',
            50: '경간 50m',
            55: '경간 55m',
            60: '경간 60m'
        }
        return span_map.get(span_length, f"경간 {span_length}m")
