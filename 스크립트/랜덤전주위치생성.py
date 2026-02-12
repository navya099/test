import random
from dataclasses import dataclass, field
from functools import lru_cache
from tkinter.filedialog import asksaveasfilename
import os
import json
import re
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import math
from enum import Enum
from tkinter import ttk, messagebox
import copy
from matplotlib import pyplot as plt
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

'''
ver 2026.02.08
클래스화리팩토링 준공
'''

#전역변수
elevation_cache = {}
interpolation_cache = {}

#데이터클래스 정의
@dataclass
class Mast:
    name: str
    index: int
    offset: float

@dataclass
class FittingDATA:
    index: int
    offset: tuple[float, float] = (0, 0)
    label: str = ""

@dataclass
class BracketDATA:
    bracket_type: str
    index: int
    offset: tuple[float, float] = (0, 0)
    bracket_name: str = ""
    fittings: list[FittingDATA] = field(default_factory=list)

@dataclass
class EquipmentDATA:
    name: str
    index: int
    offset: tuple[float, float] = (0, 0)
    rotation: float = 0.0

@dataclass
class PoleDATA:
    post_number: str
    pos: int
    next_pos: int
    span: int
    gauge: float
    next_gauge: float
    structure: str
    next_structure: str
    radius: float
    cant: float
    pitch: float
    section: str
    z: float
    next_z: float
    mast: Mast
    brackets: list[BracketDATA] = field(default_factory=list)
    equipments: list[EquipmentDATA] = field(default_factory=list)
    base_type: str = ''
    next_base_type: str = ''
    coord: tuple[float, float] = (0, 0)

@dataclass
class AirjointDataContext:
    airjoint_fitting: int
    flat_fitting: list
    steady_arm_fitting: list
    mast_type: int
    mast_name: str
    aj_bracket_values: list
    f_bracket_valuse: list
    feeder_idx: int
    spreader_name: str
    spreader_idx: int
    f_bracket_height: float

@dataclass
class SingleWire:
    """한 개의 wire 객체"""
    index: int                # 전선 인덱스
    offset: tuple[float, float] = (0, 0)  # (x, y) 오프셋
    adjusted_angle: float = 0.0           # 평면각도
    topdown_angle: float = 0.0            # 상하각도
    label: str = ""                       # 전선 이름 (급전선, FPW, 특고압 등)
    station: float = None
@dataclass
class WireData:
    """한 pos에 여러 wire를 담는 컨테이너"""
    pos: int
    span: int
    wires: list[SingleWire]
    def add_wire(self, wire: SingleWire):
        self.wires.append(wire)

@dataclass
class WireHnadlerConext:
    """WireHandler용 Conext"""

class AirJoint(Enum):
    START = "에어조인트 시작점 (1호주)"
    POINT_2 = "에어조인트 (2호주)"
    MIDDLE = "에어조인트 중간주 (3호주)"
    POINT_4 = "에어조인트 (4호주)"
    END = "에어조인트 끝점 (5호주)"

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

class BVECSV:
    """BVE CSV 구문을 생성하는 클래스
    Attributes:
        poledata (PoleDATAManager): PoleDATAManager.poledata 인스턴스
        wiredata (WireDataManager): WireDataManager.wiredata 인스턴스
        lines (list[str]]): 구문 정보를 저장할 문자열 리스트
    """

    def __init__(self, poledata=None, wiredata=None):
        self.poledata = poledata  # ✅ PoleDATAManager.poledata 인스턴스를 가져옴
        self.wiredata = wiredata
        self.lines = []

    def create_pole_csv(self):
        """전주 구문 생성 메서드"""
        self.lines = []

        for pole in self.poledata:
            try:
                pos = pole.pos
                post_number = pole.post_number
                section = pole.section
                structure = pole.structure
                curve = '직선' if pole.radius == 0.0 else '곡선'
                gauge = pole.gauge
                equipments = pole.equipments

                section_label = section if section else '일반개소'

                # 구문 작성
                self.lines.append(f',;{post_number}\n')
                self.lines.append(f',;-----{section_label}({structure})({curve})-----\n')

                if section is None:
                    # 일반개소
                    br = pole.brackets[0]
                    self.lines.append(f'{pos},.freeobj 0;{br.index};,;{br.bracket_name}\n')

                elif section in ['에어조인트 시작점 (1호주)', '에어조인트 끝점 (5호주)']:
                    br = pole.brackets[0]
                    eq = equipments[0]
                    self.lines.append(f'{pos},.freeobj 0;{br.index};,;{br.bracket_name}\n')
                    self.lines.append(
                        f'{pos},.freeobj 0;{eq.index};{eq.offset[0]};{eq.offset[1]};{eq.rotation};,;{eq.name}\n')

                elif section in ['에어조인트 (2호주)', '에어조인트 중간주 (3호주)', '에어조인트 (4호주)']:
                    if section in ['에어조인트 (2호주)', '에어조인트 (4호주)']:
                        poss  =  pos - 0.528, pos + 0.528
                    elif section == '에어조인트 중간주 (3호주)':
                        poss = pos - 0.8, pos + 0.8

                    mast = pole.mast
                    eqs = pole.equipments
                    brs = pole.brackets
                    self.lines.append(f'{pos},.freeobj 0;{mast.index};{mast.offset};,;{mast.name}\n')
                    for eq in eqs:
                        self.lines.append(
                            f'{pos},.freeobj 0;{eq.index};{eq.offset[0]};{eq.offset[1]};{eq.rotation};,;{eq.name}\n')
                    for pos, br in zip(poss, brs):
                        self.lines.append(',;가동브래킷구문\n')
                        self.lines.append(f'{pos},.freeobj 0;{br.index};{br.offset[0]};{br.offset[1]};0;,;{br.bracket_name}\n')
                        for fit in br.fittings:
                            self.lines.append(
                                f'{pos},.freeobj 0;{fit.index};{fit.offset[0]};{fit.offset[1]};0;,;{fit.label}\n')
            except AttributeError as e:
                print(f"poledata 데이터 누락: {pos}, 오류: {e}")
            except Exception as e:
                print(f"예상치 못한 오류: {pos}, 오류: {e}")

        print('create_pole_csv 실행이 완료됐습니다.')
        return self.lines

    def create_wire_csv(self):
        """
        전선 구문 생성 메서드
        """
        self.lines = []  # 코드 실행전 초기화
        for pole, wire in zip(self.poledata, self.wiredata):
            try:
                pos = pole.pos
                post_number = pole.post_number
                section = pole.section
                structure = pole.structure
                curve = '직선' if pole.radius == 0.0 else '곡선'
                section_label = section if section else '일반개소'

                # 구문 작성
                self.lines.append(f',;{post_number}\n')
                self.lines.append(f',;-----{section_label}({structure})({curve})-----\n')

                for wr in wire.wires:
                    sta = wr.station if wr.station else pos
                    self.lines.append(f'{sta},.freeobj 0;{wr.index};{wr.offset[0]};{wr.offset[1]};{wr.adjusted_angle};{wr.topdown_angle};0;,;{wr.label}\n')

            except AttributeError as e:
                print(f"Wire 데이터 누락: index {pos}, 오류: {e}")
            except Exception as e:
                print(f"예상치 못한 오류: index {pos}, 오류: {e}")

        print(f'create_wire_csv실행이 완료됐습니다.')
        return self.lines

def distribute_pole_spacing_flexible(start_km, end_km, spans=(45, 50, 55, 60)):
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

    return selected_spans, positions


# 전주번호 추가함수
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

def find_structure_section(filepath):
    """xlsx 파일을 읽고 교량과 터널 정보를 반환하는 함수"""
    structure_list = {'bridge': [], 'tunnel': []}

    # xlsx 파일 읽기
    df_bridge = pd.read_excel(filepath, sheet_name='교량', header=None)
    df_tunnel = pd.read_excel(filepath, sheet_name='터널', header=None)

    # 열 개수 확인
    print(df_tunnel.shape)  # (행 개수, 열 개수)
    print(df_tunnel.head())  # 데이터 확인

    # 첫 번째 행을 열 제목으로 설정
    df_bridge.columns = ['br_NAME', 'br_START_STA', 'br_END_STA', 'br_LENGTH']
    df_tunnel.columns = ['tn_NAME', 'tn_START_STA', 'tn_END_STA', 'tn_LENGTH']

    # 교량 구간과 터널 구간 정보
    for _, row in df_bridge.iterrows():
        structure_list['bridge'].append((row['br_NAME'], row['br_START_STA'], row['br_END_STA']))

    for _, row in df_tunnel.iterrows():
        structure_list['tunnel'].append((row['tn_NAME'], row['tn_START_STA'], row['tn_END_STA']))

    return structure_list

