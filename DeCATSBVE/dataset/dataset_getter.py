from utils.comom_util import casting_key_str_to_int


class DatasetGetter:
    def __init__(self, dataset):
        self.dataset = dataset

    def get_bracket_coordinates(self, bracket_type):
        return self.dataset['bracket_coordinates'][bracket_type]

    def get_feeder_insulator_idx(self, current_structure):
        """설계속도와 구조물에 따른 피더 애자 인덱스 반환 (JSON 기반)"""
        return self.dataset['feeder_insulator_idx'][current_structure]

    def get_spreader_idx(self, current_structure, current_airjoint):
        spreader_dictionary = self.dataset['spreader_idx']
        spreader_values = spreader_dictionary.get(current_structure, (0, 0))

        if current_airjoint in ['에어조인트 2호주', '에어조인트 4호주']:
            return spreader_values[0]
        elif current_airjoint == '에어조인트 중간주 (3호주)':
            return spreader_values[1]
        else:
            return spreader_values[0]

    def get_bracket_type(self, current_structure, current_curve):
        pole_data = self.dataset['pole_data']

        # 구조물에 따른 인덱스 가져오기ㅏ
        if current_structure == '토공':
            if current_curve == '직선':
                i_type_index, o_type_index = pole_data['토공']['직선']
            else:
                i_type_index, o_type_index = pole_data['토공']['곡선']
        elif current_structure == '교량':
            if current_curve == '직선':
                i_type_index, o_type_index = pole_data['교량']['직선']
            else:
                i_type_index, o_type_index = pole_data['교량']['곡선']
        elif current_structure == '터널':
            if current_curve == '직선':
                i_type_index, o_type_index = pole_data['터널']['직선']
            else:
                i_type_index, o_type_index = pole_data['터널']['곡선']
        else:
            raise ValueError(f'지원하지 않는 구조물입니다. {current_structure}')
        return i_type_index, o_type_index

    def get_fittings(self):
        """에어조인트 금구류 데이터를 가져옴"""
        return self.get_contact_wire_fitting(), self.get_messenger_wire_fittings(), self.get_steady_arm_fittings()

    def get_contact_wire_fitting(self):
        fitting_data = self.get_bracket_fitting_data()
        return fitting_data['전차선지지금구']['무효인상용']

    def get_messenger_wire_fittings(self):
        fitting_data = self.get_bracket_fitting_data()
        return fitting_data['조가선지지금구']

    def get_steady_arm_fittings(self):
        fitting_data = self.get_bracket_fitting_data()
        return fitting_data['곡선당김금구']

    def get_bracket_fitting_data(self):
        """브래킷 금구류 데이터를 반환 (JSON 기반)"""
        return self.dataset['bracket_fitting_data']

    def get_mast_index(self, current_structure):
        """설계속도와 구조물에 따른 전주 인덱스와 이름 반환 (JSON 기반)"""

        return self.dataset['mast_data'][current_structure]

    def get_pole_gauge(self, current_structure):
        """건식게이지 """
        return self.dataset['pole_gauge'][current_structure]

    def get_f_bracket_codes(self, current_structure):
        return self.get_F_bracket_data().get(current_structure, (0, 0))

    def get_aj_bracket_codes(self, current_structure):
        return self.get_airjoint_bracket_data().get(current_structure, (0, 0))

    def get_bracket_codes(self, current_structure, type=''):
        if type == 'F':
            return self.get_f_bracket_codes(current_structure)
        elif type == 'AJ':
            return self.get_aj_bracket_codes(current_structure)
        return 0, 0


    def get_airjoint_bracket_data(self):
        """에어조인트 브래킷 데이터를 반환 (JSON 기반)"""
        return self.dataset['airjoint_bracket_data']

    def get_F_bracket_data(self):
        """F브래킷 데이터를 반환 (JSON 기반)"""
        return self.dataset['F_bracket_data']

    def get_contact_wire_span(self, currentspan, current_structure):
        """전차선 경간에 따른 인덱스 반환"""
        if current_structure in ['토공', '교량']:
            return self._get_span(currentspan, '토공전차선')
        else:
            return self._get_span(currentspan, '터널전차선')

    def get_feeder_span(self, currentspan):
        return self._get_span(currentspan, '급전선')

    def get_protection_wire_span(self, currentspan):
        return self._get_span(currentspan, '보호선')

    def get_inactive_cw_span(self, currentspan):
        return self._get_span(currentspan, '무효용전차선')

    def get_inactive_mw_span(self, currentspan):
        return self._get_span(currentspan, '무효용조가선')

    def _get_span(self, currentspan, key):
        """공통 스판 조회 메서드"""
        span_data = self.dataset['span_data']
        values = span_data[key]
        if currentspan not in values:
            raise ValueError(f"유효하지 않은 경간 값: {currentspan}")
        return values[currentspan]


    def get_af_offset(self, current_structure):
        af_offset_values = self.dataset['wire_offset']['AF']
        return af_offset_values.get(current_structure, (0, 0))

    def get_fpw_offset(self, current_structure):
        fpw_offset_values = self.dataset['wire_offset']['FPW']
        return fpw_offset_values.get(current_structure, (0, 0))


    def get_contact_wire_and_massanger_wire_info(self, current_structure):
        """전차선 가고와 높이정보 반환 (JSON 기반)"""
        contact_height_dictionary = self.dataset['contact_height_dictionary']

        # 가고와 전차선 높이정보
        system_heigh, contact_height = contact_height_dictionary.get(current_structure, (0, 0))

        return system_heigh, contact_height

    def get_contact_wire_height(self, current_structure):
        """전차선 높이 반환"""
        return self.dataset['contact_height_dictionary'][current_structure][1]

    def get_system_height(self, current_structure):
        """가고 정보 반환"""
        return self.dataset['contact_height_dictionary'][current_structure][0]

    def get_f_bracket_height(self):
        return self.dataset['f_bracket_height']
