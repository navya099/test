
from core.equipment.equipment_data import EquipmentDATA
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
            if track_name in self.devices_by_track:
                continue
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
                        devices.append({
                            "track": track_name,
                            "pos": pole.pos,
                            "post_number": pole.post_number,
                            "device_type": "Anticreeping",
                            "tag": tag
                        })

            self.devices_by_track[track_name] = devices

    def add_manual_section(self, track_name, start_pos, end_pos, mid_pos):
        """사용자가 직접 midpos를 지정해서 흐름방지 섹션 생성"""
        poles = self.poledata[track_name]
        poles_in_section = [p for p in poles if start_pos <= p.pos <= end_pos]
        if not poles_in_section:
            return

        # midpos에 가장 가까운 전주 찾기
        mid_pole = min(poles_in_section, key=lambda p: abs(p.pos - mid_pos))

        indices = [max(0, poles_in_section.index(mid_pole) - 1),
                   poles_in_section.index(mid_pole),
                   min(len(poles_in_section) - 1, poles_in_section.index(mid_pole) + 1)]
        tags = ["흐름방지 시작점", "흐름방지 중간점", "흐름방지 끝점"]

        devices = []
        for tag, idx in zip(tags, indices):
            pole = poles_in_section[idx]
            wire = next((w for w in self.wiredata[track_name] if w.pos == pole.pos), None)
            devices.append({
                "track": track_name,
                "pos": pole.pos,
                "post_number": pole.post_number,
                "device_type": "Anticreeping",
                "tag": tag
            })

        # 기존 섹션 유지하면서 track_name에 추가
        if track_name not in self.devices_by_track:
            self.devices_by_track[track_name] = []
        self.devices_by_track[track_name].extend(devices)

        # 바로 반영
        self.apply()

    def apply(self):
        """실제로 poledata에 장치 태그 반영"""
        self.apply_pole_devices()
        self.apply_wires()

    def apply_pole_devices(self):
        for track_name, devices in self.devices_by_track.items():
            for device in devices:
                pole = next((p for p in self.poledata[track_name] if p.pos == device["pos"]), None)
                if not pole:
                    continue
                pole.section = device['tag']
                if device['tag'] == "흐름방지 시작점":

                    pole.equipments.extend([
                        EquipmentDATA(name='흐름방지장치_강관주용', index=679, offset=(pole.gauge, 0), rotation=0.0, type='흐름방지장치'),
                        EquipmentDATA(name='봉강지선', index=674, offset=(pole.gauge, 0), rotation=0.0, type='봉강지선')
                    ])
                elif device['tag'] == "흐름방지 끝점":
                    pole.equipments.extend([
                        EquipmentDATA(name='흐름방지장치_강관주용', index=679, offset=(pole.gauge, 0), rotation=180, type='흐름방지장치'),
                        EquipmentDATA(name='봉강지선', index=674, offset=(pole.gauge, 0), rotation=180, type='봉강지선')
                    ])

    def apply_wires(self):
        for track_name, devices in self.devices_by_track.items():
            for device in devices:
                pole = next((p for p in self.poledata[track_name] if p.pos == device["pos"]), None)
                if not pole:
                    continue
                wire = next((w for w in self.wiredata[track_name] if w.pos == device["pos"]), None)
                if not wire:
                    continue
                cw = next((w for w in wire.wires if w.label == '전차선'), None)
                if cw is None:
                    continue  # 전차선이 없으면 건너뜀
                if device['tag'] in ["흐름방지 시작점"] and wire:
                    extrawire = self.make_flowstop_wire(pole, cw, track_name, isstart=True)
                    wire.add_wire(extrawire)
                elif device['tag'] in ["흐름방지 중간점"] and wire:
                    extrawire = self.make_flowstop_wire(pole, cw, track_name, isstart=False)
                    wire.add_wire(extrawire)

    def make_flowstop_wire(self, pole, wire, track_name, isstart=True):
        windex = self.wire_processor.pro.get_protection_wire_span(pole.span)
        system_heigh, contact_height = self.wire_processor.pro.get_contact_wire_and_massanger_wire_info(pole.structure)
        start_x = wire.offset[0]
        end_x = wire.end_point[0]
        if isstart:
            start = (pole.gauge, 5.7)
            end = (end_x, system_heigh + contact_height)
        else:
            start = (start_x, system_heigh + contact_height)
            end = (pole.next_gauge, 5.7)
        pitch_angle = change_permile_to_degree(pole.pitch)

        return self.wire_processor.com.run(
            polyline_with_sta=self.wire_processor.polyline_by_track[track_name],
            index=windex, pos=pole.pos, next_pos=pole.next_pos,
            current_z=pole.z, next_z=pole.next_z,
            start=start, end=end, pitch_angle=pitch_angle,
            label='흐름방지선'
        )
