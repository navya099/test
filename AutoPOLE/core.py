from util import *
import sys

sys.path.append("D:\문서\chatgpt성과\python\BVEParser")
from BVEclass import RouteData # BVE CLASS 로드
from filemodule import TxTFileHandler


class MainProcess:
    def __init__(self, taskwizard):
        self.taskwizard = taskwizard  # taskwizard 인스턴스를 속성으로

        self.polePositionManager = PolePositionManager()  # 새 폴매니저 인스턴스 생성
        self.params = create_dic(pole_positions, structure_list, curvelist, pitchlist,
                                 design_speed, airjoint_list, polyline, pole_type_list, pole_number_list)
        main_process = MainProcess(params)
        self.pole_data = DATA(params)
        self.processor = PoleDataProcessor(self.pole_data)

    def run(self):
        pole_data_lines = self.processor.process_pole_data()
        poledata_filename = '전주.txt'
        buffered_write(poledata_filename, pole_data_lines)


class DATA:
    def __init__(self, params, mode=1, LINECOUNT=1, LINEOFFSET=0.0, POLE_direction=0):
        """초기화"""
        # 데이터 언팩
        self._positions, self._structure_list, self._curve_list, self._pitch_list, self._DESIGNSPEED, \
            self._airjoint_list, self._polyline, self._post_type_list, self._post_number_lst, = unpack_dic(params)

        self._mode = mode
        self._LINENUM = LINECOUNT
        self._LINEOFFSET = LINEOFFSET

        # 선로 좌우측 확인 (항상 tuple로 변환)
        self._line1_pole_direction, self._line2_pole_direction = self._convert_to_tuple(POLE_direction)

        self._line1_angle = 0 if self._line1_pole_direction == -1 else 180  # 하선 좌측: 0, 우측: 180
        self._line2_angle = 180  # 상선은 항상 180

        # 전주 데이터
        self._pole_data = format_pole_data(self._DESIGNSPEED)
        self._polyline_with_sta = [(i * 25, *values) for i, values in enumerate(self._polyline)]

        # 모드 1인 경우 새로운 전주 번호 생성, 모드 2면 기존 유지
        self._post_numbers = generate_postnumbers(self._positions) if mode == 1 else self._post_number_lst

    def _convert_to_tuple(self, direction):
        """POLE 방향을 항상 튜플로 변환"""
        if isinstance(direction, tuple):
            return direction
        return direction, None

    # 속성 캡슐화 (읽기 전용)
    @property
    def positions(self):
        return self._positions[:]  # 복사본 반환 (원본 보호)

    @property
    def mode(self):
        return self._mode  # 복사본 반환 (원본 보호)

    @property
    def structure_list(self):
        return self._structure_list.copy()

    @property
    def curve_list(self):
        return self._curve_list.copy()

    @property
    def pitch_list(self):
        return self._pitch_list.copy()

    @property
    def DESIGNSPEED(self):
        return self._DESIGNSPEED

    @property
    def pole_data(self):
        return self._pole_data

    @property
    def LINENUM(self):
        return self._LINENUM

    @property
    def LINEOFFSET(self):
        return self._LINEOFFSET

    @property
    def post_numbers(self):
        return self._post_numbers.copy()

    @property
    def line1_angle(self):
        return self._line1_angle

    @property
    def line2_angle(self):
        return self._line2_angle

    @property
    def airjoint_list(self):
        return self._airjoint_list.copy()  # '_airjoint_list'를 반환

    @property
    def line1_pole_direction(self):
        return self._line1_pole_direction  # 'line1_pole_direction'를 반환

    @property
    def line2_pole_direction(self):
        return self._line2_pole_direction  # 'line1_pole_direction'를 반환

    @property
    def polyline_with_sta(self):
        return self._polyline_with_sta.copy()  # 'line1_pole_direction'를 반환


