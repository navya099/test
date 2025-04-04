import sys
import random
from tkinter import messagebox
from enum import Enum
import pandas as pd

sys.path.append(r"..\BVEParser")
from BVEclass import Vector3  # BVE CLASS Vector3로드
from loggermodule import logger
from filemodule import TxTFileHandler
from util import *


class AirJoint(Enum):
    START = "에어조인트 시작점 (1호주)"
    POINT_2 = "에어조인트 (2호주)"
    MIDDLE = "에어조인트 중간주 (3호주)"
    POINT_4 = "에어조인트 (4호주)"
    END = "에어조인트 끝점 (5호주)"


class PolePositionManager:
    def __init__(self, params):
        self.params = params

        # ✅ 첫 번째 요소는 design_params (딕셔너리)
        self.design_params = self.params[0]  # unpack 1
        # ✅ 딕셔너리를 활용하여 안전하게 언패킹
        self.designspeed = self.design_params.get("designspeed", 250)
        self.linecount = self.design_params.get("linecount", 1)
        self.lineoffset = self.design_params.get("lineoffset", 0.0)
        self.poledirection = self.design_params.get("poledirection", -1)
        self.mode = self.design_params.get("mode", 0)

        # ✅ 두 번째 요소는 list_params (리스트)
        self.list_params = self.params[1]
        if len(self.list_params) >= 4:
            self.curve_list = self.list_params[0]
            self.pitch_list = self.list_params[1]
            self.coord_list = self.list_params[2]
            self.struct_list = self.list_params[3]
            self.end_km = self.list_params[4]

        else:
            logger.error("list_params의 길이가 4보다 작음")
            self.curve_list = []
            self.pitch_list = []
            self.coord_list = []
            self.struct_list = []
            self.end_km = 600.00  # 예외발생시 600

        self.pole_positions = []
        self.airjoint_list = []
        self.post_number_lst = []
        self.posttype_list = []
        self.total_data_list = []
        self.poledata = None

    def run(self):
        self.generate_positions()
        self.create_pole()

    def generate_positions(self):
        if self.mode == 1:  # 새 노선용
            self.pole_positions = self.distribute_pole_spacing_flexible(0, self.end_km, spans=(45, 50, 55, 60))
            self.airjoint_list = self.define_airjoint_section(self.pole_positions)
            self.post_number_lst = self.generate_postnumbers(self.pole_positions)
        else:  # mode 0  기존 노선용
            # Load from file
            messagebox.showinfo('파일 선택', '사용자 정의 전주파일을 선택해주세요')

            self.load_pole_positions_from_file()
            logger.info('사용자 정의 전주파일이 입력되었습니다.')

    def get_pole_data(self):
        logger.debug(f"📢 get_pole_data() 호출됨 - 반환 값: {self.poledata}")
        return self.poledata

    def create_pole(self):
        """전주 위치 데이터를 가공"""

        data = PoleDATAManager()  # 인스턴스 생성
        for i in range(len(self.pole_positions) - 1):
            pos = self.pole_positions[i]  # 전주 위치 station
            next_pos = self.pole_positions[i + 1]  # 다음 전주 위치 station

            data.poles[i].pos = pos  # 속성에 추가

            current_span = next_pos - pos  # 현재 전주 span
            data.poles[i].span = current_span  # 속성에 추가
            # 현재 위치의 구조물 및 곡선 정보 가져오기
            current_structure = isbridge_tunnel(pos, self.struct_list)
            data.poles[i].current_structure = current_structure  # 현재 전주 위치의 구조물
            current_curve, r, c = iscurve(pos, self.curve_list)
            data.poles[i].current_curve = current_curve
            data.poles[i].radius = r
            data.poles[i].cant = c

            current_slope, pitch = isslope(pos, self.pitch_list)
            data.poles[i].current_pitch = pitch

            current_airjoint = check_isairjoint(pos, self.airjoint_list)
            data.poles[i].current_airjoint = current_airjoint

            post_number = find_post_number(self.post_number_lst, pos)
            data.poles[i].post_number = post_number

            # final
            block = PoleDATA()  # 폴 블록 생성
            data.poles.append(block)

        self.poledata = data
        if self.poledata is None:
            logger.error("🚨 self.poledata가 None입니다! 데이터 생성에 실패했습니다.")
        else:
            logger.debug(f"✅ self.poledata가 정상적으로 생성되었습니다. 전주 개수: {len(self.poledata.poles)}")

    @staticmethod
    def generate_postnumbers(lst):
        postnumbers = []
        prev_km = -1
        count = 0

        for number in lst:
            km = number // 1000  # 1000으로 나눈 몫이 같은 구간
            if km == prev_km:
                count += 1  # 같은 구간에서 숫자 증가
            else:
                prev_km = km
                count = 1  # 새로운 구간이므로 count를 0으로 초기화

            postnumbers.append((number, f'{km}-{count}'))

        return postnumbers

    def load_pole_positions_from_file(self) -> None:
        """txt 파일을 읽고 곧바로 '측점', '전주번호', '타입', '에어조인트' 정보를 반환하는 함수"""

        data_list = []
        positions = []
        post_number_list = []
        type_list = []
        airjoint_list = []

        # 텍스트 파일(.txt) 읽기
        txtfile_handler = TxTFileHandler()
        txtfile_handler.select_file("미리 정의된 전주 파일 선택", [("txt files", "*.txt"), ("All files", "*.*")])
        txt_filepath = txtfile_handler.get_filepath()

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

    @staticmethod
    def distribute_pole_spacing_flexible(start_km, end_km, spans=()):
        """
        45, 50, 55, 60m 범위에서 전주 간격을 균형 있게 배분하여 전체 구간을 채우는 함수
        마지막 전주는 종점보다 약간 앞에 위치할 수도 있음.

        :param start_km: 시작점 (km 단위)
        :param end_km: 끝점 (km 단위)
        :param spans: 사용 가능한 전주 간격 리스트 (기본값: 45, 50, 55, 60)
        :return: 전주 간격 리스트, 전주 위치 리스트
        """
        start_m = int(start_km * 1000)  # km → m 변환
        end_m = int(end_km * 1000)

        positions = [start_m]
        selected_spans = []
        current_pos = start_m

        while current_pos < end_m:
            possible_spans = list(spans)  # 사용 가능한 간격 리스트 (45, 50, 55, 60)
            random.shuffle(possible_spans)  # 랜덤 배치

            for span in possible_spans:
                if current_pos + span > end_m:
                    continue  # 종점을 넘어서면 다른 간격을 선택

                positions.append(current_pos + span)
                selected_spans.append(span)
                current_pos += span
                break  # 하나 선택하면 다음으로 이동

            # 더 이상 배치할 간격이 없으면 종료
            if current_pos + min(spans) > end_m:
                break

        return positions

    @staticmethod
    def define_airjoint_section(positions):
        airjoint_list = []  # 결과 리스트
        airjoint_span = 1600  # 에어조인트 설치 간격(m)

        def is_near_multiple_of_number(number, tolerance=100):
            """주어진 수가 1200의 배수에 근사하는지 판별하는 함수"""
            remainder = number % airjoint_span
            return number > airjoint_span and (remainder <= tolerance or remainder >= (airjoint_span - tolerance))

        i = 0  # 인덱스 변수
        while i < len(positions) - 1:  # 마지막 전주는 제외
            pos = positions[i]  # 현재 전주 위치

            if is_near_multiple_of_number(pos):  # 조건 충족 시
                next_values = positions[i + 1:min(i + 6, len(positions))]  # 다음 5개 값 가져오기
                tags = [
                    AirJoint.START.value,
                    AirJoint.POINT_2.value,
                    AirJoint.MIDDLE.value,
                    AirJoint.POINT_4.value,
                    AirJoint.END.value
                ]

                # (전주 위치, 태그) 쌍을 리스트에 추가 (최대 5개까지만)
                airjoint_list.extend(list(zip(next_values, tags[:len(next_values)])))

                # 다음 5개의 값을 가져왔으므로 인덱스를 건너뛰기
                i += 5
            else:
                i += 1  # 조건이 맞지 않으면 한 칸씩 이동

        return airjoint_list