def find_curve_section(txt_filepath='curveinfo.txt'):
    """txt 파일을 읽고 곧바로 측점(sta)과 곡선반경(radius) 정보를 반환하는 함수"""

    curve_list = []

    # 텍스트 파일(.txt) 읽기
    df_curve = pd.read_csv(txt_filepath, sep=",", header=None, names=['sta', 'radius', 'cant'])

    # 곡선 구간 정보 저장
    for _, row in df_curve.iterrows():
        curve_list.append((row['sta'], row['radius'], row['cant']))

    return curve_list


def find_pitch_section(txt_filepath='pitchinfo.txt'):
    """txt 파일을 읽고 곧바로 측점(sta)과 기울기(pitch) 정보를 반환하는 함수"""

    curve_list = []

    # 텍스트 파일(.txt) 읽기
    df_curve = pd.read_csv(txt_filepath, sep=",", header=None, names=['sta', 'radius'])

    # 곡선 구간 정보 저장
    for _, row in df_curve.iterrows():
        curve_list.append((row['sta'], row['radius']))

    return curve_list

def isbridge_tunnel(sta, structure_list):
    """sta가 교량/터널/토공 구간에 해당하는지 구분하는 함수"""
    for name, start, end in structure_list['bridge']:
        if start <= sta <= end:
            return '교량'

    for name, start, end in structure_list['tunnel']:
        if start <= sta <= end:
            return '터널'

    return '토공'


def iscurve(cur_sta, curve_list):
    """sta가 곡선 구간에 해당하는지 구분하는 함수"""
    rounded_sta = get_block_index(cur_sta)  # 25 단위로 반올림

    for sta, R, c in curve_list:
        if rounded_sta == sta:
            if R == 0:
                return '직선', 0, 0  # 반경이 0이면 직선
            return '곡선', R, c  # 반경이 존재하면 곡선

    return '직선', 0, 0  # 목록에 없으면 기본적으로 직선 처리


def isslope(cur_sta, curve_list):
    """sta가 곡선 구간에 해당하는지 구분하는 함수"""
    rounded_sta = get_block_index(cur_sta)  # 25 단위로 반올림

    for sta, g in curve_list:
        if rounded_sta == sta:
            if g == 0:
                return '수평', 0  # 반경이 0이면 직선
            else:
                return '기울기', f'{g * 1000:.2f}'

    return '수평', 0  # 목록에 없으면 기본적으로 직선 처리

def define_airjoint_section(positions, airjoint_span):
    airjoint_list = []  # 결과 리스트

    def is_near_multiple_of_DIG(number, tolerance=100):
        """주어진 수가 1200의 배수에 근사하는지 판별하는 함수"""
        remainder = number % airjoint_span
        return number > airjoint_span and (remainder <= tolerance or remainder >= (airjoint_span - tolerance))

    i = 0  # 인덱스 변수
    while i < len(positions) - 1:  # 마지막 전주는 제외
        pos = positions[i]  # 현재 전주 위치

        if is_near_multiple_of_DIG(pos):  # 조건 충족 시
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


def check_isairjoint(input_sta, airjoint_list):
    for data in airjoint_list:
        sta, tag = data
        if input_sta == sta:
            return tag


def write_to_file(filename, lines):
    """리스트 데이터를 파일에 저장하는 함수"""
    try:
        # 디렉토리 자동 생성
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(lines)  # 리스트 데이터를 한 번에 파일에 작성

        print(f"✅ 파일 저장 완료: {filename}")
    except Exception as e:
        print(f"⚠️ 파일 저장 중 오류 발생: {e}")



class AirJointProcessor:
    def __init__(self):
        self.poles = []

    def process_airjoint(self, pole, polyline_with_sta, dataprocessor):
        """에어조인트 구간별 전주 데이터 생성"""
        # 데이터 가져오기
        airjoint_fitting, flat_fitting, steady_arm_fitting, mast_type, mast_name = dataprocessor.get_fitting_and_mast_data(
            pole.structure)
        aj_bracket_values, f_bracket_valuse = dataprocessor.get_bracket_codes(pole.structure)

        # 급전선 설비 인덱스 가져오기
        feeder_idx = dataprocessor.get_feeder_insulator_idx(pole.structure)

        # 평행틀 설비 인덱스 가져오기
        spreader_name, spreader_idx = dataprocessor.get_spreader_idx(pole.structure, pole.section)
        #F브래킷 인상높이
        f_bracket_height = dataprocessor.get_f_bracket_height()

        # 모든 필요한 값들을 전달
        context = AirjointDataContext(
            airjoint_fitting=airjoint_fitting,
            flat_fitting=flat_fitting,
            steady_arm_fitting=steady_arm_fitting,
            mast_type=mast_type,
            mast_name=mast_name,
            aj_bracket_values=aj_bracket_values,
            f_bracket_valuse=f_bracket_valuse,
            feeder_idx=feeder_idx,
            spreader_name=spreader_name,
            spreader_idx=spreader_idx,
            f_bracket_height=f_bracket_height
        )
        # 에어조인트 구간별 처리(2호주 ,3호주, 4호주)
        adder = AirjointBracketAdder(context, dataprocessor)
        adder.add_airjoint_brackets(pole, polyline_with_sta)

class AirjointBracketAdder:
    def __init__(self, params: AirjointDataContext ,dataprocessor):
        self.params = params
        self.prosc = dataprocessor

    def add_airjoint_brackets(self, pole: PoleDATA, polyline_with_sta):
        """에어조인트 각 구간별 브래킷 추가"""
        if pole.section == AirJoint.START.value:
            # START 구간 처리
            x1, y1 = self.prosc.get_bracket_coordinates('F형_시점')
            start_angle = calculate_curve_angle(polyline_with_sta, pole.pos, pole.next_pos, pole.gauge, x1)
            pole.equipments.append(EquipmentDATA(name='스프링식 장력조절장치', index=1247, offset=(pole.gauge,0),rotation=start_angle))

        elif pole.section == AirJoint.POINT_2.value:
            # POINT_2 구간 처리
            self.add_common_equipts(pole)
            self.add_F_and_AJ_brackets(pole)

        elif pole.section == AirJoint.MIDDLE.value:
            # MIDDLE 구간 처리
            self.add_common_equipts(pole)
            self.add_AJ_brackets_middle(pole)

        elif pole.section == AirJoint.POINT_4.value:
            # POINT_4 구간 처리
            self.add_common_equipts(pole)
            self.add_F_and_AJ_brackets(pole, end=True)

        elif pole.section == AirJoint.END.value:
            # END 구간 처리
            x5, y5 = self.prosc.get_bracket_coordinates('F형_끝')
            end_angle = calculate_curve_angle(polyline_with_sta, pole.pos, pole.next_pos, x5, pole.next_gauge,start=False)
            pole.equipments.append(EquipmentDATA(name='스프링식 장력조절장치', index=1247, offset=(pole.gauge,0),rotation=180 + end_angle))



    def add_F_and_AJ_brackets(self, pole, end=False):
        """F형 및 AJ형 브래킷을 추가하는 공통 함수"""
        f_i, f_o = self.params.f_bracket_valuse
        aj_i,aj_o = self.params.aj_bracket_values
        #기본 브래킷 제거
        pole.brackets.clear()
        # F형 가동 브래킷 추가
        x1, y1 = self.prosc.get_bracket_coordinates('F형_시점' if not end else 'F형_끝')
        self.add_F_bracket(pole, f_i,"가동브래킷 F형", x1, y1)

        # AJ형 가동 브래킷 추가
        x1, y1 = self.prosc.get_bracket_coordinates('AJ형_시점' if not end else 'AJ형_끝')
        self.add_AJ_bracket(pole, aj_i, '가동브래킷 AJ형', x1, y1)

    def add_F_bracket(self, pole: PoleDATA, bracket_code, bracket_name, x1, y1):
        """F형 가동 브래킷 및 금구류 추가"""
        idx1, idx2 = self.params.flat_fitting
        h = self.params.f_bracket_height
        # 브래킷 추가
        bracket = BracketDATA(
            bracket_type='F',
            index=bracket_code,
            bracket_name=bracket_name,
            offset=(0,h)
        )
        # 금구류 추가
        bracket.fittings.append(FittingDATA(index=idx1, label='조가선지지금구-F용', offset=(x1, y1)))
        bracket.fittings.append(FittingDATA(index=idx2, label='전차선지지금구-F용', offset=(x1, y1)))

        # PoleDATA에 브래킷 등록
        pole.brackets.append(bracket)

    def add_AJ_bracket(self, pole: PoleDATA, bracket_code, bracket_name, x1, y1, end=False):
        """AJ형 가동 브래킷 및 금구류 추가"""

        idx1 = self.params.airjoint_fitting
        idx2 = self.params.steady_arm_fitting[0] if not end else self.params.steady_arm_fitting[1]

        # 브래킷 추가
        bracket = BracketDATA(
            bracket_type='AJ',
            index=bracket_code,
            bracket_name=bracket_name,
            offset=(0, y1)
        )
        # 금구류 추가
        bracket.fittings.append(FittingDATA(index=idx1, label='조가선지지금구-AJ용', offset=(x1, y1)))
        bracket.fittings.append(FittingDATA(index=idx2, label='곡선당김금구', offset=(x1, y1)))

        # PoleDATA에 브래킷 등록
        pole.brackets.append(bracket)


    def add_AJ_brackets_middle(self, pole):
        """MIDDLE 구간에서 AJ형 브래킷 추가"""
        # 기본 브래킷 제거
        pole.brackets.clear()

        aj_i, aj_o = self.params.aj_bracket_values
        # AJ형 가동 브래킷 및 금구류 추가
        x1, y1 = self.prosc.get_bracket_coordinates('AJ형_중간1')
        self.add_AJ_bracket(pole, aj_i, '가동브래킷 AJ형', x1, y1)

        # AJ형 가동 브래킷 및 금구류 추가
        x1, y1 = self.prosc.get_bracket_coordinates('AJ형_중간2')
        self.add_AJ_bracket(pole, aj_o, '가동브래킷 AJ형', x1, y1)

    def add_common_equipts(self, pole):
        pole.mast = Mast(self.params.mast_name, self.params.mast_type, pole.gauge)
        feederidx = self.params.feeder_idx
        spreaderidx = self.params.spreader_idx
        pole.equipments.append(
            EquipmentDATA(name='급전선 현수 조립체', index=feederidx, offset=(pole.gauge, 0)))
        pole.equipments.append(
            EquipmentDATA(name='평행틀', index=spreaderidx, offset=(pole.gauge, 0)))

