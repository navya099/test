import random
import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import math
import re
import numpy as np
from enum import Enum
from shapely.geometry import Point, LineString


'''
ver 2025.03.13 1428
무효전선 각도 2차수정
#modify

'''

class AirJoint(Enum):
    START = "에어조인트 시작점 (1호주)"
    POINT_2 = "에어조인트 (2호주)"
    MIDDLE = "에어조인트 중간주 (3호주)"
    POINT_4 = "에어조인트 (4호주)"
    END = "에어조인트 끝점 (5호주)"
    
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

#전주번호 추가함수
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
    #print(df_tunnel.shape)  # (행 개수, 열 개수)
    #print(df_tunnel.head())  # 데이터 확인

     # 첫 번째 행을 열 제목으로 설정
    df_bridge.columns = ['br_NAME', 'br_START_STA', 'br_END_STA', 'br_LENGTH']
    df_tunnel.columns = ['tn_NAME', 'tn_START_STA', 'tn_END_STA', 'tn_LENGTH']
    
    # 교량 구간과 터널 구간 정보
    for _, row in df_bridge.iterrows():
        structure_list['bridge'].append((row['br_START_STA'], row['br_END_STA']))
    
    for _, row in df_tunnel.iterrows():
        structure_list['tunnel'].append((row['tn_START_STA'], row['tn_END_STA']))
    
    return structure_list

def find_curve_section(txt_filepath='curveinfo.txt'):
    """txt 파일을 읽고 곧바로 측점(sta)과 곡선반경(radius) 정보를 반환하는 함수"""
    
    curve_list = []

    # 텍스트 파일(.txt) 읽기
    df_curve = pd.read_csv(txt_filepath, sep=",", header=None, names=['sta', 'radius','cant'])

    # 곡선 구간 정보 저장
    for _, row in df_curve.iterrows():
        curve_list.append((row['sta'], row['radius'], row['cant']))
    
    return curve_list


def isbridge_tunnel(sta, structure_list):
    """sta가 교량/터널/토공 구간에 해당하는지 구분하는 함수"""
    for start, end in structure_list['bridge']:
        if start <= sta <= end:
            return '교량'
    
    for start, end in structure_list['tunnel']:
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

    return '직선', 0 , 0 # 목록에 없으면 기본적으로 직선 처리

def get_pole_data():
    """전주 데이터를 반환하는 기본 딕셔너리"""
    return {
        150: {
            'prefix': 'Cako150',
            'tunnel': (947, 946),
            'earthwork': (544, 545),
            'straight_bridge': (556, 557),
            'curve_bridge': (562, 563),
        },
        250: {
            'prefix': 'Cako250',
            'tunnel': (979, 977),#터널은 I,O반대
            'earthwork': (508, 510),
            'straight_bridge': (512, 514),
            'curve_bridge': (527, 529),
        },
        350: {
            'prefix': 'Cako350',
            'tunnel': (569, 568),
            'earthwork': (564, 565),
            'straight_bridge': (566, 567),
            'curve_bridge': (566, 567),
        }
    }

def format_pole_data(design_speed):
    """설계 속도에 따른 전주 데이터를 특정 형식으로 변환"""
    base_data = get_pole_data()

    if design_speed not in base_data:
        raise ValueError("올바른 DESIGNSPEED 값을 입력하세요 (150, 250, 350)")

    data = base_data[design_speed]
    prefix = data['prefix']

    def create_pole_types(i_type, o_type, bracket_suffix):
        return {
            'I_type': i_type,
            'O_type': o_type,
            'I_bracket': f'{prefix}_{bracket_suffix}-I',
            'O_bracket': f'{prefix}_{bracket_suffix}-O',
        }

    return {
        '교량': {
            '직선': create_pole_types(*data['straight_bridge'], 'OpG3.5'),
            '곡선': create_pole_types(*data['curve_bridge'], 'OpG3.5'),
        },
        '터널': create_pole_types(*data['tunnel'], 'Tn'),
        '토공': create_pole_types(*data['earthwork'], 'OpG3.0'),
    }

def define_airjoint_section(positions):
    airjoint_list = []  # 결과 리스트
    airjoint_span = 1600  # 에어조인트 설치 간격(m)

    def is_near_multiple_of_DIG(number, tolerance=100):
        """주어진 수가 1200의 배수에 근사하는지 판별하는 함수"""
        remainder = number % airjoint_span
        return number > airjoint_span and (remainder <= tolerance or remainder >= (airjoint_span - tolerance))

    i = 0  # 인덱스 변수
    while i < len(positions) - 1:  # 마지막 전주는 제외
        pos = positions[i]  # 현재 전주 위치

        if is_near_multiple_of_DIG(pos):  # 조건 충족 시
            next_values = positions[i+1:min(i+6, len(positions))]  # 다음 5개 값 가져오기
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
        if  input_sta == sta:
            return tag
            
def write_to_file(filename, lines):
    """리스트 데이터를 파일에 저장하는 함수"""
    filename  = f'c:/temp/' + filename
    try:
        # 디렉토리 자동 생성
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(lines)  # 리스트 데이터를 한 번에 파일에 작성

        print(f"✅ 파일 저장 완료: {filename}")
    except Exception as e:
        print(f"⚠️ 파일 저장 중 오류 발생: {e}")

def get_airjoint_bracket_data():
    """에어조인트 브래킷 데이터를 반환하는 기본 딕셔너리"""
    return {
        150: {
            'prefix': 'Cako150',#150급은 별도의 aj없음
            '터널': (941, 942),#G2.1 I,0
            '토공': (1252, 1253),#G3.0 I,O
            '교량': (1254, 1255),#G3.5 I,O
        },
        250: {
            'prefix': 'Cako250',
            '터널': (1325, 1326),#CAKO250-Tn-AJ
            '토공': (1296, 1297),#CAKO250-G3.0-AJ
            '교량': (1298, 1299),#CAKO250-G3.5-AJ
        },
        350: {
            'prefix': 'Cako350',
            '터널': (574, 575),#CAKO350-Tn-AJ
            '토공': (570, 571),#CAKO350-G3.0-AJ
            '교량': (572, 573),#CAKO350-G3.5-AJ
        }
    }