class PoleDATAManager:  # 전체 총괄
    def __init__(self):
        self.poles = []  # 개별 pole 데어터를 저장할 리스트
        pole = PoleDATA()
        self.poles.append(pole)


class PoleDATA:  # 기둥 브래킷 금구류 포함 데이터
    def __init__(self):
        self.mast = MastDATA()  # 기둥 요소
        self.Brackets = []  # 브래킷을 담을 리스트
        bracketdata = BracketElement()  # 인스턴스 생성
        self.Brackets.append(bracketdata)  # 리스트에 인스턴스 추가
        self.pos = 0.0  # station
        self.post_number = ''
        self.current_curve = ''
        self.radius = 0.0
        self.cant = 0.0
        self.current_structure = ''
        self.current_pitch = 0.0
        self.current_airjoint = ''
        self.gauge = 0.0
        self.span = 0.0
        self.coord = Vector3(0, 0, 0)
        self.ispreader = False


class BracketElement:
    def __init__(self):
        self.name = ''
        self.index = 0
        self.type = ''
        self.positionx = 0.0
        self.positiony = 0.0


class MastDATA:
    def __init__(self):
        self.name = ''
        self.index = 0
        self.type = ''
        self.height = 0.0
        self.width = 0.0
        self.fundermentalindex = 0
        self.fundermentaltype = ''
        self.fundermentaldimension = 0.0