class PolePositionManager:
    def __init__(self):
        self.txtfile_handler = TxTFileHandler()
        self.mode = mode
        self.start_km = start_km
        self.end_km = end_km
        self.pole_positions = []
        self.airjoint_list = []
        self.post_number_lst = []
        self.posttype_list = []
        self.total_data_list = []

    def generate_positions(self):
        if self.mode == 1:
            self.pole_positions = distribute_pole_spacing_flexible(self.start_km, self.end_km)
            self.airjoint_list = define_airjoint_section(self.pole_positions)
            self.post_number_lst = generate_postnumbers(self.pole_positions)
        else:
            # Load from file
            messagebox.showinfo('파일 선택', '사용자 정의 전주파일을 선택해주세요')

            self.load_pole_positions_from_file()
            logger.info('사용자 정의 전주파일이 입력되었습니다.')

    def load_pole_positions_from_file(self) -> None:
        """txt 파일을 읽고 곧바로 '측점', '전주번호', '타입', '에어조인트' 정보를 반환하는 함수"""

        data_list = []
        positions = []
        post_number_list = []
        type_list = []
        airjoint_list = []

        # 텍스트 파일(.txt) 읽기
        self.txtfile_handler.select_file("미리 정의된 전주 파일 선택", [("txt files", "*.txt"), ("All files", "*.*")])
        txt_filepath = self.txtfile_handler.get_filepath()

        df_curve = pd.read_csv(txt_filepath, sep=",", header=0, names=['측점', '전주번호', '타입', '에어조인트'])

        # 곡선 구간 정보 저장
        self.total_data_list = df_curve.to_records(index=False).tolist()
        self.pole_positions = df_curve['측점'].tolist()
        self.post_number_lst = list(zip(df_curve['측점'], df_curve['전주번호']))
        self.posttype_list = list(zip(df_curve['측점'], df_curve['타입']))
        self.airjoint_list = [(row['측점'], row['에어조인트']) for _, row in df_curve.iterrows() if row['에어조인트'] != '일반개소']

    # GET 메소드 추가
    def get_all_pole_data(self):
        """전주 관련 모든 데이터를 반환"""
        return {
            "pole_positions": self.pole_positions,
            "airjoint_list": self.airjoint_list,
            "post_number_lst": self.post_number_lst,
            "posttype_list": self.posttype_list,
            "total_data_list": self.total_data_list,
        }

    def get_pole_positions(self):
        return self.pole_positions

    def get_airjoint_list(self):
        return self.airjoint_list

    def get_post_number_lst(self):
        return self.post_number_lst

    def get_post_type_list(self):
        return self.posttype_list

    def get_total_data_list(self):
        return self.total_data_list