def get_F_bracket_data():
    """F브래킷 데이터를 반환하는 기본 딕셔너리"""
    return {
        150: {
            'prefix': 'Cako150',
            '터널': (1330, 1330),#TN-F
            '토공': (1253, 1253),#G3.0F
            '교량': (1255, 1255),#G3.5-F
        },
        250: {
            'prefix': 'Cako250',
            '터널': (1290, 1291),
            '토공': (1284, 1285),#CAKO250-G3.0-F(S) CAKO250-G3.0-F(L)
            '교량': (1286, 1287),#CAKO250-G3.5-F
        },
        350: {
            'prefix': 'Cako350',
            '터널': (582, 583),#CAKO350-Tn-F
            '토공': (578, 579),#CAKO350-G3.0-F(S) CAKO250-G3.0-F(L)
            '교량': (580, 581),#CAKO350-G3.5-F
        }
    }

def get_airjoint_fitting_data():
    """에어조인트 브래킷 금구류 데이터를 반환하는 기본 딕셔너리"""
    return {
        150: {
            'prefix': 'Cako150',
            '에어조인트': 499,#에어조인트용 조가선 지지금구
            'FLAT': (1292,1292), #무효인상용 조가선,전차선 지지금구(150-급에서는 f형 돼지꼬리)
            '곡선당김금구': (1293, 1294),#L,R
        },
        250: {
            'prefix': 'Cako250',#
            '에어조인트': 1279,#에어조인트용 조가선 지지금구
            'FLAT': (1281,1282), #무효인상용 조가선, 전차선  지지금구
            '곡선당김금구': (1280, 1283)#L,R
        },
        350: {
            'prefix': 'Cako350',#350
            '에어조인트': 586,#에어조인트용 조가선 지지금구
            'FLAT': (584, 585),#무효인상용 조가선, 전차선  지지금구
            '곡선당김금구': (576, 577),#L,R
        }
    }
        
def get_airjoint_lines(pos, current_airjoint, pole_type, bracket_type, current_structure, DESIGNSPEED, currentspan):
    """에어조인트 구간별 전주 데이터 생성"""
    lines = []
    
    # 데이터 가져오기
    airjoint_fitting, flat_fitting, steady_arm_fitting, mast_type, mast_name, offset = get_fitting_and_mast_data(DESIGNSPEED, current_structure, bracket_type)
    bracket_values, f_values = get_bracket_codes(DESIGNSPEED, current_structure)

    # 구조물별 건식게이지 값
    gauge = get_pole_gauge(DESIGNSPEED, current_structure)

    #에어조인트 각도 가져오기
    stagger,y1= get_bracket_coordinates(DESIGNSPEED, 'F형_끝')

    S_angle, E_angle = get_airjoint_angle(gauge, stagger, currentspan)

    
    bracket_code_start, bracket_code_end = bracket_values
    f_code_start, f_code_end = f_values

    # 전주 추가
    add_pole(lines, pos, current_airjoint, pole_type, bracket_type)

    #급전선 설비 인덱스 가져오기
    feeder_idx = get_feeder_insulator_idx(current_structure)

    #평행틀 설비 인덱스 가져오기
    spreader_name, spreader_idx =  get_spreader_idx(DESIGNSPEED, current_structure, current_airjoint)

    #공통 텍스트(전주,급전선,평행틀
    if current_airjoint in [AirJoint.POINT_2.value, AirJoint.MIDDLE.value, AirJoint.POINT_4.value]:
        common_lines(lines,mast_type, offset, mast_name, feeder_idx, spreader_name, spreader_idx)

    # 모든 필요한 값들을 딕셔너리로 묶어서 전달
    params = {
        'current_airjoint': current_airjoint,
        'lines': lines,
        'pos': pos,
        'DESIGNSPEED': DESIGNSPEED,
        'airjoint_fitting': airjoint_fitting,
        'steady_arm_fitting': steady_arm_fitting,
        'flat_fitting': flat_fitting,
        'pole_type': pole_type,
        'bracket_type': bracket_type,
        'S_angle': S_angle,
        'offset': offset,
        'E_angle': E_angle,
        'f_code_start': f_code_start,
        'f_code_end': f_code_end,
        'bracket_code_start': bracket_code_start,
        'bracket_code_end': bracket_code_end
    }
    #에어조인트 구간별 처리(2호주 ,3호주, 4호주)
    add_airjoint_brackets(params)
    
    return lines


def add_airjoint_brackets(params):
    #인자 분해
    """에어조인트 각 구간별 브래킷 추가"""
    current_airjoint = params['current_airjoint']
    lines = params['lines']
    pos = params['pos']
    DESIGNSPEED = params['DESIGNSPEED']
    airjoint_fitting = params['airjoint_fitting']
    steady_arm_fitting = params['steady_arm_fitting']
    flat_fitting = params['flat_fitting']
    pole_type = params['pole_type']
    bracket_type = params['bracket_type']
    S_angle = params['S_angle']
    offset = params['offset']
    E_angle = params['E_angle']
    f_code_start = params['f_code_start']
    f_code_end = params['f_code_end']
    bracket_code_start = params['bracket_code_start']
    bracket_code_end = params['bracket_code_end']
    
    """에어조인트 각 구간별 브래킷 추가"""
    if current_airjoint == AirJoint.START.value:
        # START 구간 처리
        lines.extend([
            f".freeobj 0;{pole_type};,;{bracket_type}\n",
            f".freeobj 0;1247;{offset};0;{S_angle},;스프링식 장력조절장치\n"
        ])
    
    elif current_airjoint == AirJoint.POINT_2.value:
        # POINT_2 구간 처리
        add_F_and_AJ_brackets(DESIGNSPEED, lines, pos, f_code_start, bracket_code_start, airjoint_fitting, steady_arm_fitting, flat_fitting)

    elif current_airjoint == AirJoint.MIDDLE.value:
        # MIDDLE 구간 처리
        add_AJ_brackets_middle(DESIGNSPEED, lines, pos, bracket_code_start, bracket_code_end, airjoint_fitting, steady_arm_fitting)

    elif current_airjoint == AirJoint.POINT_4.value:
        # POINT_4 구간 처리
        add_F_and_AJ_brackets(DESIGNSPEED, lines, pos, f_code_end, bracket_code_end, airjoint_fitting, steady_arm_fitting, flat_fitting, end=True)

    elif current_airjoint == AirJoint.END.value:
        # END 구간 처리
        lines.append(f".freeobj 0;{pole_type};,;{bracket_type}\n")
        lines.append(f".freeobj 0;1247;{offset};0;{180 - E_angle};,;스프링식 장력조절장치\n")


