import csv
from dataclasses import dataclass, field
from tkinter import filedialog, ttk, messagebox
import tkinter as tk
from PIL import Image, ImageDraw, ImageFont
import os
import pandas as pd
import math
import re
import textwrap
from enum import Enum
import matplotlib.pyplot as plt
import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import numpy as np
import shutil
import os

class CurveDirection(Enum):
    LEFT = '좌향'
    RIGHT = '우향'

@dataclass
class IPdata:
    IPNO: int = 0
    curvetype: str = '' #곡선 종류(원곡선, 완화곡선, 복심곡선)
    curve_direction: CurveDirection = CurveDirection.RIGHT  # 기본값 우향
    radius: float = 0.0
    cant: float = 0.0
    BC_STA: float = 0.0
    EC_STA: float = 0.0
    SP_STA: float = 0.0
    PC_STA: float = 0.0
    CP_STA: float = 0.0
    PS_STA: float = 0.0

@dataclass
class ObjectDATA:
    station: float = 0.0
    object_index: int = 0
    filename: str = ''
    structure: str = ''

def read_file():
    file_path = filedialog.askopenfilename(defaultextension=".txt",
                                           filetypes=[("txt files", "curve_info.txt"), ("All files", "*.*")])
    print('현재파일:', file_path)

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            lines = list(reader)
    except UnicodeDecodeError:
        print('현재파일은 utf-8인코딩이 아닙니다. euc-kr로 시도합니다.')
        try:
            with open(file_path, 'r', encoding='euc-kr') as file:
                reader = csv.reader(file)
                lines = list(reader)
        except UnicodeDecodeError:
            print('현재파일은 euc-kr인코딩이 아닙니다. 파일을 읽을 수 없습니다.')
            return []
    return lines

def remove_duplicate_radius(data):
    filtered_data = []
    previous_radius = None

    for row in data:
        try:
            station, radius, cant = map(float, row)
        except ValueError:
            print(f"잘못된 데이터 형식: {row}")
            continue

        if radius != previous_radius:
            filtered_data.append((station, radius, cant))
            previous_radius = radius

    return filtered_data

def process_sections(data):
    sections = []
    current_section = []

    for row in data:
        try:
            station, radius, cant = map(float, row)
        except ValueError:
            print(f"잘못된 데이터 형식: {row}")
            continue

        current_section.append((station, radius, cant))

        if radius == 0.0 and current_section:
            sections.append(current_section)
            current_section = []

    return sections

def annotate_sections(sections):
    ipdatas: list[IPdata] = []
    i = 1
    for section in sections:
        if not section:
            continue

        # 조건에 맞게 구간 종료 판단 (예: radius == 0)
        # 곡선 방향 판단
        direction = CurveDirection.LEFT if section[0][1] < 0 else CurveDirection.RIGHT

        # 완화곡선/원곡선 타입 판단
        if len(section) == 1:
            curvetype = '직선'
        elif len(section) == 2:
            curvetype = '원곡선'
        else:
            curvetype = '완화곡선'

        # 좌향일 때 완화곡선은 가장 큰 값, 원곡선은 가장 작은 값
        # 우향일 때 완화곡선은 가장 작은 값, 원곡선은 가장 큰 값
        # 0 제외한 필터링된 리스트 생성
        filtered_section = [row for row in section if row[1] != 0]
        if not filtered_section:
            # 모두 반경 0이면 무시
            continue

        # 가장 작은/큰 곡률반경 값
        min_value = min(filtered_section, key=lambda x: x[1])[1]
        max_value = max(filtered_section, key=lambda x: x[1])[1]

        # 원래 section에서 해당 값의 첫 인덱스 찾기
        min_index = next(i for i, row in enumerate(section) if row[1] == min_value)
        max_index = next(i for i, row in enumerate(section) if row[1] == max_value)
        if curvetype == '완화곡선':
            if direction == CurveDirection.LEFT:
                selected_radius = max_value
                selected_cant = section[max_index][2]
                pc_sta = section[max_index][0]
                cp_sta = section[max_index + 1][0]
            else:
                selected_radius = min_value
                selected_cant = section[min_index][2]
                pc_sta = section[min_index][0]
                cp_sta = section[min_index + 1][0]

        else:  # 원곡선
            if direction == '좌향':
                selected_radius = min_value
                selected_cant = section[min_index][2]
            else:
                selected_radius = max_value
                selected_cant = section[max_index][2]

        if curvetype == '원곡선':
            # IPdata 생성 (예시, 필요에 따라 STA값 할당 조정)
            ipdata = IPdata(
                IPNO=i,
                curvetype=curvetype,
                curve_direction=direction,
                radius=abs(selected_radius),
                cant=abs(selected_cant),
                BC_STA=section[0][0],
                EC_STA=section[-1][0]
            )
            ipdatas.append(ipdata)
            i += 1
        if curvetype == '완화곡선':
            # IPdata 생성 (예시, 필요에 따라 STA값 할당 조정)
            ipdata = IPdata(
                IPNO=i,
                curvetype=curvetype,
                curve_direction=direction,
                radius=abs(selected_radius),
                cant=abs(selected_cant),
                SP_STA=section[0][0],
                PC_STA=pc_sta,
                CP_STA=cp_sta,
                PS_STA=section[-1][0]
            )
            ipdatas.append(ipdata)
            i += 1

    return ipdatas

