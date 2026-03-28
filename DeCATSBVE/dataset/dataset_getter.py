from utils.comom_util import casting_key_str_to_int


class DatasetGetter:
    """데이터셋 겟터"""
    def __init__(self, dataset):
        self.dataset = dataset

    def get_prefix(self):
        return self.dataset['design']['prefix']

    def get_design_speed(self):
        return self.dataset['design']['speed']

    def get_airjoint_offset(self, bracket_type):
        """에어조인트구간 전차선 상호이격거리 반환"""
        return self.dataset['airjoint']['offset'][bracket_type]

    def get_airsection_offset(self, bracket_type):
        """에어섹션구간 전차선 상호이격거리 반환"""
        return self.dataset['airsection']['offset'][bracket_type]

    def get_feeder_insulator_idx(self, current_structure):
        """설계속도와 구조물에 따른 피더 애자 인덱스 반환 (JSON 기반)"""
        return self.dataset['feeder'][current_structure]

    def get_spreader_idx(self, current_structure, length: str):
        """평행구간 평행틀 인덱스 반환"""
        spreader_dictionary = self.dataset['spreader']
        spreader_values = spreader_dictionary.get(current_structure, (0, 0))
        return spreader_values.get(length, None)

    def get_bracket_codes(self, bracket_type: str, current_structure: str, base_type: str | None = None):
        """
        브래킷 타입과 구조물에 따른 인덱스 반환
        - bracket_type: '일반개소', '에어조인트', 'F브래킷' 등
        - current_structure: '토공', '교량', '터널'
        - base_type: 'I' 또는 'O' (일반개소처럼 방향 구분이 필요한 경우만 사용)
        """
        try:
            data = self.dataset['bracket']['index'][bracket_type][current_structure]
            if base_type:
                return data[base_type]
            return data
        except KeyError:
            raise ValueError(f"지원하지 않는 브래킷 타입/구조물/방향입니다: {bracket_type}, {current_structure}, {base_type}")


    def get_fittings(self):
        """에어조인트 금구류 데이터를 가져옴"""
        return self.get_contact_wire_fitting(), self.get_messenger_wire_fittings(), self.get_steady_arm_fittings()

    def get_contact_wire_fitting(self):
        """전차선지지금구 무효인상용"""
        fitting_data = self.get_bracket_fitting_data()
        return fitting_data['전차선지지금구']['무효인상용']

    def get_messenger_wire_fittings(self):
        """조가선지지금구"""
        fitting_data = self.get_bracket_fitting_data()
        return fitting_data['조가선지지금구']

    def get_steady_arm_fittings(self):
        """곡선당김금구"""
        fitting_data = self.get_bracket_fitting_data()
        return fitting_data['곡선당김금구']

    def get_bracket_fitting_data(self):
        """브래킷 금구류 데이터를 반환 (JSON 기반)"""
        return self.dataset['bracket']['fitting']

    def get_mast_index(self, current_structure, section):
        """설계속도와 구조물에 따른 전주 인덱스와 이름 반환 (JSON 기반)"""
        if section is None:
            return self.dataset['mast']['index']['일반개소'][current_structure]
        else:
            return self.dataset['mast']['index']['평행개소'][current_structure]

    def get_pole_gauge(self, current_structure):
        """건식게이지 """
        return self.dataset['mast']['gauge'][current_structure]

    def get_airjoint_bracket_data(self):
        """에어조인트 브래킷 데이터를 반환 (JSON 기반)"""
        return self.dataset['bracket']['index']['에어조인트']

    def get_F_bracket_data(self):
        """F브래킷 데이터를 반환 (JSON 기반)"""
        return self.dataset['bracket']['index']['F브래킷']

    def get_contact_wire_span(self, currentspan, current_structure):
        """전차선 경간에 따른 인덱스 반환"""
        if current_structure in ['토공', '교량']:
            return self._get_span(currentspan, '토공전차선')
        else:
            return self._get_span(currentspan, '터널전차선')

    def get_feeder_span(self, currentspan):
        """SPAN에 해당하는 급전선 인덱스"""
        return self._get_span(currentspan, '급전선')

    def get_protection_wire_span(self, currentspan):
        """SPAN에 해당하는 보호선 인덱스"""
        return self._get_span(currentspan, '보호선')

    def get_inactive_cw_span(self, currentspan):
        """SPAN에 해당하는 무효전차선 인덱스"""
        return self._get_span(currentspan, '무효용전차선')

    def get_inactive_mw_span(self, currentspan):
        """SPAN에 해당하는 무효조가선 인덱스"""
        return self._get_span(currentspan, '무효용조가선')

    def _get_span(self, currentspan, key):
        """공통 스판 조회 메서드"""
        span_data = self.dataset['span_data']
        values = span_data[key]
        if currentspan not in values:
            raise ValueError(f"유효하지 않은 경간 값: {currentspan}")
        return values[currentspan]

    def get_af_offset(self, current_structure):
        """구조물에 해당하는 급전선 오프셋"""
        af_offset_values = self.dataset['wire']['offset']['AF']
        return af_offset_values.get(current_structure, (0, 0))

    def get_fpw_offset(self, current_structure):
        """구조물에 해당하는 보호선 오프셋"""
        fpw_offset_values = self.dataset['wire']['offset']['FPW']
        return fpw_offset_values.get(current_structure, (0, 0))

    def get_contact_wire_and_massanger_wire_info(self, current_structure):
        """전차선 가고와 높이정보 반환 (JSON 기반)"""
        return self.get_system_height(current_structure), self.get_contact_wire_height(current_structure)

    def get_contact_wire_height(self, current_structure):
        """전차선 높이 반환"""
        return self.dataset['wire']['offset']['CW'][current_structure]

    def get_system_height(self, current_structure):
        """가고 정보 반환"""
        return self.dataset['wire']['system_height'][current_structure]

    def get_airjoint_f_bracket_height(self):
        """에어조인트구간 f브래킷 인상높이 반환"""
        return self.dataset['airjoint']['bracket_height']

    def get_airsection_f_bracket_height(self):
        """에어섹션구간 f브래킷 인상높이 반환"""
        return self.dataset['airsection']['bracket_height']

    def get_post_base(self, current_structure):
        """전철주 기초 인덱스 반환"""
        return self.dataset['mast']['foundation'][current_structure]

    def get_mast_band_index(self, band_type, size):
        """전주 밴드 인덱스"""
        return self.dataset['mast']['band']['index'][band_type][size]

    def get_mast_band_offset(self, band_type, current_structure):
        """전주 밴드 오프셋
        """
        return self.dataset['mast']['band']['yoffset'][band_type][current_structure]

    def get_extra_band_index(self):
        """추가 전주 밴드"""
        return self.dataset['mast']['band']['index'].get('기타', None)
    def get_extra_band_offset(self):
        """추가 전주 오프셋"""
        return self.dataset['mast']['band']['yoffset'].get('기타', None)

    def get_extra_wire_dictionary(self):
        """추가전선 오프셋 딕셔너리 반환"""
        return self.dataset['wire']['offset'].get('Extra', None)