def add_F_and_AJ_brackets(DESIGNSPEED, lines, pos, f_code, bracket_code, airjoint_fitting, steady_arm_fitting, flat_fitting, end=False):
    """F형 및 AJ형 브래킷을 추가하는 공통 함수"""
    # F형 가동 브래킷 추가
    x1, y1 = get_bracket_coordinates(DESIGNSPEED, 'F형_시점' if not end else 'F형_끝')
    add_F_bracket(lines, pos - 0.528, f_code, "가동브래킷 F형", flat_fitting, x1, y1)

    # AJ형 가동 브래킷 추가
    x1, y1 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_시점' if not end else 'AJ형_끝')
    add_AJ_bracket(lines, pos + 0.528, bracket_code, '가동브래킷 AJ형', airjoint_fitting, steady_arm_fitting[0] if not end else steady_arm_fitting[1], x1, y1)


def add_AJ_brackets_middle(DESIGNSPEED, lines, pos, bracket_code_start, bracket_code_end, airjoint_fitting, steady_arm_fitting):
    """MIDDLE 구간에서 AJ형 브래킷 추가"""
    # AJ형 가동 브래킷 및 금구류 추가
    x1, y1 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_중간1')
    bracket_code_else = bracket_code_start if DESIGNSPEED == 150 else bracket_code_end
    steady_arm_fitting_else = steady_arm_fitting[0] if DESIGNSPEED == 150 else steady_arm_fitting[1]
    add_AJ_bracket(lines, pos - 0.8, bracket_code_else, '가동브래킷 AJ형', airjoint_fitting, steady_arm_fitting_else, x1, y1)

    # AJ형 가동 브래킷 및 금구류 추가
    x1, y1 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_중간2')
    add_AJ_bracket(lines, pos + 0.8, bracket_code_end, '가동브래킷 AJ형', airjoint_fitting, steady_arm_fitting[1], x1, y1)


def get_fitting_and_mast_data(DESIGNSPEED, current_structure, bracket_type):
    """금구류 및 전주 데이터를 가져옴"""
    fitting_data = get_airjoint_fitting_data().get(DESIGNSPEED, {})
    airjoint_fitting = fitting_data.get('에어조인트', 0)
    flat_fitting = fitting_data.get('FLAT', (0, 0))
    steady_arm_fitting = fitting_data.get('곡선당김금구', (0, 0))
    
    mast_type, mast_name = get_mast_type(DESIGNSPEED, current_structure)

    offset = get_pole_gauge(DESIGNSPEED , current_structure)

    return airjoint_fitting, flat_fitting, steady_arm_fitting, mast_type, mast_name, offset

def get_mast_type(DESIGNSPEED, current_structure):
    #전주 인덱스 딕셔너리(idx,comment)
    mast_dic = {
        150: {
            'prefix': 'Cako150',
            '토공': (1370,'P-10"x7t-9m'),
            '교량': (1376,'P-12"x7t-8.5m'),
            '터널': (1400,'터널하수강'),
        },
        250: {
            'prefix': 'Cako250',
            '토공': (1370,'P-10"x7t-9m'),
            '교량': (1376,'P-12"x7t-8.5m'),
            '터널': (1400,'터널하수강'),
        },
        350: {
            'prefix': 'Cako350',#350
            '토공': (619,'H형주-208X202'),
            '교량': (620,'H형주-250X255'),
            '터널': (621,'터널하수강'),
        }
    }
    mast_data = mast_dic.get(DESIGNSPEED, mast_dic[250])
    mast_type , mast_name = mast_data.get(current_structure, ("", "알 수 없는 구조"))

    return mast_type , mast_name
    
def get_bracket_codes(DESIGNSPEED, current_structure):
    """브래킷 코드 가져오기"""
    airjoint_data = get_airjoint_bracket_data().get(DESIGNSPEED, {})
    f_data = get_F_bracket_data().get(DESIGNSPEED, {})

    bracket_values = airjoint_data.get(current_structure, (0, 0))
    f_values = f_data.get(current_structure, (0, 0))

    return bracket_values, f_values

def add_pole(lines, pos, current_airjoint, pole_type, bracket_type):
    """전주를 추가하는 함수"""
    lines.extend([
        f"\n,;-----{current_airjoint}-----\n",
        f"{pos}\n"
    ])


