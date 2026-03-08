from networkx.algorithms.operators.unary import reverse

from core.equipment.equipment_data import EquipmentDATA
from core.wire.extra_wire.extra_wire_processor import ExtraWireProcessor
from utils.math_util import change_permile_to_degree


class AnticreepingDeviceProcessor:
    def __init__(self, poledata, wiredata, airjoint_list, wire_processor):
        self.devices_by_track = {}
        self.poledata = poledata      # {"main": [...], "sub": [...]}
        self.wiredata = wiredata
        self.airjoint_list = airjoint_list  # 그냥 리스트일 경우
        self.wire_processor = wire_processor
    def process(self):
        self.define_section()
        self.apply()

    def define_section(self):
        for track_name, poles in self.poledata.items():
            devices = []
            aj_list = self.airjoint_list

            for i in range(len(aj_list) - 1):
                current_tag = aj_list[i][1]
                next_tag = aj_list[i + 1][1]

                if current_tag == "에어조인트 끝점 (5호주)" and next_tag == "에어조인트 시작점 (1호주)":
                    start_pos = aj_list[i][0]
                    end_pos = aj_list[i + 1][0]

                    poles_in_section = [p for p in poles if start_pos <= p.pos <= end_pos]
                    if not poles_in_section:
                        continue

                    mid_index = len(poles_in_section) // 2
                    mid_pole = poles_in_section[mid_index]

                    # 중심 전주 기준 앞뒤 1개 포함 (예시)
                    indices = [max(0, mid_index - 1), mid_index, min(len(poles_in_section) - 1, mid_index + 1)]
                    tags = ["흐름방지 시작점", "흐름방지 중간점", "흐름방지 끝점"]


                    for tag, idx in zip(tags, indices):
                        pole = poles_in_section[idx]
                        wire = next((w for w in self.wiredata[track_name] if w.pos == pole.pos), None)
                        devices.append({
                            "track": track_name,
                            "pos": pole.pos,
                            "post_number": pole.post_number,
                            "device_type": "Anticreeping",
                            "tag": tag,
                            "pole":pole, #pole객체 직접 참조
                            "wire": wire #wire객체 직접참조
                        })

            self.devices_by_track[track_name] = devices

    def apply(self):
        """실제로 poledata에 장치 태그 반영"""
        self.apply_pole_devices()
        self.apply_wires()

    def apply_pole_devices(self):
        for track_name, devices in self.devices_by_track.items():
            for device in devices:
                pole = device["pole"]
                pole.section = device['tag']
                if device['tag'] == "흐름방지 시작점":

                    pole.equipments.extend([
                        EquipmentDATA(name='장간애자N-a', index=678, offset=(pole.gauge, 5.7), rotation=0.0, type='장간애자'),
                        EquipmentDATA(name='봉강지선', index=674, offset=(pole.gauge, 0), rotation=0.0, type='봉강지선')
                    ])
                elif device['tag'] == "흐름방지 끝점":
                    pole.equipments.extend([
                        EquipmentDATA(name='장간애자N-a', index=678, offset=(pole.gauge, 5.7), rotation=180, type='장간애자'),
                        EquipmentDATA(name='봉강지선', index=674, offset=(pole.gauge, 0), rotation=180, type='봉강지선')
                    ])

    def apply_wires(self):
        for track_name, devices in self.devices_by_track.items():
            for device in devices:
                wire = device["wire"]
                pole = device["pole"]
                if device['tag'] in ["흐름방지 시작점"] and wire:
                    extrawire = self.make_flowstop_wire(pole, track_name)
                    wire.add_wire(extrawire)
                elif device['tag'] in ["흐름방지 중간점"] and wire:
                    extrawire = self.make_flowstop_wire(pole, track_name, reverse=True)
                    wire.add_wire(extrawire)

    def make_flowstop_wire(self, pole, track_name, reverse=False):
        windex = self.wire_processor.pro.get_protection_wire_span(pole.span)
        system_heigh, contact_height = self.wire_processor.pro.get_contact_wire_and_massanger_wire_info(pole.structure)

        start = (pole.gauge, 5.7)
        end = (pole.brackets[0].stagger, system_heigh + contact_height)

        # 끝점일 경우 방향 반전
        if reverse:
            start, end = end, start

        pitch_angle = change_permile_to_degree(pole.pitch)

        return self.wire_processor.com.run(
            polyline_with_sta=self.wire_processor.polyline_by_track[track_name],
            index=windex, pos=pole.pos, next_pos=pole.next_pos,
            current_z=pole.z, next_z=pole.next_z,
            start=start, end=end, pitch_angle=pitch_angle,
            label='흐름방지선'
        )