def find_post_number(lst, pos):
    for arg in lst:
        if arg[0] == pos:
            return arg[1]

class PoleProcessor:
    def __init__(self):
        self.poles = []

    def process_pole(self, positions, structure_list, curve_list, pitchlist, dataset, airjoint_list, polyline_with_sta):
        """전주 위치 데이터를 가공 함수"""
        # 전주 데이터 구성
        pole_data = dataset['pole_data']

        # 전주번호
        post_number_lst = generate_postnumbers(positions)
        #dataset처리기
        dataprocessor = DatasetGetter(dataset)
        airjoint_processor = AirJointProcessor()
        for i in range(len(positions) - 1):
            try:
                pos, next_pos = positions[i], positions[i + 1]
                currentspan = next_pos - pos  # 전주 간 거리 계산
                # 현재 위치의 구조물 및 곡선 정보 가져오기
                current_structure = isbridge_tunnel(pos, structure_list)
                next_structure = isbridge_tunnel(next_pos, structure_list)
                current_curve, R, c = iscurve(pos, curve_list)
                current_slope, pitch = isslope(pos, pitchlist)
                z = get_elevation_pos(pos, polyline_with_sta)  # 현재 측점의 z값
                next_z = get_elevation_pos(next_pos, polyline_with_sta)  # 다음 측점의 z값
                current_airjoint = check_isairjoint(pos, airjoint_list)
                post_number = find_post_number(post_number_lst, pos)
                coord, _, v1 = interpolate_cached(polyline_with_sta, pos)

                i_type_index, o_type_index = dataprocessor.get_bracket_type(current_structure, current_curve)

                gauge = dataprocessor.get_pole_gauge(current_structure)
                next_gauge = dataprocessor.get_pole_gauge(next_structure)
                pos_coord_with_offset = calculate_offset_point(v1, coord, gauge)

                # 홀수/짝수에 맞는 전주 데이터 생성
                current_type = 'I' if i % 2 == 1 else 'O'
                next_type = 'O' if current_type == 'I' else 'I'
                pole_type = i_type_index if i % 2 == 1 else o_type_index
                bracket_name =  f"{pole_data['prefix']}-{current_type}"
                bracket = BracketDATA(bracket_type=current_type, index=pole_type, bracket_name=bracket_name)

                pole = PoleDATA(
                    pos=pos,
                    next_pos=next_pos,
                    span=currentspan,
                    gauge=gauge,
                    next_gauge=next_gauge,
                    structure=current_structure,
                    next_structure=next_structure,
                    radius=R,
                    cant=c,
                    pitch=pitch,
                    section=current_airjoint,
                    post_number=post_number,
                    brackets=[bracket],
                    mast=None,
                    equipments=[],
                    z=z,
                    next_z=next_z,
                    base_type=current_type,
                    next_base_type=next_type,
                    coord=pos_coord_with_offset
                )

                if not current_airjoint is None:
                    airjoint_processor.process_airjoint(pole, polyline_with_sta, dataprocessor)
                self.poles.append(pole)
            except Exception as e:
                print(f"process_pole 실행 중 에러 발생: {e}")
        return self.poles

def open_excel_file():
    """파일 선택 대화 상자를 열고, 엑셀 파일 경로를 반환하는 함수"""
    root = tk.Tk()
    root.withdraw()  # Tkinter 창을 숨김
    file_path = filedialog.askopenfilename(
        title="엑셀 파일 선택",
        filetypes=[("Excel Files", "*.xlsx")]
    )

    return file_path

def get_block_index(current_track_position, block_interval=25):
    """현재 트랙 위치를 블록 인덱스로 변환"""
    return math.floor(current_track_position / block_interval + 0.001) * block_interval

class WireProcessor:
    def __init__(self, dataprocessor, polyline_with_sta, poledatas):
        self.pro = dataprocessor
        self.wires = []
        self.com = CommonWireProcessor()
        self.afp = AFWireProcessor(self.pro)
        self.fpwp = FPWWireProcessor(self.pro)
        self.etcp = ExtraWireProcessor(self.pro)
        self.al = polyline_with_sta
        self.polelist = poledatas

    def process_to_wire(self):
        """ 전주 위치에 wire를 배치하는 함수 """
        self.wires.clear()
        wirehandler = WireSectionHandler(self.com ,self.pro ,self.al)
        for pole in self.polelist:
            try:
                pitch_angle = change_permile_to_degree(pole.pitch)
                wire = WireData(pole.pos, pole.span, wires=[])
                #본선 /에어조인트구간 전차선 처리
                wirehandler.run(pole, wire, pitch_angle)
                #AF
                wire.add_wire(self.afp.process(pole, self.al, pitch_angle))
                #fpw
                wire.add_wire(self.fpwp.process(pole, self.al, pitch_angle))

                #추가 전선 처리(extra wire)
                #wire.add_wire(self.etcp.process(pole, self.al, pitch_angle))

                self.wires.append(wire)
            except Exception as e:
                print(f"process_to_WIRE 실행 중 에러 발생: {e}")
                continue
        return self.wires

def get_elevation_pos(pos, polyline_with_sta):
    if pos in elevation_cache:
        return elevation_cache[pos]

    # 범위 체크
    if pos < polyline_with_sta[0][0] or pos > polyline_with_sta[-1][0]:
        raise ValueError(f"pos {pos}가 polyline 범위({polyline_with_sta[0][0]} ~ {polyline_with_sta[-1][0]})를 벗어났습니다.")

    for i in range(len(polyline_with_sta) - 1):
        sta1, x1, y1, z1 = polyline_with_sta[i]
        sta2, x2, y2, z2 = polyline_with_sta[i + 1]
        L = sta2 - sta1
        L_new = pos - sta1

        if sta1 <= pos <= sta2:
            new_z = calculate_height_at_new_distance(z1, z2, L, L_new)
            elevation_cache[pos] = new_z
            return new_z

    raise ValueError(f"pos {pos}에 대한 고도 값을 찾을 수 없습니다.")

def calculate_height_at_new_distance(h1, h2, L, L_new):
    """주어진 거리 L에서의 높이 변화율을 기반으로 새로운 거리 L_new에서의 높이를 계산"""
    h3 = h1 + ((h2 - h1) / L) * L_new
    return h3

def buffered_write(filename, lines):
    """파일 쓰기 버퍼 함수"""
    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(lines)