#에어조인트 편위와 인상높이 딕셔너리
def get_bracket_coordinates(DESIGNSPEED, bracket_type):
    """설계속도와 브래킷 유형에 따른 좌표 반환"""
    coordinates = {
        "F형_시점": {
            150: (-0.35, 0.2),
            250: (-0.3, 0.32),
            350: (-0.25, 0.2)
        },
        "AJ형_시점": {
            150: (-0.15, 0),
            250: (-0.1, 0),
            350: (-0.05, 0)
        },
        "AJ형_중간1": {
            150: (-0.15, 0),
            250: (-0.1, 0),
            350: (-0.05, 0)
        },
        "AJ형_중간2": {
            150: (0.15, 0),
            250: (0.1, 0),
            350: (0.05, 0)
        },
        "AJ형_끝": {
            150: (0.15, 0),
            250: (0.1, 0),
            350: (0.05, 0)
        },
        "F형_끝": {
            150: (0.35, 0.2),
            250: (0.3, 0.32),
            350: (0.25, 0.2)
        },
    }

    # 지정된 브래킷 유형과 속도에 맞는 좌표 반환
    return coordinates.get(bracket_type, {}).get(DESIGNSPEED, (0, 0))


def common_lines(lines,mast_type, offset, mast_name, feeder_idx, spreader_name, spreader_idx):
    
    lines.extend([
                ',;전주 구문\n',
                f".freeobj 0;{mast_type};{offset};,;{mast_name}\n",
                f".freeobj 0;{feeder_idx};{offset};,;급전선 현수 조립체\n",
                f".freeobj 0;{spreader_idx};{offset};,;{spreader_name}\n\n"
    ])

def get_feeder_insulator_idx(current_structure):
    idx_dic = {'토공':1234, '교량':1234, '터널':1249}
    idx = idx_dic.get(current_structure, 1234)
    return idx

def get_spreader_idx(DESIGNSPEED, current_structure, current_airjoint):
    """평행틀 인덱스를 반환하는 기본 딕셔너리"""
    spreader_dictionary = {
        150: {
            'prefix': 'Cako150',
            '토공': (531, 532),
            '교량': (534, 535),
            '터널': (537, 538)
        },
        250: {
            'prefix': 'Cako250',
            '토공': (531, 532),
            '교량': (534, 535),
            '터널': (537, 538)
        },
        350: {
            'prefix': 'Cako350',
            '토공': (587, 588),
            '교량': (589, 590),
            '터널': (587, 588)
        }
    }

    spreader_data = spreader_dictionary.get(DESIGNSPEED, spreader_dictionary[250])
    spreader_str = spreader_data.get(current_structure, (0, 0))  # 기본값 (0, 0) 설정

    if current_airjoint in ['에어조인트 2호주' , '에어조인트 4호주']:
        spreader_idx = spreader_str[0]
        spreader_name = '평행틀-1m'
    elif current_airjoint in ['에어조인트 중간주 (3호주)']:
        spreader_idx = spreader_str[1]
        spreader_name = '평행틀-1.6m'
    else:
        spreader_idx = spreader_str[0]
        spreader_name = '평행틀-1m'

    return spreader_name, spreader_idx

def add_F_bracket(lines, pos, bracket_code, bracket_type, fitting_data,x1,y1):
    """F형 가동 브래킷 및 금구류 추가"""
    idx1, idx2 = fitting_data
    lines.extend([
        ',;가동브래킷구문\n',
        f"{pos},.freeobj 0;{bracket_code};0;0;,;{bracket_type}\n",
        f"{pos},.freeobj 0;{idx1};{x1};{y1},;조가선지지금구-F용\n",
        f"{pos},.freeobj 0;{idx2};{x1};{y1},;전차선선지지금구-F용\n",
    ])

def add_AJ_bracket(lines, pos, bracket_code, bracket_type, fitting_data, steady_arm_fitting, x1,y1):
    """AJ형 가동 브래킷 및 금구류 추가"""
    lines.extend([
        ',;가동브래킷구문\n',
        f"{pos},.freeobj 0;{bracket_code};0;0;,;{bracket_type}\n",
        f"{pos},.freeobj 0;{fitting_data};{x1};{y1},;조가선지지금구-AJ용\n",
        f"{pos},.freeobj 0;{steady_arm_fitting};{x1};{y1},;곡선당김금구\n",
    ])

def find_post_number(lst, pos):
    for arg in lst:
        if arg[0] == pos:
            return arg[1]
    
def save_to_txt(positions, structure_list, curve_list, DESIGNSPEED, airjoint_list, filename="C:/TEMP/pole_positions.txt"):
    """전주 위치 데이터를 가공하여 .txt 파일로 저장하는 함수"""
    
    # 전주 데이터 구성
    pole_data = format_pole_data(DESIGNSPEED)
    
    lines = []  # 파일에 저장할 데이터를 담을 리스트
    #전주번호
    post_number_lst = generate_postnumbers(positions)
    
    for i in range(len(positions) - 1):
        pos, next_pos = positions[i], positions[i + 1]
        currentspan = next_pos - pos  # 전주 간 거리 계산
        # 현재 위치의 구조물 및 곡선 정보 가져오기
        current_structure = isbridge_tunnel(pos, structure_list)
        current_curve, R, c = iscurve(pos, curve_list)
        current_airjoint = check_isairjoint(pos, airjoint_list)
        post_number = find_post_number(post_number_lst, pos)
        # 해당 구조물에 대한 전주 데이터 가져오기 (없으면 '토공' 기본값 사용)
        station_data = pole_data.get(current_structure, pole_data.get('토공', {}))

        # '교량' 같은 구간일 경우, 곡선 여부에 따라 데이터 선택
        if isinstance(station_data, dict) and '직선' in station_data:
            station_data = station_data.get('곡선' if current_curve == '곡선' else '직선', {})

        # 필요한 데이터 추출 (기본값 설정)
        I_type = station_data.get('I_type', '기본_I_type')
        O_type = station_data.get('O_type', '기본_O_type')
        I_bracket = station_data.get('I_bracket', '기본_I_bracket')
        O_bracket = station_data.get('O_bracket', '기본_O_bracket')

        # 홀수/짝수에 맞는 전주 데이터 생성
        pole_type = I_type if i % 2 == 1 else O_type
        bracket_type = I_bracket if i % 2 == 1 else O_bracket

        if current_airjoint:
            lines.extend(f'\n,;{post_number}')
            lines.extend(get_airjoint_lines(pos, current_airjoint, pole_type, bracket_type, current_structure, DESIGNSPEED, currentspan))
        else:
            lines.append(f'\n,;{post_number}')
            lines.append(f'\n,;-----일반개소({current_structure})({current_curve})-----\n')
            lines.append(f"{pos},.freeobj 0;{pole_type};,;{bracket_type}\n")

    # 파일 저장 함수 호출
    write_to_file(filename, lines)

