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
        span_data = self.dataset['span_data']
        span_list = self.dataset['span_list']
        cw_span_values = span_data['전차선'][current_structure]
        self.validate_span_lengths([cw_span_values], len(span_list))
        return cw_span_values[span_list.index(currentspan)]

    def get_feeder_span(self, currentspan):
        span_data = self.dataset['span_data']
        span_list = self.dataset['span_list']
        af_span_values = span_data['급전선']
        self.validate_span_lengths([af_span_values], len(span_list))
        return af_span_values[span_list.index(currentspan)]

    def get_protection_wire_span(self, currentspan):
        span_data = self.dataset['span_data']
        span_list = self.dataset['span_list']
        fpw_span_values = span_data['보호선']
        self.validate_span_lengths([fpw_span_values], len(span_list))
        return fpw_span_values[span_list.index(currentspan)]

    def get_inactive_cw_span(self, currentspan):
        span_data = self.dataset['span_data']
        span_list = self.dataset['span_list']
        inactive_cw_values = span_data['무효전차선']
        self.validate_span_lengths([inactive_cw_values], len(span_list))
        return inactive_cw_values[span_list.index(currentspan)]

    def get_inactive_mw_span(self, currentspan):
        span_data = self.dataset['span_data']
        span_list = self.dataset['span_list']
        inactive_mw_values = span_data['무효조가선']
        self.validate_span_lengths([inactive_mw_values], len(span_list))
        return inactive_mw_values[span_list.index(currentspan)]

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

    def get_f_bracket_height(self):
        return self.dataset['f_bracket_height']

    def get_span_list(self):
        return self.dataset['span_list']

    def validate_span_lengths(self, lists, expected_len):
        if not all(len(lst) == expected_len for lst in lists):
            raise ValueError("스판 인덱스와 정의된 LIST의 길이가 맞지 않습니다. 파일을 확인해주세요")