def get_lateral_offset_and_angle(index, currentspan):
    """ 홀수/짝수 전주에 따른 편위 및 각도 계산 """
    sign = -1 if index % 2 == 1 else 1
    return sign * 0.2, -sign * math.degrees(0.4 / currentspan)

class WireSectionHandler:
    def __init__(self, commonprocessor ,dataprocseor, polyline_with_sta):
        self.compros = commonprocessor
        self.datapro = dataprocseor
        self.al = polyline_with_sta
        self.airpro = AirjointWireProcessor(self.compros, self.datapro, self.al)

    def run(self, pole, wire, pitch_angle):
        """일반개소 및 에어조인트개소 구분처리"""
        sign = -1 if pole.base_type == 'I' else 1
        next_sign = -1 if pole.next_base_type == 'I' else 1
        start_offset = sign * 0.2
        end_offset = next_sign * 0.2
        # 전차선 인덱스 얻기
        cw_index,_,_ = self.datapro.get_wire_span_data(wire.span, pole.structure)

        if pole.section is None:
            self.process_normal_section(pole, wire, pitch_angle, start_offset, end_offset, cw_index)
        else:
            self.process_airjoint_section(pole, wire, pitch_angle, start_offset, cw_index)

    def process_normal_section(self, pole, wire, pitch_angle ,offset1 ,offset2 , index):

        wire.add_wire(self.compros.run(self.al, index ,
            pole.pos, pole.next_pos ,pole.z, pole.next_z, start=(offset1,0)
            ,end=(offset2,0), pitch_angle=pitch_angle, label='전차선'))

    def process_airjoint_section(self, pole, wire, pitch_angle , offset, index):
        self.airpro.run(pole, wire, pitch_angle ,offset, index)

class CommonWireProcessor:
    def __init__(self):
        pass
    def run(self, polyline_with_sta, index ,
            pos, next_pos ,current_z, next_z, start: tuple[float, float], end: tuple[float, float], pitch_angle, label):
        """공통 전선 생성기
        Args:
            polyline_with_sta: 폴리선
            index: 인덱스
            pos: 시작 측점
            next_pos: 끝 측점
            current_z: 현재 z
            next_z: 다음 z
            start: 시작 좌표
            end: 끝 좌표
            pitch_angle: 구배 각도
            label: 라벨
        Returns:
            SingleWire: 전선 객체
        """

        x1, y1 = start
        x2, y2 = end
        currentspan = next_pos - pos
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos,
                                               x1, x2)
        topdown_angle = calculate_slope(current_z + y1,next_z + y2, currentspan) - pitch_angle

        return SingleWire(index=index, offset=start,adjusted_angle=adjusted_angle,topdown_angle=topdown_angle, label=label)

class AirjointWireProcessor:
    def __init__(self, compros: CommonWireProcessor, datap, al):
        self.common = compros
        self.datap = datap
        self.al = al

    def run(self, pole, wire, pitch_angle ,offset, index):
        # 에어조인트 구간 처리
        # 전차선 정보 가져오기
        (contact_object_index, messenger_object_index,
         system_heigh, contact_height) = self.datap.get_contact_wire_and_massanger_wire_info(pole.structure, pole.span)

        # 평행구간 전차선 오프셋
        aj_start_x, aj_start_y = self.datap.get_bracket_coordinates('AJ형_시점')
        f_start_x, f_start_y = self.datap.get_bracket_coordinates('F형_시점')
        aj_middle1_x, aj_middle1_y = self.datap.get_bracket_coordinates('AJ형_중간1')
        aj_middle2_x, aj_middle2_y = self.datap.get_bracket_coordinates('AJ형_중간2')
        aj_end_x, aj_end_y = self.datap.get_bracket_coordinates('AJ형_끝')
        f_end_x, f_end_y = self.datap.get_bracket_coordinates('F형_끝')



        if pole.section == '에어조인트 시작점 (1호주)':
            # 본선
            wire.add_wire(self.common.run(
                self.al, index, pole.pos, pole.next_pos, pole.z, pole.next_z,
                (offset,0),(aj_start_x,0), pitch_angle, label='본선전차선')
            )
            # 무효선
            adjusted_angle = calculate_curve_angle(self.al, pole.pos, pole.next_pos, offset, aj_start_x)#평면각도
            #slope_degree1=전차선 각도, slope_degree2=조가선 각도, H1=전차선높이, H2=조가선 높이
            slope_degree1, slope_degree2, h1, h2, pererall_d, sta2 = initialrize_tenstion_device(
                pole.pos, pole.gauge, pole.span,contact_height,system_heigh, adjusted_angle, f_start_y)

            mw = self.common.run(
                self.al, messenger_object_index, pole.pos, pole.next_pos, pole.z, pole.next_z,
                (pole.gauge,h2),(aj_start_x,contact_height + system_heigh), pitch_angle, label='무효조가선')

            mw.station = sta2
            wire.add_wire(mw)
            cw = self.common.run(
                self.al, messenger_object_index, pole.pos, pole.next_pos, pole.z, pole.next_z,
                (pole.gauge, h1), (aj_start_x, contact_height + f_start_y), pitch_angle, label='무효전차선')
            cw.station = sta2
            wire.add_wire(cw)
        elif pole.section == '에어조인트 (2호주)':
            # 본선
            wire.add_wire(self.common.run(
                self.al, index, pole.pos, pole.next_pos, pole.z, pole.next_z,
                (aj_start_x, 0), (aj_middle2_x, 0), pitch_angle, label='본선전차선')
            )
            # 무효선
            wire.add_wire(self.common.run(
                self.al, index, pole.pos, pole.next_pos, pole.z, pole.next_z,
                (f_start_x, f_start_y), (aj_middle1_x, 0), pitch_angle, label='무효전차선')
            )

        elif pole.section == '에어조인트 중간주 (3호주)':
            # 본선 >무효선 상승
            wire.add_wire(self.common.run(
                self.al, index, pole.pos, pole.next_pos, pole.z, pole.next_z,
                (aj_middle2_y, 0), (f_end_x, f_start_y), pitch_angle, label='본선->무효전차선')
            )
            # 무효선 > 본선
            wire.add_wire(self.common.run(
                self.al, index, pole.pos, pole.next_pos, pole.z, pole.next_z,
                (aj_middle1_x, 0), (aj_end_x, 0), pitch_angle, label='무효->본선전차선')
            )

        elif pole.section == '에어조인트 (4호주)':
            # 본선

            wire.add_wire(self.common.run(
                self.al, index, pole.pos, pole.next_pos, pole.z, pole.next_z,
                (aj_end_x, 0), (-offset, 0), pitch_angle, label='본선전차선')
            )
            # 무효선
            adjusted_angle = calculate_curve_angle(self.al, pole.pos, pole.next_pos, aj_end_x, -offset)  # 평면각도
            # slope_degree1=전차선 각도, slope_degree2=조가선 각도, H1=전차선높이, H2=조가선 높이
            slope_degree1, slope_degree2, h1, h2, pererall_d, sta2 = initialrize_tenstion_device(
                pole.pos, pole.gauge, pole.span, contact_height, system_heigh, adjusted_angle, f_start_y)

            wire.add_wire(self.common.run(
                self.al, messenger_object_index, pole.pos, pole.next_pos, pole.z, pole.next_z,
                (f_end_x, contact_height + system_heigh), (pole.next_gauge, h2), pitch_angle, label='무효조가선')
            )
            wire.add_wire(self.common.run(
                self.al, messenger_object_index, pole.pos, pole.next_pos, pole.z, pole.next_z,
                (f_end_x, contact_height + f_start_y), (pole.next_gauge, h1), pitch_angle, label='무효전차선')
            )
        elif pole.section == '에어조인트 끝점 (5호주)':
            # 본선
            wire.add_wire(self.common.run(
                self.al, index, pole.pos, pole.next_pos, pole.z, pole.next_z,
                (offset, 0), (-offset, 0), pitch_angle, label='본선전차선')
            )
class BaseWireProcessor:
    def __init__(self, dataprocessor):
        self.pro = dataprocessor
        self.common = CommonWireProcessor()

    def process(self, pole: PoleDATA, polyline_with_sta, pitch_angle) -> SingleWire:
        idx, start, end, label = self.collect_data(pole)
        return self.common.run(polyline_with_sta, idx,
                               pole.pos, pole.next_pos,
                               pole.z, pole.next_z,
                               start=start, end=end,
                               pitch_angle=pitch_angle,
                               label=label)

    def collect_data(self, pole: PoleDATA):
        """구체적인 wire별 데이터 수집은 하위 클래스에서 구현"""
        raise NotImplementedError