#미사용
def get_stagger_at_cant(cant,height,stagger):
    '''곡선반경에 따른 캔트에 의한 편위를 반환하는 함수'''
    '''
        param:cant (캔트 float)
        param:height(전차선 높이:float)
        param:stagger(직선구간 전차선 편위 float)
        return stagger
        
    '''
    default = stagger#기본값
    gague = 1.5#표준궤간
    angle = gauge / height#cant각도

    if cant == 0:
        return default
    
    return stagger
    
    
def open_excel_file():
    """파일 선택 대화 상자를 열고, 엑셀 파일 경로를 반환하는 함수"""
    root = tk.Tk()
    root.withdraw()  # Tkinter 창을 숨김
    file_path = filedialog.askopenfilename(
        title="엑셀 파일 선택",
        filetypes=[("Excel Files", "*.xlsx")]
    )
    
    return file_path

def get_block_index(current_track_position, block_interval = 25):
    """현재 트랙 위치를 블록 인덱스로 변환"""
    return math.floor(current_track_position / block_interval + 0.001) * block_interval

def process_to_WIRE(positions, spans, structure_list, curve_list, polyline, airjoint_list, filename="wire.txt"):
    """ 전주 위치에 wire를 배치하는 함수 """
    post_number_lst = generate_postnumbers(positions)
    polyline_with_sta = [(i * 25, *values) for i, values in enumerate(polyline)]
    lines = []
    for i in range(len(positions) - 1):
        pos, next_pos = positions[i], positions[i + 1]
        currentspan = next_pos - pos  # 전주 간 거리 계산
        current_structure = isbridge_tunnel(pos, structure_list)
        next_structure = isbridge_tunnel(next_pos, structure_list)
        current_curve, R, c = iscurve(pos, curve_list)
        current_sta = get_block_index(pos)
        current_airjoint = check_isairjoint(pos, airjoint_list)
        currnet_type = 'I' if i % 2 == 1 else 'O'
        post_number = find_post_number(post_number_lst, pos)
        obj_index, comment, AF_wire, FPW_wire = get_wire_span_data(DESIGNSPEED,  currentspan, current_structure)
        
        #AF와 FPW오프셋(X,Y)
        AF_X_offset,AF_y_offset , fpw_wire_X_offset, fpw_wire_y_offset , AF_yz_angle, FPW_yz_angle ,AF_xy_angle , FPW_xy_angle,AF_X_offset_Next, fpw_wire_X_offset_Next = CALULATE_AF_FPW_OFFET_ANGLE(current_structure, next_structure, currentspan)

        #편위(0.2)와 직선구간 각도
        lateral_offset, adjusted_angle = get_lateral_offset_and_angle(i, currentspan)

        lines.extend([f'\n,;{post_number}'])
        if current_airjoint in ['에어조인트 시작점 (1호주)', '에어조인트 (2호주)' , '에어조인트 중간주 (3호주)', '에어조인트 (4호주)', '에어조인트 끝점 (5호주)']:
            lines.extend([f'\n,;-----{current_airjoint}({current_structure})-----\n'])
        else:
            
            lines.extend([f'\n,;-----일반개소({current_structure})({current_curve})-----\n'])

        lines.extend(handle_curve_and_straight_section(pos, next_pos, currentspan, polyline_with_sta, current_airjoint, obj_index, comment, currnet_type, current_structure,  next_structure))
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, AF_X_offset, AF_X_offset_Next)
        lines.append(f"{pos},.freeobj 0;{AF_wire};{AF_X_offset};{AF_y_offset};{adjusted_angle};{AF_yz_angle};,;급전선\n")
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, fpw_wire_X_offset, fpw_wire_X_offset_Next)
        lines.append(f"{pos},.freeobj 0;{FPW_wire};{fpw_wire_X_offset};{fpw_wire_y_offset};{adjusted_angle};{FPW_yz_angle};,;FPW\n")
    
            
    buffered_write(filename, lines)

def CALULATE_AF_FPW_OFFET_ANGLE(current_structure, next_structure, currentspan):
    
    #현재
    AF_X_offset,AF_y_offset , fpw_wire_X_offset, fpw_wire_y_offset = get_wire_offsetanlge(DESIGNSPEED ,current_structure)
    #다음
    AF_X_offset_Next,AF_y_offset_Next , fpw_wire_X_offset_Next, fpw_wire_y_offset_Next = get_wire_offsetanlge(DESIGNSPEED, next_structure)

    # YZ 평면 각도 계산
    AF_yz_angle = math.degrees(math.atan((AF_y_offset_Next - AF_y_offset) / currentspan))
    FPW_yz_angle = math.degrees(math.atan((fpw_wire_y_offset_Next - fpw_wire_y_offset) / currentspan))

    # XY 평면 각도 계산
    AF_xy_angle = math.degrees(math.atan((AF_X_offset_Next - AF_X_offset) / currentspan))
    FPW_xy_angle = math.degrees(math.atan((fpw_wire_X_offset_Next - fpw_wire_X_offset) / currentspan))

    return AF_X_offset,AF_y_offset , fpw_wire_X_offset, fpw_wire_y_offset , AF_yz_angle, FPW_yz_angle ,AF_xy_angle , FPW_xy_angle ,AF_X_offset_Next, fpw_wire_X_offset_Next

