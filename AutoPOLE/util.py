import re
import pandas as pd
import math
from dataclasses import dataclass
from typing import Dict, List, Union


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
    return '일반개소'


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


@dataclass
class Bracket:
    inner: int  # I형
    outer: int  # O형
    flat_short: int  # F(S)
    flat_long: int  # F(L)
    airjoint_inner: int  # AJ-I
    airjoint_outer: int  # AJ-O


@dataclass
class GaugeBracketSet:
    gauge: float
    bracket: Bracket


@dataclass
class InstallTypeBracket:
    install_type: str  # 예: OpG, Tn
    gauge_brackets: Dict[float, GaugeBracketSet]  # 게이지별 브래킷 정보


@dataclass
class PoleStructure:
    design_speed: int
    typename: str
    install_brackets: Dict[str, InstallTypeBracket]  # OpG, Tn 등


# 사전 정의한 브래킷 정보 클래스(데이터클래스구조)
class Dictionaryofbracket:
    def __init__(self):
        self.brackettable = {
            150: PoleStructure(
                design_speed=150,
                typename="CaKo150",
                install_brackets={
                    "OpG": InstallTypeBracket(
                        install_type="OpG",
                        gauge_brackets={
                            3.0: GaugeBracketSet(
                                gauge=3.0,
                                bracket=Bracket(
                                    inner=1252,
                                    outer=1253,
                                    flat_short=1328,
                                    flat_long=1328,
                                    airjoint_inner=1252,
                                    airjoint_outer=1253
                                )
                            ),
                            3.5: GaugeBracketSet(
                                gauge=3.5,
                                bracket=Bracket(
                                    inner=1254,
                                    outer=1255,
                                    flat_short=1329,
                                    flat_long=1329,
                                    airjoint_inner=1254,
                                    airjoint_outer=1255
                                )
                            ),
                            2.1: GaugeBracketSet(
                                gauge=2.1,
                                bracket=Bracket(
                                    inner=1250,
                                    outer=1251,
                                    flat_short=1327,
                                    flat_long=1327,
                                    airjoint_inner=1250,
                                    airjoint_outer=1251
                                )
                            )
                        }
                    ),
                    "Tn": InstallTypeBracket(
                        install_type="Tn",
                        gauge_brackets={
                            2.1: GaugeBracketSet(  # 터널은 게이지 2.1만 존재
                                gauge=2.1,
                                bracket=Bracket(
                                    inner=941,
                                    outer=942,
                                    flat_short=1330,
                                    flat_long=1330,
                                    airjoint_inner=941,
                                    airjoint_outer=942
                                )
                            )
                        }
                    )
                }
            ),
            250: PoleStructure(
                design_speed=250,
                typename="CaKo250",
                install_brackets={
                    "OpG": InstallTypeBracket(
                        install_type="OpG",
                        gauge_brackets={
                            3.0: GaugeBracketSet(
                                gauge=3.0,
                                bracket=Bracket(
                                    inner=641,
                                    outer=642,
                                    flat_short=1284,
                                    flat_long=1285,
                                    airjoint_inner=1296,
                                    airjoint_outer=1297
                                )
                            ),
                            3.5: GaugeBracketSet(
                                gauge=3.5,
                                bracket=Bracket(
                                    inner=643,
                                    outer=644,
                                    flat_short=1286,
                                    flat_long=1287,
                                    airjoint_inner=1298,
                                    airjoint_outer=1299
                                )
                            ),
                            2.1: GaugeBracketSet(
                                gauge=2.1,
                                bracket=Bracket(
                                    inner=645,
                                    outer=646,
                                    flat_short=1288,
                                    flat_long=1289,
                                    airjoint_inner=1323,
                                    airjoint_outer=1324
                                )
                            )
                        }
                    ),
                    "Tn": InstallTypeBracket(
                        install_type="Tn",
                        gauge_brackets={
                            2.1: GaugeBracketSet(  # 터널은 게이지 2.1만 존재
                                gauge=2.1,
                                bracket=Bracket(
                                    inner=647,
                                    outer=648,
                                    flat_short=1290,
                                    flat_long=1291,
                                    airjoint_inner=1325,
                                    airjoint_outer=1326
                                )
                            )
                        }
                    )
                }
            ),
            350: PoleStructure(
                design_speed=350,
                typename="CaKo350",
                install_brackets={
                    "OpG": InstallTypeBracket(
                        install_type="OpG",
                        gauge_brackets={
                            3.0: GaugeBracketSet(
                                gauge=3.0,
                                bracket=Bracket(
                                    inner=570,
                                    outer=571,
                                    flat_short=578,
                                    flat_long=579,
                                    airjoint_inner=635,
                                    airjoint_outer=636
                                )
                            ),
                            3.5: GaugeBracketSet(
                                gauge=3.5,
                                bracket=Bracket(
                                    inner=572,
                                    outer=573,
                                    flat_short=580,
                                    flat_long=581,
                                    airjoint_inner=637,
                                    airjoint_outer=638
                                )
                            ),
                            2.1: GaugeBracketSet(
                                gauge=2.1,
                                bracket=Bracket(
                                    inner=1250,
                                    outer=1251,
                                    flat_short=1327,
                                    flat_long=1327,
                                    airjoint_inner=1250,
                                    airjoint_outer=1251
                                )
                            )
                        }
                    ),
                    "Tn": InstallTypeBracket(
                        install_type="Tn",
                        gauge_brackets={
                            2.1: GaugeBracketSet(  # 터널은 게이지 2.1만 존재
                                gauge=2.1,
                                bracket=Bracket(
                                    inner=574,
                                    outer=575,
                                    flat_short=582,
                                    flat_long=583,
                                    airjoint_inner=639,
                                    airjoint_outer=640
                                )
                            )
                        }
                    )
                }
            )
        }

    def get_structure(self, speed: int) -> PoleStructure:
        return self.brackettable.get(speed)

    def get_install_type(self, speed: int, install_type: str) -> InstallTypeBracket:
        structure = self.get_structure(speed)
        if structure:
            return structure.install_brackets.get(install_type)
        return None

    def get_gauge_set(self, speed: int, install_type: str, gauge: float) -> GaugeBracketSet:
        install = self.get_install_type(speed, install_type)
        if install:
            return install.gauge_brackets.get(gauge)
        return None

    def get_bracket_number(self, speed: int, install_type: str, gauge: float, bracket_name: str) -> int:
        gauge_set = self.get_gauge_set(speed, install_type, gauge)
        if gauge_set:
            return getattr(gauge_set.bracket, bracket_name, None)
        return None


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


def get_mast_type(speed, current_structure):
    # 전주 인덱스 딕셔너리(idx,comment)
    mast_dic = {
        150: {
            'prefix': 'Cako150',
            '토공': (1370, 'P-10"x7t-9m'),
            '교량': (1376, 'P-12"x7t-8.5m'),
            '터널': (1400, '터널하수강'),
        },
        250: {
            'prefix': 'Cako250',
            '토공': (1370, 'P-10"x7t-9m'),
            '교량': (1376, 'P-12"x7t-8.5m'),
            '터널': (1400, '터널하수강'),
        },
        350: {
            'prefix': 'Cako350',  # 350
            '토공': (619, 'H형주-208X202'),
            '교량': (620, 'H형주-250X255'),
            '터널': (621, '터널하수강'),
        }
    }
    mast_data = mast_dic.get(speed, mast_dic[250])
    mast_index, mast_name = mast_data.get(current_structure, ("", "알 수 없는 구조"))

    return mast_index, mast_name