class AFWireProcessor(BaseWireProcessor):
    def collect_data(self, pole: PoleDATA):
        x_offset, y_offset, _, _ = self.pro.get_wire_offset(pole.structure)
        x_offset_next, y_offset_next, _, _ = self.pro.get_wire_offset(pole.next_structure)
        _,idx,_ = self.pro.get_wire_span_data(pole.span, pole.structure)
        return idx, (x_offset, y_offset), (x_offset_next, y_offset_next), "AF"


class FPWWireProcessor(BaseWireProcessor):
    def collect_data(self, pole: PoleDATA):
        _, _, x_offset, y_offset = self.pro.get_wire_offset(pole.structure)
        _, _, x_offset_next, y_offset_next = self.pro.get_wire_offset(pole.next_structure)
        _, _, idx = self.pro.get_wire_span_data(pole.span, pole.structure)
        return idx, (x_offset, y_offset), (x_offset_next, y_offset_next), "FPW"

class ExtraWireProcessor(BaseWireProcessor):
    def collect_data(self, pole: PoleDATA):
        pass

def change_permile_to_degree(permile):
    """퍼밀 값을 도(degree)로 변환"""
    # 정수 또는 문자열이 들어오면 float으로 변환
    if not isinstance(permile, (int, float)):
        permile = float(permile)

    return math.degrees(math.atan(permile / 1000))  # 퍼밀을 비율로 변환 후 계산


def calculate_slope(h1, h2, gauge):
    """주어진 높이 차이와 수평 거리를 바탕으로 기울기(각도) 계산"""
    slope = (h2 - h1) / gauge  # 기울기 값 (비율)
    return math.degrees(math.atan(slope))  # 아크탄젠트 적용 후 degree 변환

def initialrize_tenstion_device(pos, gauge, currentspan, contact_height, system_heigh, adjusted_angle=0, y=0):
    """장력장치구간 전차선과 조가선 각도 높이를 반환"""
    # 장력장치 치수
    tension_device_length = 7.28

    # 전선 각도
    new_length = currentspan - tension_device_length  # 현재 span에서 장력장치까지의 거리
    pererall_d, vertical_offset = return_new_point(gauge, currentspan, tension_device_length)  # 선형 시작점에서 전선까지의 거리

    sta2 = pos + vertical_offset  # 전선 시작 측점
    h1 = 5.563936  # 장력장치 전차선 높이
    h2 = 6.04784  # 장력장치 조가선 높이

    slope_radian1 = math.atan((h1 - (contact_height + y)) / currentspan)  # 전차선 각도(라디안)
    slope_radian2 = math.atan((h2 - (contact_height + system_heigh)) / currentspan)  # 조가선 각도(라디안)

    slope_degree1 = math.degrees(slope_radian1)  # 전차선 각도(도)
    slope_degree2 = math.degrees(slope_radian2)  # 조가선 각도(도)

    return slope_degree1, slope_degree2, h1, h2, pererall_d, sta2

# 새로운 점 계산 함수
def return_new_point(x, y, L):
    A = (x, 0)  # A점 좌표
    B = (0, 0)  # 원점 B
    C = (0, y)  # C점 좌표
    theta = math.degrees(abs(math.atan(y / x)))
    D = calculate_destination_coordinates(A[0], A[1], theta, L)  # 이동한 D점 좌표
    E = B[0], B[1] + D[1]
    d1 = calculate_distance(D[0], D[1], E[0], E[1])
    d2 = calculate_distance(B[0], B[1], E[0], E[1])

    # 외적을 이용해 좌우 판별
    v_x, v_y = C[0] - B[0], C[1] - B[1]  # 선분 벡터
    w_x, w_y = A[0] - B[0], A[1] - B[1]  # 점에서 선분 시작점까지의 벡터
    cross = v_x * w_y - v_y * w_x  # 외적 계산
    sign = -1 if cross > 0 else 1

    return d1 * sign, d2

def interpolate_cached(polyline_with_sta, pos):


    if pos not in interpolation_cache:
        interpolation_cache[pos] = interpolate_coordinates(polyline_with_sta, pos)
    return interpolation_cache[pos]

def calculate_curve_angle(polyline_with_sta, pos, next_pos, stagger1, stagger2 ,start=True):
    # 캐싱된 보간 사용
    point_a, P_A, vector_a = interpolate_cached(polyline_with_sta, pos)
    point_b, P_B, vector_b = interpolate_cached(polyline_with_sta, next_pos)

    if point_a and point_b:
        offset_point_a = calculate_offset_point(vector_a, point_a, stagger1)
        offset_point_b = calculate_offset_point(vector_b, point_b, stagger2)

        # bearing 계산 (캐싱 적용)
        a_b_angle = calculate_bearing(offset_point_a[0], offset_point_a[1],
                                      offset_point_b[0], offset_point_b[1])
        if start:
            return vector_a - a_b_angle
        else:
            return vector_b - a_b_angle
    return 0.0

def get_airjoint_angle(gauge, stagger, span):
    S_angle = abs(math.degrees((gauge + stagger) / span)) if span != 0 else 0.0
    E_angle = abs(math.degrees((gauge - stagger) / span)) if span != 0 else 0.0

    return S_angle, E_angle

def casting_key_str_to_int(dic):
    return {int(k): v for k, v in dic.items()}




def calculate_distance(x1, y1, x2, y2):
    """두 점 (x1, y1)과 (x2, y2) 사이의 유클리드 거리 계산"""
    return math.hypot(x2 - x1, y2 - y1)  # math.sqrt((x2 - x1)**2 + (y2 - y1)**2)와 동일


def interpolate_coordinates(polyline, target_sta):
    """
    주어진 폴리선 데이터에서 특정 sta 값에 대한 좌표를 선형 보간하여 반환.

    :param polyline: [(sta, x, y, z), ...] 형식의 리스트
    :param target_sta: 찾고자 하는 sta 값
    :return: (x, y, z) 좌표 튜플
    """
    # 정렬된 리스트를 가정하고, 적절한 두 점을 찾아 선형 보간 수행
    for i in range(len(polyline) - 1):
        sta1, x1, y1, z1 = polyline[i]
        sta2, x2, y2, z2 = polyline[i + 1]
        v1 = calculate_bearing(x1, y1, x2, y2)
        # target_sta가 두 점 사이에 있는 경우 보간 수행
        if sta1 <= target_sta < sta2:
            t = abs(target_sta - sta1)
            x, y = calculate_destination_coordinates(x1, y1, v1, t)
            z = z1 + t * (z2 - z1)
            return (x, y, z), (x1, y1, z1), v1

    raise ValueError(f"target_sta {target_sta}가 polyline 범위({polyline[0][0]} ~ {polyline[-1][0]})를 벗어났습니다.")

# 폴리선 좌표 읽기
def read_polyline(file_path):
    points = []
    with open(file_path, 'r') as file:
        for line in file:
            # 쉼표로 구분된 값을 읽어서 float로 변환
            x, y, z = map(float, line.strip().split(','))
            points.append((x, y, z))
    return points

def find_last_block(data):
    """
    데이터 리스트에서 마지막 블록 번호(첫 번째 숫자)를 반환.
    예: ['45676,500,0','4646,366,35'] → 4646
    """
    last_block = None

    for line in data:
        if isinstance(line, str):
            # 문자열 맨 앞의 숫자만 추출 (콤마 앞까지)
            match = re.match(r'(\d+)', line)
            if match:
                last_block = int(match.group(1))

    return last_block

def read_file():
    root = tk.Tk()
    root.withdraw()  # Tkinter 창을 숨김
    file_path = filedialog.askopenfilename(defaultextension=".txt",
                                           filetypes=[("txt files", "curve_info.txt"), ("All files", "*.*")])

    if not file_path:
        print("파일을 선택하지 않았습니다.")
        return []

    print('현재 파일:', file_path)

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.read().splitlines()  # 줄바꿈 기준으로 리스트 생성
    except UnicodeDecodeError:
        print('현재 파일은 UTF-8 인코딩이 아닙니다. EUC-KR로 시도합니다.')
        try:
            with open(file_path, 'r', encoding='euc-kr') as file:
                lines = file.read().splitlines()
        except UnicodeDecodeError:
            print('현재 파일은 EUC-KR 인코딩이 아닙니다. 파일을 읽을 수 없습니다.')
            return []

    return lines

# 추가
# 방위각 거리로 점 좌표반환
def calculate_destination_coordinates(x1, y1, bearing, distance):
    # Calculate the destination coordinates given a starting point, bearing, and distance in Cartesian coordinates
    angle = math.radians(bearing)
    x2 = x1 + distance * math.cos(angle)
    y2 = y1 + distance * math.sin(angle)
    return x2, y2