def get_wire_offsetanlge(DESIGNSPEED, current_structure):
    """AF,FPW offset을 반환하는 기본 딕셔너리(x,y)"""
    AF_offset_values = {
        150: {
            'prefix': 'Cako150',
            '토공': (0,0),
            '교량': (-0.5,0),
            '터널': (-0.28,-1.75)
        },
        250: {
            'prefix': 'Cako250',
            '토공': (0, 0),
            '교량': (-0.5, 0),
            '터널': (-0.28, -1.75)
        },
        350: {
            'prefix': 'Cako350',
            '토공': (-2.732, -1.043),
            '교량': (-0.785, 0.905),
            '터널': (3.98, 0.828)
        }
    }

    FPW_offset_values = {
        150: {
            'prefix': 'Cako150',
            '토공': (0,0),
            '교량': (-0.5,0),
            '터널': (0.93,0)
        },
        250: {
            'prefix': 'Cako250',
            '토공': (0, 0),
            '교량': (-0.5, 0),
            '터널': (0.93, 0)
        },
        350: {
            'prefix': 'Cako350',
            '토공': (-0.193, 0.592),
            '교량': (-0.4389, 0.573),
            '터널': (0.1, 0)
        }
    }
    AF_data = AF_offset_values.get(DESIGNSPEED, AF_offset_values[250])    
    AF_X_offset, AF_y_offset = AF_data[current_structure]
    FPW_data = FPW_offset_values.get(DESIGNSPEED, FPW_offset_values[250])    
    fpw_wire_X_offset, fpw_wire_y_offset = FPW_data[current_structure]
    
    return [AF_X_offset,AF_y_offset , fpw_wire_X_offset, fpw_wire_y_offset]

def buffered_write(filename, lines):
    """파일 쓰기 버퍼 함수"""
    filename = "C:/TEMP/" + filename
    with open(filename, "w", encoding="utf-8") as f: 
        f.writelines(lines)

def get_wire_span_data(DESIGNSPEED, currentspan, current_structure):
    """ 경간에 따른 wire 데이터 반환 """
    # SPEED STRUCTURE span 45, 50, 55, 60
    span_data = {
        150: {
            'prefix': 'Cako150',
            '토공': (592, 593, 594, 595),  # 가고 960
            '교량': (592, 593, 594, 595),  # 가고 960
            '터널': (614, 615, 616, 617)  # 가고 710
        },
        250: {
            'prefix': 'Cako250',
            '토공': (484, 478, 485, 479),  # 가고 1200
            '교량': (484, 478, 485, 479),  # 가고 1200
            '터널': (494, 495, 496, 497)  # 가고 850
        },
        350: {
            'prefix': 'Cako350',
            '토공': (488, 489, 490, 491),  # 가고 1400
            '교량': (488, 489, 490, 491),  # 가고 1400
            '터널': (488, 489, 490, 491)  # 가고 1400
        }
    }

    # DESIGNSPEED에 맞는 구조 선택 (기본값 250 사용)
    span_values = span_data.get(DESIGNSPEED, span_data[250])
    
    # current_structure에 맞는 값 추출
    current_structure_list = span_values[current_structure]

    # currentspan 값을 통해 인덱스를 추출
    span_index_mapping = {
        45: (0, '경간 45m', 1236, 1241),
        50: (1, '경간 50m', 1237, 1242),
        55: (2, '경간 55m', 1238, 1243),
        60: (3, '경간 60m', 1239, 1244)
    }
    
    # currentspan이 유효한 값인지 확인
    if currentspan not in span_index_mapping:
        raise ValueError(f"Invalid span value '{currentspan}'. Valid values are 45, 50, 55, 60.")

    # currentspan에 해당하는 인덱스 및 주석 추출
    idx, comment, feeder_idx, fpw_idx = span_index_mapping[currentspan]
    # idx 값을 current_structure_list에서 가져오기
    idx_value = current_structure_list[idx]

    return idx_value, comment, feeder_idx, fpw_idx

def get_lateral_offset_and_angle(index, currentspan):
    """ 홀수/짝수 전주에 따른 편위 및 각도 계산 """
    sign = -1 if index % 2 == 1 else 1
    return sign * 0.2, -sign * math.degrees(0.4 / currentspan)