class FeederDATA:
    def __init__(self):
        self.name = ''
        self.index = 0
        self.x = 0.0
        self.y = 0.0


class BaseManager:
    """MastManager와 BracketManager의 공통 기능을 관리하는 부모 클래스"""

    def __init__(self, params, poledata):
        self.poledata = poledata  # ✅ PoleDATAManager.poledata 인스턴스를 가져옴
        self.params = params  # ✅ DataLoader.params 인스턴스를 가져옴

        # ✅ 첫 번째 요소는 design_params (딕셔너리)
        self.design_params = self.params[0]  # unpack 1
        # ✅ 딕셔너리를 활용하여 안전하게 언패킹
        self.designspeed = self.design_params.get("designspeed", 250)
        self.linecount = self.design_params.get("linecount", 1)
        self.lineoffset = self.design_params.get("lineoffset", 0.0)
        self.poledirection = self.design_params.get("poledirection", -1)
        self.mode = self.design_params.get("mode", 0)


class MastManager(BaseManager):
    """전주(Mast) 데이터를 설정하는 클래스"""
    def run(self):
        self.create_mast()

    def create_mast(self):
        data = self.poledata
        for i in range(len(data.poles) - 1):
            current_structure = data.poles[i].current_structure
            mast_index, mast_name = get_mast_type(self.designspeed, current_structure)
            data.poles[i].mast.name = mast_name
            data.poles[i].mast.index = mast_index


class BracketManager(BaseManager):
    def __init__(self, params, poledata):
        super().__init__(params, poledata)
        self.dictionaryofbracket = Dictionaryofbracket()  # 브래킷 데이터 클래스 가져오기

    def run(self):
        self.create_bracket()

    def get_brackettype(self, speed, installtype, gauge, name):
        """브래킷 정보를 반환"""
        return self.dictionaryofbracket.get_bracket_number(speed, installtype, gauge, name)

    def create_bracket(self):
        data = self.poledata

        install_type = None
        gauge = None

        current_type = None

        for i in range(len(data.poles) - 1):
            if self.mode == 0:  # 기존 노선용
                bracket_index = 0
            else:
                is_i_type = (i % 2 == 1)  # bool
                if is_i_type:
                    current_type = 'I'
                    bracket_name = 'inner'
                else:
                    current_type = 'O'
                    bracket_name = 'outer'
                data.poles[i].Brackets[0].type = current_type  # 속성지정
                current_structure = data.poles[i].current_structure  # 찾을수 없는 속성
                if current_structure == '토공':
                    install_type = 'OpG'
                    gauge = 3.0
                elif current_structure == '교량':
                    install_type = 'OpG'
                    gauge = 3.5
                elif current_structure == '터널':
                    install_type = 'Tn'
                    gauge = 2.1
                bracket_index = self.get_brackettype(self.designspeed, install_type, gauge, bracket_name)
            bracket_full_name = f'CaKo{self.designspeed}-{install_type}{gauge}-{current_type}'
            data.poles[i].Brackets[0].name = bracket_full_name  # 속성지정
            data.poles[i].Brackets[0].index = bracket_index  # 속성지정