# offset 좌표 반환
def calculate_offset_point(vector, point_a, offset_distance):
    if offset_distance > 0:  # 우측 오프셋
        vector -= 90
    else:
        vector += 90  # 좌측 오프셋
    offset_a_xy = calculate_destination_coordinates(point_a[0], point_a[1], vector, abs(offset_distance))
    return offset_a_xy


@lru_cache(maxsize=None)
def calculate_bearing(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    return math.degrees(math.atan2(dy, dx))

# 실행
def load_structure_data():
    """구조물 데이터를 엑셀 파일에서 불러오는 함수"""
    openexcelfile = open_excel_file()
    if openexcelfile:
        return find_structure_section(openexcelfile)
    else:
        print("엑셀 파일을 선택하지 않았습니다.")
        return None


def load_curve_data():
    """곡선 데이터를 텍스트 파일에서 불러오는 함수"""
    txt_filepath = 'c:/temp/curve_info.txt'
    if txt_filepath:
        return find_curve_section(txt_filepath)
    else:
        print("지정한 파일을 찾을 수 없습니다.")
        return None


def load_pitch_data():
    """곡선 데이터를 텍스트 파일에서 불러오는 함수"""
    txt_filepath = 'c:/temp/pitch_info.txt'
    if txt_filepath:
        return find_pitch_section(txt_filepath)
    else:
        print("지정한 파일을 찾을 수 없습니다.")
        return None


def load_coordinates():
    """BVE 좌표 데이터를 텍스트 파일에서 불러오는 함수"""
    coord_filepath = 'c:/temp/bve_coordinates.txt'
    return read_polyline(coord_filepath)

def createtxt(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        for line in data:
            f.write(f'{line}\n')


def get_designspeed():
    """사용자로부터 설계 속도를 입력받아 반환"""
    while True:
        try:
            DESIGNSPEED = int(input('프로젝트의 설계속도 입력 (150, 250, 350): '))
            if DESIGNSPEED not in (150, 250, 350):
                print('올바른 DESIGNSPEED 값을 입력하세요 (150, 250, 350)')
            else:
                return DESIGNSPEED
        except ValueError:
            print("숫자를 입력하세요.")

def get_iscustommode():
    """사용자로부터 설계 속도를 입력받아 반환"""
    while True:
        try:
            iscustommode = input('커스텀 모드?: ')
            if iscustommode not in ('y' , 'n'):
                print('올바르지 않은 값: y/ n 입력')
            else:
                return True if iscustommode == 'y' else False
        except ValueError:
            print("문자를 입력하세요.")

def get_iscreatedxf():
    """사용자로부터 설계 속도를 입력받아 반환"""
    while True:
        try:
            iscustommode = input('도면 작성?: ')
            if iscustommode not in ('y' , 'n'):
                print('올바르지 않은 값: y/ n 입력')
            else:
                return True if iscustommode == 'y' else False
        except ValueError:
            print("문자를 입력하세요.")

def load_dataset(designspeed, iscustommode):
    if iscustommode:
        filename = r'c:/temp/custom_data.json'
    else:
        if designspeed == 150:
            filename = r'c:/temp/railway_150.json'
        elif designspeed == 250:
            filename = r'c:/temp/railway_250.json'
        elif designspeed == 350:
            filename = r'c:/temp/railway_350.json'
        else:
            raise ValueError(f'지원하지 않는 속도 모드입니다. {designspeed}')
    with open(filename, "r", encoding="utf-8") as f:
        base_data = json.load(f)
    return base_data

class AutoPole:
    def __init__(self, log_widget):
        self.airjoint_list = None
        self.pitchlist = None
        self.curvelist = None
        self.structure_list = None
        self.polyline_with_sta = None
        self.pole_processor = None
        self.wire_processor = None
        self.polesaver = None
        self.wire_path = None
        self.pole_path = None
        self.dataprocessor = None
        self.designspeed = 0
        self.iscustommode = False
        self.is_create_dxf = False
        self.log_widget = log_widget
        self.poledata = None
        self.wire_data = None

    def log(self, msg):
        if self.log_widget:
            self.log_widget.insert("end", msg + "\n")
            self.log_widget.see("end")
        else:
            print(msg)

    def run(self):
        """전체 작업을 관리하는 메인 함수"""

        # 파일 읽기 및 데이터 처리
        data = read_file()
        last_block = find_last_block(data)
        start_km = 0
        end_km = last_block // 1000


        # 구조물 정보 로드
        self.structure_list = load_structure_data()
        if self.structure_list:
            print("구조물 정보가 성공적으로 로드되었습니다.")

        # 곡선 정보 로드
        self.curvelist = load_curve_data()
        if self.curvelist:
            print("곡선 정보가 성공적으로 로드되었습니다.")
        # 기울기 정보 로드
        self.pitchlist = load_pitch_data()
        if self.pitchlist:
            print("기울기선 정보가 성공적으로 로드되었습니다.")
        # BVE 좌표 로드
        polyline = load_coordinates()
        self.polyline_with_sta = [(i * 25, *values) for i, values in enumerate(polyline)]

        #데이터셋 로드,
        dataset = load_dataset(self.designspeed, self.iscustommode)
        spans, pole_positions = distribute_pole_spacing_flexible(start_km, end_km, spans=dataset['span_list'])
        self.airjoint_list = define_airjoint_section(pole_positions ,airjoint_span=1600)

        # 전주번호 추가
        post_number_lst = generate_postnumbers(pole_positions)
        # 데이터 처리
        self.dataprocessor = DatasetGetter(dataset)

        self.pole_processor = PoleProcessor()
        self.poledata = self.pole_processor.process_pole(pole_positions, self.structure_list, self.curvelist, self.pitchlist, dataset, self.airjoint_list, self.polyline_with_sta)
        self.wire_processor = WireProcessor(self.dataprocessor, self.polyline_with_sta, self.poledata)
        self.wire_data = self.wire_processor.process_to_wire()
        self.pole_path = asksaveasfilename(title='전주 데이터 저장')
        self.wire_path = asksaveasfilename(title='전차선 데이터 저장')
        self.polesaver = BVECSV(self.poledata, self.wire_data)
        pole_text = self.polesaver.create_pole_csv()
        wire_text = self.polesaver.create_wire_csv()
        write_to_file(self.pole_path, pole_text)
        write_to_file(self.wire_path, wire_text)

        self.log("전주와 전차선 txt가 성공적으로 저장되었습니다.")
        if self.is_create_dxf:
            print("도면 작성중.")

        # 최종 출력
        self.log(f"전주 개수: {len(pole_positions)}")
        self.log(f"마지막 전주 위치: {pole_positions[-1]}m (종점: {int(end_km * 1000)}m)")
        self.log('모든 작업 완료')

class AutoPoleApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AutoPOLE")
        self.events = EventController()

        # 로그 박스
        self.log_box = tk.Text(self, height=10, width=80)
        self.log_box.pack(side="bottom", fill="x")
        self.runner = AutoPole(self.log_box)

        # 입력 영역
        input_frame = tk.Frame(self)
        input_frame.pack(side="top", fill="x")
        tk.Label(input_frame, text="설계속도").pack(side="left")
        self.entry_speed_var = tk.IntVar(value=150)
        self.entry_speed = tk.Entry(input_frame, width=10, textvariable=self.entry_speed_var)
        self.entry_speed.pack(side="left")

        self.is_custom_mode = tk.BooleanVar(value=False)
        tk.Checkbutton(input_frame, text="커스텀 모드", variable=self.is_custom_mode).pack(side="left")
        self.is_create_dxf = tk.BooleanVar(value=False)
        tk.Checkbutton(input_frame, text="도면 작성", variable=self.is_create_dxf).pack(side="left")

        # 버튼 영역
        button_frame = tk.Frame(self)
        button_frame.pack(side="top", fill="x")
        tk.Button(button_frame, text="실행", command=self.run_and_open_editor).pack(side="left")
        tk.Button(button_frame, text="로그 클리어", command=self.clear_log).pack(side="left")
        tk.Button(button_frame, text="저장", command=self.save).pack(side="left")
        tk.Button(button_frame, text="종료", command=self.exit_app).pack(side="left")

        # 메인 영역 (좌우 분할)
        main_frame = tk.PanedWindow(self, orient="horizontal")
        main_frame.pack(fill="both", expand=True)

        # 좌측: Editor
        editor_frame = tk.Frame(main_frame)
        self.editor = AutoPoleEditor(self.runner, self.events, master=editor_frame)
        self.editor.pack(fill="both", expand=True)   # 추가

        main_frame.add(editor_frame)

        # 우측: Plotter
        plotter_frame = tk.Frame(main_frame)
        self.plotter = PlotPoleMap(self.runner, self.events, master=plotter_frame)
        self.plotter.pack(fill="both", expand=True)  # 추가

        main_frame.add(plotter_frame)

    def exit_app(self):
        self.quit()
        self.destroy()

    def clear_log(self):
        self.log_box.delete("1.0", tk.END)

    def update_inputs(self):
        try:
            self.runner.designspeed = int(self.entry_speed.get())
            self.runner.iscustommode = int(self.is_custom_mode.get())
            self.runner.is_create_dxf = int(self.is_create_dxf.get())
            if self.runner.iscustommode:
                self.runner.log(f"현재 모드: 커스텀모드")
                return
            self.runner.log(f"현재 모드: 일반모드")
            self.runner.log(f"설계속도={self.runner.designspeed}km/h")

        except ValueError:
            self.runner.log("⚠️ 숫자를 입력하세요")

    def run_and_open_editor(self):
        # 입력값 반영 후 실행
        self.update_inputs()
        self.runner.run()
        self.editor.create_epoles()
        self.editor.refresh_tree()
        self.plotter.update_plot()


    def save(self):
        t = self.runner.polesaver.create_pole_csv()
        t2 = self.runner.polesaver.create_wire_csv()
        write_to_file(self.runner.pole_path, t)
        write_to_file(self.runner.wire_path, t2)
        self.runner.log(f"저장 성공!")

# event_controller.py
class EventController:
    def __init__(self):
        self._listeners = {}

    def bind(self, event_name, callback):
        self._listeners.setdefault(event_name, []).append(callback)

    def emit(self, event_name, *args, **kwargs):
        for cb in self._listeners.get(event_name, []):
            cb(*args, **kwargs)

class AutoPoleEditor(tk.Frame):
    def __init__(self, runner, events=None, master=None):
        super().__init__(master)
        self.runner = runner
        self.events = events
        if self.events:
            # pole_moved 이벤트가 발생하면 on_pole_moved 실행
            self.events.bind('pole_moved', self.on_pole_moved)


        self.editable_poles = []

        # Treeview + Scrollbar 프레임
        frame = tk.Frame(self)
        frame.pack(fill="both", expand=True)

        # Treeview 생성
        self.tree = ttk.Treeview(
            frame,
            columns=("전주번호", "측점", '경간', "건식게이지", "구조물", "구간", "기본 타입", '곡선반경','구배','캔트','계획고'),
            show="headings"
        )
        for col in ("전주번호", "측점", '경간', "건식게이지", "구조물", "구간", "기본 타입", '곡선반경','구배','캔트','계획고'):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")  # 기본 폭 지정

        # 가로 스크롤바 추가
        xscroll = tk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=xscroll.set)

        # 배치
        self.tree.pack(side="top", fill="both", expand=True)
        xscroll.pack(side="bottom", fill="x")

        # Entry widgets + Label
        frame_post_number = tk.Frame(self)
        tk.Label(frame_post_number, text="전주번호").pack(side="left")
        self.entry_post_number = tk.Entry(frame_post_number)
        self.entry_post_number.pack(side="left")
        frame_post_number.pack()

        frame_pos = tk.Frame(self)
        tk.Label(frame_pos, text="측점").pack(side="left")
        self.entry_pos = tk.Entry(frame_pos)
        self.entry_pos.pack(side="left")
        frame_pos.pack()

        frame_gauge = tk.Frame(self)
        tk.Label(frame_gauge, text="건식게이지").pack(side="left")
        self.entry_gauge = tk.Entry(frame_gauge)
        self.entry_gauge.pack(side="left")
        frame_gauge.pack()

        frame_structure = tk.Frame(self)
        tk.Label(frame_structure, text="구조물").pack(side="left")
        self.entry_structure = tk.Entry(frame_structure)
        self.entry_structure.pack(side="left")
        frame_structure.pack()

        frame_section = tk.Frame(self)
        tk.Label(frame_section, text="구간").pack(side="left")
        self.entry_section = tk.Entry(frame_section)
        self.entry_section.pack(side="left")
        frame_section.pack()

        frame_base_type = tk.Frame(self)
        tk.Label(frame_base_type, text="기본 타입").pack(side="left")
        self.entry_base_type = tk.Entry(frame_base_type)
        self.entry_base_type.pack(side="left")
        frame_base_type.pack()

        for e in (self.entry_post_number, self.entry_pos, self.entry_gauge,
                  self.entry_structure, self.entry_section, self.entry_base_type):
            e.pack()

        # 버튼
        tk.Button(self, text="선택 불러오기", command=self.load_selected).pack()
        tk.Button(self, text="수정 저장", command=self.save_edit).pack()

    def on_pole_moved(self):
        self.refresh_tree()

    def refresh_tree(self):
        if not self.runner.poledata:
            return
        for row in self.tree.get_children():
            self.tree.delete(row)
        for pole in self.runner.poledata:
            self.tree.insert("", "end", values=(pole.post_number, pole.pos, pole.span, pole.gauge, pole.structure, pole.section, pole.base_type , pole.radius,pole.pitch ,pole.cant, pole.z))

    def load_selected(self):
        selected = self.tree.selection()
        if selected:

            item = self.tree.item(selected[0])
            post_number, pos, span, gauge, structure, section, base_type, radius, pitch, cant ,z = item["values"]
            # epole 객체 찾기
            epole = None
            for e in self.editable_poles:
                if e.pole.pos == pos:
                    epole = e
                    break

            if self.events and epole:
                self.events.emit("pole_selected", epole)

            self.original_pos = pos
            self.entry_post_number.delete(0, tk.END)
            self.entry_post_number.insert(0, post_number)
            self.entry_pos.delete(0, tk.END)
            self.entry_pos.insert(0, pos)
            self.entry_gauge.delete(0, tk.END)
            self.entry_gauge.insert(0, gauge)
            self.entry_structure.delete(0, tk.END)
            self.entry_structure.insert(0, structure)
            self.entry_section.delete(0, tk.END)
            self.entry_section.insert(0, section)
            self.entry_base_type.delete(0, tk.END)
            self.entry_base_type.insert(0, base_type)



    def create_epoles(self):
        # EditablePole 리스트 생성

        for i, pole in enumerate(self.runner.poledata):
            prev_epole = self.editable_poles[i - 1] if i > 0 else None
            epole = EditablePole(pole, self.runner.structure_list,self.runner.curvelist,self.runner.pitchlist, self.runner.polyline_with_sta, prev_pole=prev_epole)
            self.editable_poles.append(epole)
            if prev_epole:
                prev_epole.next_pole = epole

    def save_edit(self):
        new_post_number = self.entry_post_number.get()
        new_pos = int(self.entry_pos.get())
        new_gauge = float(self.entry_gauge.get())
        new_section = self.entry_section.get() if not self.entry_section.get() == 'None' else None
        new_base_type = self.entry_base_type.get()
        for epole in self.editable_poles:
            if epole.pole.pos == self.original_pos:
                try:
                    # 일반개소만 편집 허용
                    if epole.pole.section is not None:
                        messagebox.showerror('전주 업데이트 실패', f'지정한 {epole.pole.pos}는 일반 개소가 아닙니다.')
                        return
                    # 새 span 계산
                    new_span = epole.pole.next_pos - new_pos
                    if new_span not in self.runner.dataprocessor.get_span_list():
                        messagebox.showerror('전주 업데이트 실패', f'경간 {new_span}은 지정된 spanlist에 없습니다.')
                        return

                    with Transaction(epole.pole, epole.prev_pole.pole, epole.next_pole.pole):
                            epole.update(
                                post_number=new_post_number,
                                pos=new_pos,
                                gauge=new_gauge,
                                section=new_section,
                                base_type=new_base_type
                            )
                            BracketEditor.update(epole.pole, self.runner.dataprocessor)
                    break
                except Exception as e:
                    messagebox.showerror('전주 업데이트 실패', str(e))
                    return
            # radius, cant, pitch, z, span, next_pos 등은 자동 재계산 예정
        self.refresh_tree()
        # 와이어 전체 재계산
        self.runner.wire_data = self.runner.wire_processor.process_to_wire()

        if self.events:
            self.events.emit("pole_saved")

        self.runner.log(f'전주 편집 성공 {new_pos}')

    def open_equipment_editor(self):
        top = tk.Toplevel(self)
        top.title("장비 편집")
        tk.Label(top, text="mast, brackets, equipments 편집 예정").pack()

class EditablePole:
    def __init__(self, pole, structure_list, curve_list ,pitch_list, polyline_with_sta, prev_pole=None, next_pole=None):
        self.pole = pole
        self.structure_list = structure_list
        self.curve_list = curve_list
        self.pitch_list = pitch_list
        self.polyline_with_sta = polyline_with_sta
        self.prev_pole = prev_pole
        self.next_pole = next_pole

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.pole, key):
                setattr(self.pole, key, value)

        try:
            # 현재 전주 재계산
            self.recalculate()

            # 인접 전주 pos/next_pos 동기화
            if self.prev_pole:
                self.prev_pole.pole.next_pos = self.pole.pos
                self.prev_pole.pole.next_base_type = self.pole.base_type
                self.prev_pole.recalculate()
            if self.next_pole:
                self.next_pole.pole.pos = self.pole.next_pos
                self.next_pole.recalculate()
        except Exception as e:
            raise Exception(e)

    def recalculate(self):
        # span 갱신
        self.pole.span = self.pole.next_pos - self.pole.pos
        #좌표갱신
        coord, _, v1 = interpolate_cached(self.polyline_with_sta, self.pole.pos)
        pos_coord_with_offset = calculate_offset_point(v1, coord, self.pole.gauge)
        self.pole.coord = pos_coord_with_offset

        # z, next_z 갱신
        self.pole.z = get_elevation_pos(self.pole.pos, self.polyline_with_sta)
        self.pole.next_z = get_elevation_pos(self.pole.next_pos, self.polyline_with_sta)

        # 구조물, 곡선, 구배 등 갱신
        self.pole.structure = isbridge_tunnel(self.pole.pos, self.structure_list)
        curve, R, c = iscurve(self.pole.pos, self.curve_list)
        self.pole.radius, self.pole.cant = R, c
        slope, pitch = isslope(self.pole.pos, self.pitch_list)
        self.pole.pitch = pitch