def handle_curve_and_straight_section(pos, next_pos, currentspan, polyline_with_sta, current_airjoint, obj_index, comment, currnet_type ,current_structure, next_structure):
    """ 직선, 곡선 구간 wire 처리 """
    lines = []
    sign = -1 if currnet_type == 'I' else 1
    
    lateral_offset = sign * 0.2    
    x,y = get_bracket_coordinates(DESIGNSPEED, 'AJ형_시점')
    x1,y1 = get_bracket_coordinates(DESIGNSPEED, 'F형_시점')
    x2,y2 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_중간1')
    x3,y3 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_중간2')
    x4,y4 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_끝')
    x5,y5 = get_bracket_coordinates(DESIGNSPEED, 'F형_끝')
    
    #구조물 OFFSET 가져오기
    gauge = get_pole_gauge(DESIGNSPEED, current_structure)
    next_gauge = get_pole_gauge(DESIGNSPEED, next_structure)
    #전차선 정보 가져오기
    contact_object_index, messenger_object_index, system_heigh, contact_height = get_contact_wire_and_massanger_wire_info(DESIGNSPEED ,current_structure, currentspan)

    
    #에어조인트 구간 처리
    if current_airjoint == '에어조인트 시작점 (1호주)':

        #본선
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, lateral_offset, x)  
        lines.append(f'{pos},.freeobj 0;{obj_index};{lateral_offset};0;{adjusted_angle};,;본선\n')
        
        #무효선
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, gauge, x1)#평면각도
        slope_degree1, slope_degree2, h1, h2, pererall_d, sta2 = initialrize_tenstion_device(pos, gauge, currentspan, contact_height + y1, system_heigh, adjusted_angle)
        lines.append(f'{sta2},.freeobj 0;{messenger_object_index};{pererall_d};{h2};{adjusted_angle};{slope_degree1},;무효조가선\n')
        lines.append(f'{sta2},.freeobj 0;{contact_object_index};{pererall_d};{h1};{adjusted_angle};{slope_degree2},;무효전차선\n')
        
    elif current_airjoint == '에어조인트 (2호주)':
        #본선 각도        
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, x, x3)
        lines.append(f"{pos},.freeobj 0;{obj_index};{x};0;{adjusted_angle};,;본선\n")
        
        #무효선 각도
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, x1, x2)
        adjusted_angle2 = calculate_slope(y1, contact_height, currentspan)#상하각도
        lines.append(f"{pos},.freeobj 0;{obj_index};{x1};{y1};{adjusted_angle};{adjusted_angle2},;무효선\n")
        
    elif current_airjoint == '에어조인트 중간주 (3호주)':
        #본선 각도
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, x3, x5)
        lines.append(f"{pos},.freeobj 0;{obj_index};{x3};0;{adjusted_angle};,;본선\n")
        #무효선 각도
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, x2, x4)
        adjusted_angle2 = calculate_slope(contact_height, contact_height + y1, currentspan)#상하각도
        lines.append(f"{pos},.freeobj 0;{obj_index};{x2};0;{adjusted_angle};{adjusted_angle2},;무효선\n")
        
    elif current_airjoint == '에어조인트 (4호주)':
        #본선 각도
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, x4, -lateral_offset)  
        lines.append(f"{pos},.freeobj 0;{obj_index};{x4};0;{adjusted_angle};,;본선\n")

        
        #무효선
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, x5, next_gauge)
        slope_degree1, slope_degree2, _, _, _, _ = initialrize_tenstion_device(pos, gauge, currentspan, contact_height + y1, system_heigh, adjusted_angle)
        lines.append(f'{pos},.freeobj 0;{messenger_object_index};{x5};{contact_height +system_heigh + y1};{adjusted_angle};{slope_degree1},;무효조가선\n')
        lines.append(f'{pos},.freeobj 0;{contact_object_index};{x5};{contact_height + y1};{adjusted_angle};{slope_degree2},;무효전차선\n')
        
    #일반구간
    else:
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, lateral_offset, -lateral_offset)
        lines.append(f"{pos},.freeobj 0;{obj_index};{lateral_offset};;{adjusted_angle};,;{comment}\n")
    return lines

def calculate_slope(h1, h2, gauge):
    """주어진 높이 차이와 수평 거리를 바탕으로 기울기 계산"""
    slope = (h1 - h2) / gauge
    return slope

def initialrize_tenstion_device(pos, gauge, currentspan, contact_height, system_heigh, adjusted_angle):
    #장력장치 치수
    tension_device_length = 7.28
    
    #전선 각도
    new_length = currentspan - tension_device_length #현재 span에서 장력장치까지의 거리
    pererall_d ,  vertical_offset = return_new_point(gauge, currentspan, tension_device_length)#선형 시작점에서 전선까지의 거리

    sta2 = pos + vertical_offset #전선 시작 측점
    h1 = 5.56 #장력장치 조가선 높이
    h2 = 6.06 #장력장치 전차선 높이
    slope_radian1 = math.atan((h2 - (contact_height +system_heigh)) / currentspan)#조가선 각도(라디안)
    slope_radian2 = math.atan((h1 - (contact_height)) / currentspan)#전차선 각도(라디안)
    slope_degree1 = math.degrees(slope_radian1)#조가선 각도(도)
    slope_degree2 = math.degrees(slope_radian2)#전차선 각도(도)

    return slope_degree1, slope_degree2, h1, h2, pererall_d, sta2

# 새로운 점 계산 함수
def return_new_point(x, y, L):
    A = (x, 0)  # A점 좌표
    B = (0, 0)  # 원점 B
    C = (0, y)  # C점 좌표
    theta = math.degrees(abs(math.atan(y/x)))
    D = calculate_destination_coordinates(A[0], A[1], theta, L)  # 이동한 D점 좌표
    E = B[0],B[1] + D[1]
    d1 = calculate_distance(D[0], D[1], E[0], E[1])
    d2 = calculate_distance(B[0], B[1], E[0], E[1])

    # 외적을 이용해 좌우 판별
    v_x, v_y = C[0] - B[0], C[1] - B[1]  # 선분 벡터
    w_x, w_y = A[0] - B[0], A[1] - B[1]  # 점에서 선분 시작점까지의 벡터
    cross = v_x * w_y - v_y * w_x  # 외적 계산
    sign = -1 if cross > 0 else 1
        
    return d1 * sign, d2

def calculate_curve_angle(polyline_with_sta, pos, next_pos, stagger1, stagger2):
    point_a, P_A, vector_a = interpolate_coordinates(polyline_with_sta, pos)
    point_b, P_B, vector_b = interpolate_coordinates(polyline_with_sta, next_pos)

    if point_a and point_b:
        
        offset_point_a = calculate_offset_point(vector_a, point_a, stagger1)
        offset_point_b = calculate_offset_point(vector_b, point_b, stagger2)
        
        offset_point_a_z = (offset_point_a[0],offset_point_a[1] ,0) #Z값 0추가
        offset_point_b_z = (offset_point_b[0],offset_point_b[1] ,0) #Z값 0추가
    
        a_b_angle = calculate_bearing(offset_point_a[0], offset_point_a[1], offset_point_b[0], offset_point_b[1])
        finale_anlge = vector_a - a_b_angle
    return finale_anlge

def get_pole_gauge(DESIGNSPEED, current_structure):
    GAUGE_dictionary = {
        150: {'토공': -3, '교량': -3.5, '터널': 2.1},
        250: {'토공': -3, '교량': -3.5, '터널': 2.1},
        350: {'토공': -3.25, '교량': -3.7, '터널': 2.1}
    }
    gauge = GAUGE_dictionary.get(DESIGNSPEED, {}).get(current_structure, "알 수 없는 구조")
    return gauge

