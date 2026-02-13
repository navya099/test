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
        spreader_str = spreader_dictionary.get(current_structure, (0, 0))  # 기본값 (0, 0) 설정

        if current_airjoint in ['에어조인트 2호주', '에어조인트 4호주']:
            spreader_idx = spreader_str[0]
            spreader_name = '평행틀-1m'
        elif current_airjoint in ['에어조인트 중간주 (3호주)']:
            spreader_idx = spreader_str[1]
            spreader_name = '평행틀-1.6m'
        else:
            spreader_idx = spreader_str[0]
            spreader_name = '평행틀-1m'

        return spreader_name, spreader_idx

    def get_bracket_type(self, current_structure, current_curve):
        pole_data = self.dataset['pole_data']

        # 구조물에 따른 인덱스 가져오기ㅏ
        if current_structure == '토공':
            i_type_index, o_type_index = pole_data['토공']
        elif current_structure == '교량':
            if current_curve == '직선':
                i_type_index, o_type_index = pole_data['교량']['직선']
            else:
                i_type_index, o_type_index = pole_data['교량']['곡선']
        elif current_structure == '터널':
            i_type_index, o_type_index = pole_data['터널']
        else:
            raise ValueError(f'지원하지 않는 구조물입니다. {current_structure}')
        return i_type_index, o_type_index

    def get_fitting_and_mast_data(self, current_structure):
        """금구류 및 전주 데이터를 가져옴"""
        fitting_data = self.get_airjoint_fitting_data()
        airjoint_fitting = fitting_data.get('에어조인트', 0)
        flat_fitting = fitting_data.get('FLAT', (0, 0))
        steady_arm_fitting = fitting_data.get('곡선당김금구', (0, 0))

        mast_type, mast_name = self.get_mast_type(current_structure)

        return airjoint_fitting, flat_fitting, steady_arm_fitting, mast_type, mast_name

    def get_airjoint_fitting_data(self):
        """에어조인트 브래킷 금구류 데이터를 반환 (JSON 기반)"""
        return self.dataset['airjoint_fitting_data']

    def get_mast_type(self, current_structure):
        """설계속도와 구조물에 따른 전주 인덱스와 이름 반환 (JSON 기반)"""
        mast_data = self.dataset['mast_data']
        mast_index, mast_name = mast_data.get(current_structure, ("", "알 수 없는 구조"))

        return mast_index, mast_name

    def get_pole_gauge(self, current_structure):
        """건식게이지 """
        return self.dataset['pole_gauge'][current_structure]

    def get_bracket_codes(self, current_structure):
        """브래킷 코드 가져오기"""
        airjoint_bracket_data = self.get_airjoint_bracket_data()
        f_data = self.get_F_bracket_data()

        bracket_values = airjoint_bracket_data.get(current_structure, (0, 0))
        f_values = f_data.get(current_structure, (0, 0))

        return bracket_values, f_values

    def get_airjoint_bracket_data(self):
        """에어조인트 브래킷 데이터를 반환 (JSON 기반)"""
        return self.dataset['airjoint_bracket_data']

    def get_F_bracket_data(self):
        """F브래킷 데이터를 반환 (JSON 기반)"""
        return self.dataset['F_bracket_data']

    def get_wire_span_data(self, currentspan, current_structure):
        """경간에 따른 wire 데이터 반환 (JSON 기반)"""
        span_data = self.dataset['span_data']
        span_list = self.dataset['span_list']
        #구조물에 맞는 전차선 가져오기
        cw_span_values = span_data['전차선'][current_structure]
        af_span_valuse = span_data['급전선']
        fpw_span_values = span_data['보호선']

        #길이검사
        expected_len = len(self.dataset['span_list'])
        if not all(len(lst) == expected_len for lst in [cw_span_values, af_span_valuse, fpw_span_values]):
            raise ValueError('스판 인덱스와 정의된 LIST의 길이가 맞지 않습니다. 파일을 확인해주세요')

        # currentspan에 해당하는 인덱스 및 주석 추출
        idx = span_list.index(currentspan)
        cw_index = cw_span_values[idx]
        af_index = af_span_valuse[idx]
        fpw_index = fpw_span_values[idx]

        return cw_index, af_index, fpw_index

    def get_wire_offset(self, current_structure):
        """AF, FPW offset을 반환 (JSON 기반)"""
        af_offset_values = self.dataset['wire_offset']['AF']
        af_x_offset, af_y_offset = af_offset_values[current_structure]

        fpw_offset_values = self.dataset['wire_offset']['FPW']
        fpw_wire_x_offset, fpw_wire_y_offset = fpw_offset_values[current_structure]

        return af_x_offset, af_y_offset, fpw_wire_x_offset, fpw_wire_y_offset

    def get_contact_wire_and_massanger_wire_info(self, current_structure, span):
        """경간에 따른 무효 전차선/조가선 인덱스와 높이정보 반환 (JSON 기반)"""
        inactive_contact_wire = casting_key_str_to_int(self.dataset['inactive_contact_wire'])
        inactive_messenger_wire = casting_key_str_to_int(self.dataset['inactive_messenger_wire'])
        contact_height_dictionary = self.dataset['contact_height_dictionary']

        # 객체 인덱스 가져오기 (기본값 60)
        contact_object_index = inactive_contact_wire.get(span, inactive_contact_wire[60])
        messenger_object_index = inactive_messenger_wire.get(span, inactive_messenger_wire[60])

        # 가고와 전차선 높이정보
        system_heigh, contact_height = contact_height_dictionary.get(current_structure, (0, 0))

        return contact_object_index, messenger_object_index, system_heigh, contact_height
    def get_f_bracket_height(self):
        return self.dataset['f_bracket_height']

    def get_span_list(self):
        return self.dataset['span_list']