class BracketEditor:
    @staticmethod
    def update(pole ,dataprocseeor):
        """일반구간용"""
        current_type = pole.base_type
        current_curve = '직선' if pole.radius == 0 else '곡선'
        i, o  = dataprocseeor.get_bracket_type(pole.structure, current_curve)
        if current_type == 'I':
            index = i
        else:
            index = o
        bracket_name = current_type
        pole.brackets[0] = BracketDATA(bracket_type=current_type, index=index, bracket_name=bracket_name)

class Transaction:
    def __init__(self, *objs):
        """
        objs: 트랜잭션을 적용할 여러 객체 (PoleDATA, EditablePole 등)
        """
        self._originals = objs
        self._backups = []
        self._active = False

    def __enter__(self):
        if self._active:
            raise RuntimeError("Transaction already started")
        # 모든 객체 백업
        self._backups = [copy.deepcopy(obj) for obj in self._originals]
        self._active = True
        print("Transaction started.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.abort()

    def commit(self):
        if not self._active:
            raise RuntimeError("No active transaction")
        self._backups = []
        self._active = False
        print("Transaction committed.")

    def abort(self):
        if not self._active:
            raise RuntimeError("No active transaction")
        # 모든 객체를 백업 상태로 복원
        for original, backup in zip(self._originals, self._backups):
            if isinstance(original, dict):
                original.clear()
                original.update(backup)
            elif isinstance(original, list):
                original.clear()
                original.extend(backup)
            else:
                for attr in vars(backup):
                    setattr(original, attr, getattr(backup, attr))
        self._backups = []
        self._active = False
        print("Transaction aborted.")

class PlotPoleMap(tk.Frame):
    def __init__(self, runner, events=None, master=None):
        super().__init__(master)
        self.selected_epole = None
        self.selected_pole_scatter = None
        self.sel_xy = None
        self.selected_pole = None
        self.runner = runner
        self.events = events
        if self.events:
            self.events.bind("pole_selected", self.on_pole_selected)

        # Matplotlib Figure/Axes 생성
        plt.rcParams['font.family'] = 'Malgun Gothic'
        plt.rcParams['axes.unicode_minus'] = False

        self.fig, self.ax = plt.subplots(figsize=(8,8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # 툴바 추가
        toolbar = NavigationToolbar2Tk(self.canvas, self)
        toolbar.update()
        toolbar.pack(side="bottom", fill="x")

        # 이동 버튼 등록
        btn_left = tk.Button(self, text="-5m", command=self.move_left)
        btn_right = tk.Button(self, text="+5m", command=self.move_right)
        btn_left.pack(side="left")
        btn_right.pack(side="right")

    def draw_alignment(self):
        # polyline 좌표 꺼내기
        sta_list, x_list, y_list, z_list = zip(*self.runner.polyline_with_sta)
        # 선형 그리기 (예: x vs z)
        self.ax.plot(x_list, y_list, color="gray", label="선형")

    def draw_poles(self):
        # 전주 위치(pos)를 x축에 표시
        poles = self.runner.poledata
        x_val = [pole.coord[0] for pole in poles]
        y_val = [pole.coord[1] for pole in poles]
        self.ax.scatter(x_val, y_val, c="blue", marker="o", label="전주")

    def update_plot(self):
        self.ax.clear()
        self.ax.set_title("전주 위치 맵")
        self.ax.set_xlabel("X좌표")
        self.ax.set_ylabel("Y좌표")

        self.draw_alignment()
        self.draw_poles()
        self.canvas.draw()

    def highlight_pole(self, pos):
        self.ax.set_title("선택된 전주")
        self.ax.clear()
        self.draw_alignment()
        self.draw_poles()
        poles = self.runner.poledata
        # 선택된 전주 강조
        for pole in poles:
            if pole.pos == pos:
                self.selected_pole = pole
                self.sel_xy = pole.coord[0], pole.coord[1]

                self.selected_pole_scatter = self.ax.scatter(self.sel_xy[0], self.sel_xy[1], c="red", s=100, label="선택된 전주", picker=5)
                self.ax.text(self.sel_xy[0], self.sel_xy[1], f'{pole.post_number}')
                self.ax.set_xlim(self.sel_xy[0] - 50, self.sel_xy[0] + 50)
                self.ax.set_ylim(self.sel_xy[1] - 50, self.sel_xy[1] + 50)
                break

        self.ax.legend()
        self.canvas.draw()

    def on_pole_selected(self, epole):
        self.selected_epole = epole
        self.highlight_pole(epole.pole.pos)

    def move_left(self):
        self._move_pole(-5)

    def move_right(self):
        self._move_pole(+5)

    def _move_pole(self, delta):
        if not self.selected_epole: return

        new_pos = self.selected_epole.pole.pos + delta
        prev_pos = self.selected_epole.prev_pole.pole.pos if self.selected_epole.prev_pole else None
        next_pos = self.selected_epole.next_pole.pole.pos if self.selected_epole.next_pole else None

        # 범위 검사
        if prev_pos and new_pos <= prev_pos: return
        if next_pos and new_pos >= next_pos: return
        #타입ㄱ머사
        if self.selected_epole.pole.section is not None:
            messagebox.showerror('오류', f'{self.selected_epole.pole.post_number}: 지정한 전주는 일반개소가 아닙니다. 일반개소만 이동이 가능합니다.')
            return
        #span 검사
        new_prev_pole_span = new_pos - prev_pos #이전전주와의 span
        new_span = next_pos - new_pos #다음 전주와의 스판

        if new_prev_pole_span not in self.runner.dataprocessor.get_span_list() or new_span not in self.runner.dataprocessor.get_span_list():
            messagebox.showerror('오류', f'{self.selected_epole.pole.post_number}: 지정한 전주는 span 범위에 없습니다.')
            return

        # 보간 좌표 계산
        coord, _, v1 = interpolate_cached(self.runner.polyline_with_sta, new_pos)
        pos_coord_with_offset = calculate_offset_point(v1, coord, self.selected_epole.pole.gauge)

        # 최종 반영
        with Transaction(self.selected_epole.pole,
                         self.selected_epole.prev_pole.pole if self.selected_epole.prev_pole else None,
                         self.selected_epole.next_pole.pole if self.selected_epole.next_pole else None):
            self.selected_epole.update(pos=new_pos)

        self.selected_epole.pole.coord = pos_coord_with_offset
        self.runner.wire_data = self.runner.wire_processor.process_to_wire()
        self.runner.log(f"전주 {self.selected_epole.pole.post_number} 이동 완료: {new_pos}")

        self.highlight_pole(new_pos)
        self.events.emit('pole_moved') #전주 이동 이벤트 발생
# 실행
if __name__ == "__main__":
    app = AutoPoleApp()
    app.mainloop()