def get_airjoint_angle(gauge, stagger, span):
    
    S_angle = abs(math.degrees((gauge + stagger) / span)) if span != 0 else 0.0
    E_angle = abs(math.degrees((gauge - stagger) / span)) if span != 0 else 0.0

    return S_angle, E_angle

def get_contact_wire_and_massanger_wire_info(DESIGNSPEED ,current_structure, span):

    inactive_contact_wire = {40: 1257, 45:1258, 50:1259, 55:1260 ,60:1261}#무효 전차선 인덱스
    inactive_messenger_wire = {40: 1262, 45:1263, 50:1264, 55:1265 ,60:1266}#무효 조가선 인덱스

    # 객체 인덱스 가져오기 (기본값 60)
    contact_object_index = inactive_contact_wire.get(span, 1261)
    messenger_object_index = inactive_messenger_wire.get(span, 1266)
    
    # 가고와 전차선 높이정보
    contact_height_dictionary = {
        150: {'토공': (0.96, 5.2), '교량': (0.96, 5.2), '터널': (0.71, 5)},
        250: {'토공': (1.2, 5.2), '교량': (1.2, 5.2), '터널': (0.85, 5)},
        350: {'토공': (1.4, 5.1), '교량': (1.4, 5.1), '터널': (1.4, 5.1)}
    }

    contact_data = contact_height_dictionary.get(DESIGNSPEED, contact_height_dictionary[250])
    system_heigh, contact_height = contact_data.get(current_structure, (0, 0))  # 기본값 (0, 0) 설정


    return contact_object_index, messenger_object_index, system_heigh, contact_height

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
            x,y = calculate_destination_coordinates(x1, y1, v1, t)
            z = z1 + t * (z2 - z1)
            return (x, y, z), (x1, y1, z1) ,v1
    
    return None  # 범위를 벗어난 sta 값에 대한 처리

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
    last_block = None  # None으로 초기화하여 값이 없을 때 오류 방지
    
    for line in data:
        if isinstance(line, str):  # 문자열인지 확인
            match = re.search(r'(\d+),', line)
            if match:
                last_block = int(match.group(1))  # 정수 변환하여 저장
    
    return last_block  # 마지막 블록 값 반환

def read_file():
    root = tk.Tk()
    root.withdraw()  # Tkinter 창을 숨김
    file_path = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("txt files", "curve_info.txt"), ("All files", "*.*")])
    
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

#추가
#방위각 거리로 점 좌표반환
def calculate_destination_coordinates(x1, y1, bearing, distance):
    # Calculate the destination coordinates given a starting point, bearing, and distance in Cartesian coordinates
    angle = math.radians(bearing)
    x2 = x1 + distance * math.cos(angle)
    y2 = y1 + distance * math.sin(angle)
    return x2, y2

#offset 좌표 반환
def calculate_offset_point(vector, point_a, offset_distance):
    if offset_distance > 0:#우측 오프셋
        vector -= 90
    else:
        vector += 90 #좌측 오프셋
    offset_a_xy = calculate_destination_coordinates(point_a[0], point_a[1], vector, abs(offset_distance))
    return offset_a_xy

def calculate_bearing(x1, y1, x2, y2):
    # Calculate the bearing (direction) between two points in Cartesian coordinates
    dx = x2 - x1
    dy = y2 - y1
    bearing = math.degrees(math.atan2(dy, dx))
    return bearing

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

def load_coordinates():
    """BVE 좌표 데이터를 텍스트 파일에서 불러오는 함수"""
    coord_filepath = 'c:/temp/bve_coordinates.txt'
    return read_polyline(coord_filepath)

def save_pole_data(pole_positions, structure_list, curve_list, DESIGNSPEED, airjoint_list):
    """전주 데이터를 텍스트 파일로 저장하는 함수"""
    save_to_txt(pole_positions, structure_list, curve_list, DESIGNSPEED, airjoint_list, filename="전주.txt")
    print(f"✅ 전주 데이터가 'C:/TEMP/전주.txt' 파일로 저장되었습니다!")

def save_wire_data(pole_positions, spans, structure_list, curvelist, polyline, airjoint_list):
    """전차선 데이터를 텍스트 파일로 저장하는 함수"""
    process_to_WIRE(pole_positions, spans, structure_list, curvelist, polyline, airjoint_list, filename="전차선.txt")
    print(f"✅ 전차선 데이터가 'C:/TEMP/전차선.txt' 파일로 저장되었습니다!")

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

def main():
    """전체 작업을 관리하는 메인 함수"""
    #고속철도인지 확인
    global DESIGNSPEED

    DESIGNSPEED = get_designspeed()
    
    # 파일 읽기 및 데이터 처리
    data = read_file()
    last_block = find_last_block(data)
    start_km = 0
    end_km = last_block // 1000
    spans, pole_positions = distribute_pole_spacing_flexible(start_km, end_km)

    # 구조물 정보 로드
    structure_list = load_structure_data()
    if structure_list:
        print("구조물 정보가 성공적으로 로드되었습니다.")

    # 곡선 정보 로드
    curvelist = load_curve_data()
    if curvelist:
        print("곡선 정보가 성공적으로 로드되었습니다.")
    
    # BVE 좌표 로드
    polyline = load_coordinates()

    
    airjoint_list = define_airjoint_section(pole_positions)

    #전주번호 추가
    post_number_lst = generate_postnumbers(pole_positions)
    
    # 데이터 저장
    save_pole_data(pole_positions, structure_list, curvelist, DESIGNSPEED, airjoint_list)
    save_wire_data(pole_positions, spans, structure_list, curvelist, polyline, airjoint_list)
    #createtxt('c:/temp/airjoint_list.txt', airjoint_list)
    
    # 최종 출력
    print(f"전주 개수: {len(pole_positions)}")
    print(f"마지막 전주 위치: {pole_positions[-1]}m (종점: {int(end_km * 1000)}m)")
    print('모든 작업 완료')
# 실행
if __name__ == "__main__":
    main()