def process_sections_for_images(ipdatas: list[IPdata], structure_list, work_directory):
    """주어진 구간 정보를 처리하여 이미지 및 CSV 생성"""

    image_names = []
    structure_comment = []
    objec_index_name = ''
    objec_index_counter = 2025
    line = []
    for i in range(len(ipdatas) - 1):
        cant = ipdatas[i].cant
        radius = ipdatas[i].radius

        if ipdatas[i].curvetype == '원곡선':
            bc_sta = ipdatas[i].BC_STA
            ec_sta = ipdatas[i].EC_STA

            line = [['BC',bc_sta], ['EC',ec_sta]]
            isSPPS = False

        if ipdatas[i].curvetype == '완화곡선':
            sp = ipdatas[i].SP_STA
            pc = ipdatas[i].PC_STA
            cp = ipdatas[i].CP_STA
            ps = ipdatas[i].PS_STA
            line = [['SP',sp], ['PC',pc], ['CP', cp], ['PS', ps]]
            isSPPS = True

        for key, value in line:
            # 구조물 정보 확인
            structure = isbridge_tunnel(value, structure_list)
            img_text = format_distance(value)
            img_f_name = f'IP{i}_{key}'
            openfile_name = f'{key}_{structure}용'
            create_png_from_ai(key, img_text, cant, filename=img_f_name)
            copy_and_export_csv(openfile_name, img_f_name, isSPPS, radius, key)

    return structure_comment


def isbridge_tunnel(sta, structure_list):
    """sta가 교량/터널/토공 구간에 해당하는지 구분하는 함수"""
    for start, end in structure_list['bridge']:
        if start <= sta <= end:
            return '교량'

    for start, end in structure_list['tunnel']:
        if start <= sta <= end:
            return '터널'

    return '토공'

def process_curve_type(i, ipdatas: list[IPdata], structure_list):
    """곡선 형식별 이미지 및 CSV 생성"""


    # 구조물 정보 확인
    structure = isbridge_tunnel(sta, structure_list)

    for key, values in curve_types.items():
        if key in line:
            img_text = format_distance(sta)
            img_f_name = f'IP{i}_{key}'
            openfile_name = f'{key}_{structure}용'
            isSPPS = key in ['SP', 'PS']

            create_png_from_ai(key, img_text, cant, filename=img_f_name)
            copy_and_export_csv(openfile_name, img_f_name, isSPPS, radius, key)

            return img_f_name, structure, isSPPS, radius, key

    return None, None, False, 0, 'ERROR'

work_directory = 'c:/temp/'
lines = read_file()
remove_duplicatedata = remove_duplicate_radius(lines)
sectionsdata = process_sections(remove_duplicatedata)
ipdatas = annotate_sections(sectionsdata)
print('a')