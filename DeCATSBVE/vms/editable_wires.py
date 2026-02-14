from core.alignment.define_funtion import iscurve, isslope
from core.structure.define_structure import isbridge_tunnel
from core.wire.common_processor import CommonWireProcessor
from utils.math_util import interpolate_cached, calculate_offset_point, get_elevation_pos, change_permile_to_degree
from xref_module.transaction import Transaction


class EditableWire:
    def __init__(self, wire, structure_list, curve_list ,pitch_list, polyline_with_sta, prev_wire=None, next_wire=None):
        self.wire = wire
        self.structure_list = structure_list
        self.curve_list = curve_list
        self.pitch_list = pitch_list
        self.polyline_with_sta = polyline_with_sta
        self.prev_wire = prev_wire
        self.next_wire = next_wire

    def update(self, index=None, **kwargs):
        if index is not None and 0 <= index < len(self.wire.wires):
            target = self.wire.wires[index]
            for key, value in kwargs.items():
                if key == "offset":  # 시작점
                    target.offset = value
                elif key == "end_point":  # 끝점
                    target.end_point = value
                elif hasattr(target, key):
                    setattr(target, key, value)

        try:
            self.recalculate()
        except Exception as e:
            raise Exception(e)

    def recalculate(self):
        if not self.next_wire:
            return

        current_z = get_elevation_pos(self.wire.pos, self.polyline_with_sta)
        next_z = get_elevation_pos(self.next_wire.wire.pos, self.polyline_with_sta)
        pitch_angle = change_permile_to_degree(isslope(self.wire.pos, self.pitch_list)[1])

        processor = CommonWireProcessor()

        for i, w in enumerate(self.wire.wires):
            # 끝점은 end_point 우선, 없으면 next_wire 기준
            end_point = w.end_point if w.end_point != (0, 0) else (
                self.next_wire.wire.wires[i].offset if i < len(self.next_wire.wire.wires) else w.offset
            )

            new_wire = processor.run(
                polyline_with_sta=self.polyline_with_sta,
                index=w.index,
                pos=self.wire.pos,
                next_pos=self.next_wire.wire.pos,
                current_z=current_z,
                next_z=next_z,
                start=w.offset,  # 시작점
                end=end_point,  # 끝점
                pitch_angle=pitch_angle,
                label=w.label
            )
            w.adjusted_angle = new_wire.adjusted_angle
            w.topdown_angle = new_wire.topdown_angle


