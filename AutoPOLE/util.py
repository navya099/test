import re
import pandas as pd
import math


def isbridge_tunnel(sta, structure_list):
    """sta가 교량/터널/토공 구간에 해당하는지 구분하는 함수"""
    for start, end in structure_list['bridge']:
        if start <= sta <= end:
            return '교량'

    for start, end in structure_list['tunnel']:
        if start <= sta <= end:
            return '터널'

    return '토공'


def check_isairjoint(input_sta, airjoint_list):
    for data in airjoint_list:
        sta, tag = data
        if input_sta == sta:
            return tag


def get_block_index(current_track_position, block_interval=25):
    """현재 트랙 위치를 블록 인덱스로 변환"""
    return math.floor(current_track_position / block_interval + 0.001) * block_interval


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


def find_last_block(data):
    last_block = None  # None으로 초기화하여 값이 없을 때 오류 방지

    for line in data:
        if isinstance(line, str):  # 문자열인지 확인
            match = re.search(r'(\d+),', line)
            if match:
                last_block = int(match.group(1))  # 정수 변환하여 저장

    return last_block  # 마지막 블록 값 반환


def create_dic(*args):
    dic = {}
    for i, arg in enumerate(args):
        dic[f'{i}'] = arg  # 'arg1', 'arg2', ..., 'argN' as keys
    return dic

def find_post_number(lst, pos):
    for arg in lst:
        if arg[0] == pos:
            return arg[1]

def buffered_write(filename, lines):
    """파일 쓰기 버퍼 함수"""
    filename = "C:/TEMP/" + filename
    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(lines)