class PoleDataProcessor:
    """전주 위치 데이터를 처리하는 클래스"""

    def __init__(self, pole_data):
        """초기화"""
        self.pole_info = pole_data  # pole_data는 DATA 인스턴스 pole info로 네이밍

    def get_pole_types(self, pole_info, pos, i):
        """전주 타입 및 브래킷 정보를 반환"""
        structure = isbridge_tunnel(pos, pole_info.structure_list)
        curve, _, _ = iscurve(pos, pole_info.curve_list)
        station_data = pole_info.pole_data.get(structure, pole_info.pole_data.get('토공', {}))

        # 곡선/직선에 따라 데이터 선택
        if isinstance(station_data, dict) and '직선' in station_data:
            station_data = station_data.get('곡선' if curve == '곡선' else '직선', {})

        I_type, O_type = station_data.get('I_type', '기본_I_type'), station_data.get('O_type', '기본_O_type')
        I_bracket, O_bracket = station_data.get('I_bracket', '기본_I_bracket'), station_data.get('O_bracket',
                                                                                               '기본_O_bracket')

        is_I_type = (i % 2 == 1) if pole_info.mode == 1 else (
                get_current_post_type(pos, pole_info.post_type_list) == 'I')
        pole_type, bracket_type = (I_type, I_bracket) if is_I_type else (O_type, O_bracket)

        if pole_info.LINENUM == 2:  # 복선이면 상선 전주 타입 반대로 설정
            pole_type2, bracket_type2 = (O_type, O_bracket) if is_I_type else (I_type, I_bracket)
        else:
            pole_type2, bracket_type2 = None, None  # 단선이면 사용 안 함

        return pole_type, bracket_type, pole_type2, bracket_type2, structure, curve

    def process_normal_pole(self, pole_info, pos, structure, curve, pole_type,
                            bracket_type, pole_type2, bracket_type2, lines):
        """일반 전주 처리"""
        lines.append(f"\n,;-----일반개소({structure})({curve})-----\n")
        for line_idx in range(pole_info.LINENUM):
            suffix = "상선" if line_idx == 1 else "하선"
            angle = pole_info.line1_angle if line_idx == 0 else pole_info.line2_angle
            lines.append(f",;{suffix}\n")
            line_str = "".join([
                f"{pos},.freeobj {line_idx};",
                f"{pole_type if line_idx == 0 else pole_type2};0;0;{angle};,;",
                f"{bracket_type if line_idx == 0 else bracket_type2}\n"
            ])
            lines.append(line_str)

    def process_pole_data(self):
        """전주 데이터 처리"""
        lines = []  # 최종 데이터 리스트
        pole_info = self.pole_info
        positions = pole_info.positions
        post_numbers = pole_info.post_numbers
        airjoint_list = pole_info.airjoint_list

        for i in range(len(positions) - 1):
            pos, next_pos = positions[i], positions[i + 1]
            post_number = self.find_post_number(post_numbers, pos)

            pole_type, bracket_type, pole_type2, bracket_type2, current_structure, current_curve = self.get_pole_types(
                pole_info, pos, i)
            _, _, _, _, next_structure, _ = self.get_pole_types(pole_info, next_pos, i)
            current_airjoint = check_isairjoint(pos, airjoint_list)

            lines.append(f"\n,;{post_number}")  # 전주 번호 추가
            if current_airjoint:
                pass
                '''
                self.process_airjoint_pole(pole_info, pos, next_pos, current_structure, next_structure, current_curve,
                                           pole_type, bracket_type, pole_type2, bracket_type2, current_airjoint,
                                           lines)
                '''
            else:
                self.process_normal_pole(pole_info, pos, current_structure, current_curve,
                                         pole_type, bracket_type, pole_type2, bracket_type2, lines)

        return lines

    def process_wire_data(self):
        pass

    @staticmethod
    def find_post_number(lst, pos):
        for arg in lst:
            if arg[0] == pos:
                return arg[1]

    def process_airjoint_pole(self, pole_info, pos, next_pos, current_structure, next_structure, current_curve,
                              pole_type, bracket_type, pole_type2, bracket_type2, current_airjoint, lines):
        """에어조인트 구간별 전주 데이터 생성"""
        lines = []
        sign1 = pole_info.line1_pole_direction  # 하선 부호
        sign2 = pole_info.line2_pole_direction  # 상선 부호
        angle1 = 0 if sign1 == -1 else 180  # 하선 각도
        angle2 = 0 if sign2 == -1 else 180  # 상선 각도

        # 데이터 가져오기
        airjoint_fitting, flat_fitting, steady_arm_fitting, \
            mast_type, mast_name, offset = self.get_fitting_and_mast_data(current_structure, bracket_type)
        bracket_values, f_values = get_bracket_codes(DESIGNSPEED, current_structure)

        # 구조물별 건식게이지 값(절대값)
        gauge = get_pole_gauge(DESIGNSPEED, current_structure)
        next_gauge = get_pole_gauge(DESIGNSPEED, next_structure)

        # 건식게이지에 선별 방향 적용
        gauge = gauge * sign1
        next_gauge = next_gauge * sign1

        bracket_code_start, bracket_code_end = bracket_values
        f_code_start, f_code_end = f_values

        # 공통구문 sta ;-----에어조인트 시작점 (1호주)-----
        add_pole(lines, pos, current_airjoint)

        # 급전선 설비 인덱스 가져오기
        feeder_idx = get_feeder_insulator_idx(DESIGNSPEED, current_structure)

        # 평행틀 설비 인덱스 가져오기
        spreader_name, spreader_idx = get_spreader_idx(DESIGNSPEED, current_structure, current_airjoint)

        # 공통 텍스트(전주,급전선,평행틀
        if current_airjoint in [AirJoint.POINT_2.value, AirJoint.MIDDLE.value, AirJoint.POINT_4.value]:
            for line_idx in range(LINECOUNT):
                gauge = gauge if line_idx == 0 else gauge * -1  # 이미 부호가 적용되어있음

                common_lines(lines, mast_type, gauge, mast_name, feeder_idx, spreader_name, spreader_idx, line_idx)

            # 모든 필요한 값들을 딕셔너리로 묶어서 전달
        params = create_dic(pole_info.polyline_with_sta, current_airjoint, lines, pos, next_pos, DESIGNSPEED,
                            airjoint_fitting,
                            steady_arm_fitting,
                            flat_fitting, pole_type, pole_type2, bracket_type, bracket_type2, offset,
                            f_code_start, f_code_end, bracket_code_start, bracket_code_end,
                            current_structure, next_structure, gauge, next_gauge, pole_info.line1_pole_direction,
                            pole_info.line2_pole_direction, LINECOUNT)

        # 에어조인트 구간별 처리(2호주 ,3호주, 4호주)
        brackets_processor = BracketsProcessor(self)

    def get_fitting_and_mast_data(self, current_structure, bracket_type):
        """금구류 및 전주 데이터를 가져옴"""
        fitting_data = get_airjoint_fitting_data().get(DESIGNSPEED, {})
        airjoint_fitting = fitting_data.get('에어조인트', 0)
        flat_fitting = fitting_data.get('FLAT', (0, 0))
        steady_arm_fitting = fitting_data.get('곡선당김금구', (0, 0))

        mast_type, mast_name = get_mast_type(DESIGNSPEED, current_structure)

        offset = get_pole_gauge(DESIGNSPEED, current_structure)

        return airjoint_fitting, flat_fitting, steady_arm_fitting, mast_type, mast_name, offset

    def get_bracket_codes(DESIGNSPEED, current_structure):
        """브래킷 코드 가져오기"""
        airjoint_data = get_airjoint_bracket_data().get(DESIGNSPEED, {})
        f_data = get_F_bracket_data().get(DESIGNSPEED, {})

        bracket_values = airjoint_data.get(current_structure, (0, 0))
        f_values = f_data.get(current_structure, (0, 0))

        return bracket_values, f_values
