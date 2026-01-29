import csv
from dataclasses import dataclass
from enum import Enum
from functools import partial
from tkinter import filedialog, ttk, messagebox, simpledialog
import tkinter as tk
from PIL import Image, ImageDraw, ImageFont
import os
import pandas as pd
import math
import re
import textwrap
import fitz  # pymupdf
import matplotlib.pyplot as plt
import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import numpy as np
import shutil
import os


'''
BVE파일을 바탕으로 거리표(준고속용)을 설치하는 프로그램
-made by dger -


입력파일:BVE에서 추출한 구배파일 OR 곡선파일 (pitch_info.TXT)

pitch_info 샘플
25,0
550,0
575,-0.00117
600,-0.0043
625,-0.00664
650,-0.00977
675,-0.01211
700,-0.01523
725,-0.01836
750,-0.0207

준비파일: base 오브젝트 bvc토공용.csv 등
csv파일에는 텍스쳐명이 bvc와 g 이어야함

출력파일: OBJECT인덱스 파일 , FREEOBJ구문파일, CSV오브젝트파일, PNG텍스쳐파일

'''
from tqdm import tqdm

from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm

def km_task(i, interval, structure_list, alignmenttype, source_directory, work_directory, target_directory, offset, first_index):
    current_sta = i * interval
    current_structure = isbridge_tunnel(current_sta, structure_list)

    # km표/m표 구분
    post_type = 'km표' if current_sta % 1000 == 0 else 'm표'

    current_km_int = round(current_sta * 0.001, 1)
    km_string, m_string = f"{current_km_int:.1f}".split('.')

    img_text1 = km_string
    img_text2 = m_string
    img_f_name = str(current_sta)
    img_bg_color = (2, 6, 140)
    text_color = (255, 255, 255)
    openfile_name = f'{post_type}_{current_structure}용'

    # 이미지 생성
    if alignmenttype in ['도시철도', '일반철도']:
        process_dxf_image(img_text1, img_text2, img_f_name,
                          source_directory, work_directory, post_type, alignmenttype)
    else:
        if len(img_text2) != 1:
            img_text2 = resize_to_length(img_text2, desired_length=1)
        if post_type == 'km표':
            create_km_image(img_text1, img_bg_color, img_f_name, text_color,
                            work_directory, image_size=(500, 300), font_size=235)
        elif post_type == 'm표' and int(m_string) != 0:
            create_m_image(img_text1, img_text2, img_bg_color, img_f_name, text_color,
                           work_directory, image_size=(250, 400), font_size=144, font_size2=192)

    # CSV 생성
    copy_and_export_csv(openfile_name, img_f_name, post_type,
                        source_directory, work_directory, offset)

    # 구문 데이터 생성
    index = first_index + i
    index_data = create_km_index_data(index, current_sta, target_directory)
    post_data = create_km_post_data(index, current_sta, current_structure)

    return index_data, post_data
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


def find_block(data, start=True):
    block = None  # None으로 초기화하여 값이 없을 때 오류 방지
    if start:
        index = 0
    else:
        index = -1
    block = float(data[index].strip().split(',')[0])

    return block  # 마지막 블록 값 반환


def create_km_image(text, bg_color, filename, text_color, work_directory, image_size=(500, 300), font_size=40):
    # 이미지 생성
    img = Image.new('RGB', image_size, color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # 폰트 설정
    try:
        font = ImageFont.truetype('c:/windows/fonts/HYGTRE.ttf', font_size)
    except:
        font = ImageFont.truetype('c:/windows/fonts/H2GTRE.ttf', font_size)
    # 텍스트 박스 크기 (25px 여백 적용)
    box_x1, box_y1 = 25, 25
    box_x2, box_y2 = image_size[0] - 25, image_size[1] - 25
    box_width = box_x2 - box_x1
    box_height = box_y2 - box_y1

    # 줄바꿈 적용
    wrapped_text = textwrap.fill(text, width=15)  # 글자 수 제한
    text_bbox = draw.textbbox((0, 0), wrapped_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # 폰트 크기가 박스를 넘으면 자동 조정
    while text_width > box_width or text_height > box_height:
        font_size -= 2
        font = ImageFont.truetype("gulim.ttc", font_size)
        text_bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

    # 중앙 정렬
    text_x = box_x1 + (box_width - text_width) // 2
    text_y = box_y1 + (box_height - text_height) // 2

    # 이미지에 텍스트 추가
    draw.text((text_x, text_y), wrapped_text, font=font, fill=text_color)

    # 이미지 저장
    if not filename.endswith('.png'):
        filename += '.png'
    final_dir = work_directory + filename
    img.save(final_dir)

def create_m_image(text, text2, bg_color, filename, text_color, work_directory, image_size=(500, 300), font_size=40, font_size2=40 ):
    # 이미지 생성
    img = Image.new('RGB', image_size, color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # 폰트 설정
    try:
        font = ImageFont.truetype('c:/windows/fonts/HYGTRE.ttf', font_size)
        font2 = ImageFont.truetype('c:/windows/fonts/HYGTRE.ttf', font_size2)
    except:
        font = ImageFont.truetype('c:/windows/fonts/H2GTRE.ttf', font_size)
        font2 = ImageFont.truetype('c:/windows/fonts/H2GTRE.ttf', font_size2)
    #km문자 위치
    #글자수별로 글자 분리
    if len(text) == 1:
        text_x = 80
        text_y = 220 
    elif len(text) == 2:
        text_x = 35
        text_y = 220
    elif len(text) == 3:
        text_x = -10
        text_y = 220
    else:
        text_x = 150
        text_y = 220
    
    #m문자 위치
    text_x2 = 60
    text_y2 = 22
    
    #km텍스트 추가
    if not len(text) == 3:
        draw.text((text_x, text_y), text, font=font, fill=text_color)
    else:
        #예시 숫자 '145'
        digit100 = int(text[0]) #1
        digit10 = int(text[1]) #4
        digit1 = int(text[2]) #5
        draw.text((10, text_y), str(digit100), font=font, fill=text_color)#100의자리
        draw.text((72, text_y), str(digit10), font=font, fill=text_color)#10의자리
        draw.text((152, text_y), str(digit1), font=font, fill=text_color)#1의자리
    # 이미지에 텍스트 추가
    draw.text((text_x2, text_y2), text2, font=font2, fill=text_color)
    # 이미지 저장
    if not filename.endswith('.png'):
        filename += '.png'
    final_dir = work_directory + filename
    img.save(final_dir)

def copy_and_export_csv(open_filename='km표-토공용', output_filename='13460', ptype = 'km표' ,source_directory='', work_directory='', offset=0.0):
    # Define the input and output file paths
    open_file = source_directory + open_filename + '.csv'
    output_file = work_directory + output_filename + '.csv'
    
    # List to store modified lines
    new_lines = []
        
    # Open the input file for reading
    with open(open_file, 'r', encoding='utf-8') as file:
        # Iterate over each line in the input file
        for line in file:
            # Replace 'LoadTexture, SP.png,' with 'LoadTexture, output_filename.png,' if found
            if f'LoadTexture, {ptype}.png,' in line:
                line = line.replace(f'LoadTexture, {ptype}.png,', f'LoadTexture, {output_filename}.png,')

            # Append the modified line to the new_lines list
            new_lines.append(line)
    new_lines.append(f'\nTranslateAll, {offset}, 0, 0\n')

    # Open the output file for writing the modified lines
    with open(output_file, 'w', encoding='utf-8') as file:
        # Write the modified lines to the output file
        file.writelines(new_lines)

def find_structure_section(filepath):
    """xlsx 파일을 읽고 교량과 터널 정보를 반환하는 함수"""
    structure_list = {'bridge': [], 'tunnel': []}
    
    # xlsx 파일 읽기
    df_bridge = pd.read_excel(filepath, sheet_name='교량', header=None)
    df_tunnel = pd.read_excel(filepath, sheet_name='터널', header=None)
    
     # 첫 번째 행을 열 제목으로 설정
    df_bridge.columns = ['br_NAME', 'br_START_STA', 'br_END_STA', 'br_LENGTH']
    df_tunnel.columns = ['tn_NAME', 'tn_START_STA', 'tn_END_STA', 'tn_LENGTH']
    
    # 교량 구간과 터널 구간 정보
    for _, row in df_bridge.iterrows():
        structure_list['bridge'].append((row['br_START_STA'], row['br_END_STA']))
    
    for _, row in df_tunnel.iterrows():
        structure_list['tunnel'].append((row['tn_START_STA'], row['tn_END_STA']))
    
    return structure_list

def isbridge_tunnel(sta, structure_list):
    """sta가 교량/터널/토공 구간에 해당하는지 구분하는 함수"""
    for name, start, end in structure_list['bridge']:
        if start <= sta <= end:
            return '교량'
    
    for name, start, end in structure_list['tunnel']:
        if start <= sta <= end:
            return '터널'
    
    return '토공'

def open_excel_file():
    """파일 선택 대화 상자를 열고, 엑셀 파일 경로를 반환하는 함수"""
    root = tk.Tk()
    root.withdraw()  # Tkinter 창을 숨김
    # 대화 상자가 항상 최상위로 표시되도록 설정
    root.attributes("-topmost", True)
    
    file_path = filedialog.askopenfilename(
        title="엑셀 파일 선택",
        filetypes=[("Excel Files", "*.xlsx")]
    )
    
    return file_path

def resize_to_length(text, desired_length=1):
    """
    문자열의 길이가 원하는 길이와 다를 경우 강제로 조정합니다.
    기본적으로 원하는 길이는 1로 설정되어 있습니다.

    Parameters:
    text (str): 입력 문자열
    desired_length (int): 원하는 문자열 길이 (기본값: 1)

    Returns:
    str: 조정된 문자열
    """
    if len(text) != desired_length:
        # 문자열을 원하는 길이로 자르거나, 부족한 경우 앞에 '0'을 채웁니다.
        if len(text) > desired_length:
            return text[:desired_length]
        else:
            return text.zfill(desired_length)
    return text


class DXF2IMG:
    """DXF 파일을 이미지로 변환하는 클래스"""
    default_img_format = '.png'
    default_img_res = 96

    def convert_dxf2img(self, file_paths, img_format=default_img_format, img_res=default_img_res):
        """DXF를 이미지(PNG)로 변환하는 함수"""
        output_paths = []
        for file_path in file_paths:
            if not os.path.exists(file_path):
                print(f"❌ 파일을 찾을 수 없음: {file_path}")
                continue

            try:
                doc = ezdxf.readfile(file_path)
                msp = doc.modelspace()

                # DXF 파일 검증
                auditor = doc.audit()
                if auditor.has_errors:
                    print(f"⚠️ DXF 파일에 오류가 있음: {file_path}")
                    continue

                # Matplotlib 설정
                fig, ax = plt.subplots(figsize=(10, 10))
                ax.set_axis_off()  # 축 제거

                # DXF 렌더링
                ctx = RenderContext(doc)
                out = MatplotlibBackend(ax)
                Frontend(ctx, out).draw_layout(msp, finalize=True)

                # 파일 이름 설정 및 저장 경로 지정
                img_name = re.sub(r"\.dxf$", "", os.path.basename(file_path), flags=re.IGNORECASE)
                output_path = os.path.join(os.path.dirname(file_path), f"{img_name}{img_format}")

                # 이미지 저장
                fig.savefig(output_path, dpi=img_res, bbox_inches='tight', pad_inches=0)
                plt.close(fig)  # 메모리 해제

                print(f"✅ 변환 완료: {output_path}")
                output_paths.append(output_path)

            except Exception as e:
                print(f"❌ 변환 실패: {file_path} - {str(e)}")

        return output_paths

    def convert_doc2img(self, doc, output_path):
        msp = doc.modelspace()
        ctx = RenderContext(doc)
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.set_axis_off()
        out = MatplotlibBackend(ax)
        Frontend(ctx, out).draw_layout(msp, finalize=True)
        fig.savefig(output_path, dpi=96, bbox_inches='tight', pad_inches=0)
        plt.close(fig)

    def trim_and_resize_image(self, input_path, output_path, target_size=(500, 300)):
        """bbox 없이 이미지 여백을 직접 제거하고 500x300 크기로 조정"""
        try:
            img = Image.open(input_path).convert("RGB")
            np_img = np.array(img)

            # 흰색 배경 탐색 (흰색 또는 거의 흰색인 부분 제외)
            mask = np.any(np_img < [250, 250, 250], axis=-1)

            # 유효한 영역 찾기
            coords = np.argwhere(mask)
            if coords.size == 0:
                print("❌ 유효한 이미지 내용을 찾을 수 없음")
                return

            y_min, x_min = coords.min(axis=0)
            y_max, x_max = coords.max(axis=0)

            # 이미지 자르기 (bbox 사용하지 않음)
            cropped_img = img.crop((x_min, y_min, x_max, y_max))

            # 크기 조정 (500x300)
            resized_img = cropped_img.resize(target_size, Image.LANCZOS)
            resized_img.save(output_path)


        except Exception as e:
            print(f"❌ 이미지 처리 실패: {e}")
        #######이미지 생성 로직 끝

class LineProcessor:
    LAYER_RULES = {
        "일반철도": {
            "km": {
                1: [("1자리", lambda km, m: km)],
                2: [
                    ("2자리-앞", lambda km, m: km[0]),
                    ("2자리-뒤", lambda km, m: km[1]),
                ],
                3: [
                    ("3자리-앞", lambda km, m: km[0]),
                    ("3자리-뒤", lambda km, m: km[2]),
                    ("1자리", lambda km, m: km[1]),
                ],
            },
            "m": {
                1: [
                    ("1자리", lambda km, m: km),
                    ("m", lambda km, m: m),
                ],
                2: [
                    ("2자리-앞", lambda km, m: km[0]),
                    ("2자리-뒤", lambda km, m: km[1]),
                    ("m", lambda km, m: m),
                ],
                3: [
                    ("3자리-앞", lambda km, m: km[0]),
                    ("1자리", lambda km, m: km[1]),
                    ("3자리-뒤", lambda km, m: km[2]),
                    ("m", lambda km, m: m),
                ],
            }
        },
        "도시철도": {
            "km": {
                1: [("KM-1자리", lambda km, m: km)],
                2: [("KM-2자리", lambda km, m: km)],
            },
            "m": {
                1: [
                    ("KM-1자리", lambda km, m: km),
                    ("M-1자리", lambda km, m: m[0]),
                ],
                2: [
                    ("KM-2자리-앞", lambda km, m: km[0]),
                    ("KM-2자리-뒤", lambda km, m: km[1]),
                    ("M-1자리", lambda km, m: m[0]),
                ],
            },
        },
    }

    def __init__(self, file_path, modified_path, kmtext, mtext, line_type="normal"):
        self.file_path = file_path
        self.modified_path = modified_path
        self.kmtext = kmtext
        self.mtext = mtext
        self.line_type = line_type  # "normal" or "city"

    def replace_text_in_dxf(self, mode="km"):
        """DXF 텍스트 교체"""
        try:
            doc = ezdxf.readfile(self.file_path)
            msp = doc.modelspace()
            layers = doc.layers

            rules = self.LAYER_RULES[self.line_type][mode]
            length = len(self.kmtext)

            if length not in rules:
                raise ValueError(f"길이 {length}에 대한 규칙 없음")

            for entity in msp.query("TEXT"):
                for layer, text_func in rules[length]:
                    if entity.dxf.layer == layer:
                        entity.dxf.text = text_func(self.kmtext, self.mtext)
                        layers.get(layer).on()


            return doc

        except Exception as e:
            print(f"❌ DXF 수정 실패: {e}")
            return False

def process_dxf_image(img_text1, img_text2, img_f_name, source_directory, work_directory, post_type, alignmenttype):
    """DXF 파일 수정 및 이미지 변환"""
    file_path = os.path.join(source_directory, post_type + '.dxf')
    modifed_path = os.path.join(work_directory, post_type + '-수정됨.dxf')

    lineprogram = LineProcessor(file_path, modifed_path, img_text1, img_text2, alignmenttype)
    mode = 'km' if post_type == 'km표' else 'm'
    doc = lineprogram.replace_text_in_dxf(mode=mode)

    final_output_image = os.path.join(work_directory, img_f_name + '.png')
    converter = DXF2IMG()
    target_size = (200, 250) if alignmenttype == '도시철도' else (180, 650)

    # 멀티프로세싱 고려
    converter.convert_doc2img(doc, final_output_image)
    converter.trim_and_resize_image(final_output_image, final_output_image, target_size)



def create_km_object(start_block, last_block, structure_list, interval,
                     alignmenttype, source_directory, work_directory,
                     target_directory, offset=0.0):
    start_block //= interval
    last_block //= interval
    first_index = 4025
    total = last_block - start_block

    print('-----이미지 생성중-----\n')

    # partial로 인자 고정
    task = partial(km_task, interval=interval,
                   structure_list=structure_list,
                   alignmenttype=alignmenttype,
                   source_directory=source_directory,
                   work_directory=work_directory,
                   target_directory=target_directory,
                   offset=offset,
                   first_index=first_index)

    results = []


    with ProcessPoolExecutor() as executor:
        for res in tqdm(executor.map(task, range(start_block, last_block)),
                        total=total, desc="KM Object 생성"):
            results.append(res)

    index_datas, post_datas = zip(*results)
    return list(index_datas), list(post_datas)


def create_km_index_data(idx, sta, work_directory):
    object_folder = work_directory.split("Object/")[-1]
    data = f'.freeobj({idx}) {object_folder}/{sta}.csv\n'
    return data

def create_km_post_data(idx, sta, struc):
    data = f'{sta},.freeobj 0;{idx};,;{struc}\n'
    return data

def create_txt(output_file, data):
    with open(output_file, 'w', encoding='utf-8') as file:
        for line in data:
            file.write(line)

def select_target_directory():
    """폴더 선택 다이얼로그를 띄워 target_directory를 설정"""
    global target_directory
    root = tk.Tk()
    root.withdraw()  # GUI 창 숨기기

    target_directory = filedialog.askdirectory(title="대상 폴더 선택")

    if target_directory:
        print(f"📁 선택된 대상 폴더: {target_directory}")
    else:
        print("❌ 대상 폴더가 선택되지 않았습니다.")

    return target_directory


def copy_all_files(source_directory, target_directory, include_extensions=None, exclude_extensions=None):
    """
    원본 폴더의 모든 파일을 대상 폴더로 복사 (대상 폴더의 모든 데이터 제거)

    :param source_directory: 원본 폴더 경로
    :param target_directory: 대상 폴더 경로
    :param include_extensions: 복사할 확장자의 리스트 (예: ['.txt', '.csv'] → 이 확장자만 복사)
    :param exclude_extensions: 제외할 확장자의 리스트 (예: ['.log', '.tmp'] → 이 확장자는 복사 안 함)
    """

    # 대상 폴더가 존재하면 삭제 후 다시 생성
    if os.path.exists(target_directory):
        shutil.rmtree(target_directory)  # 대상 폴더 삭제
    os.makedirs(target_directory, exist_ok=True)  # 대상 폴더 재생성

    # 원본 폴더의 모든 파일을 가져와 복사
    for filename in os.listdir(source_directory):
        source_path = os.path.join(source_directory, filename)
        target_path = os.path.join(target_directory, filename)

        # 파일만 처리 (폴더는 복사하지 않음)
        if os.path.isfile(source_path):
            file_ext = os.path.splitext(filename)[1].lower()  # 확장자 추출 후 소문자로 변환

            # 포함할 확장자가 설정된 경우, 해당 확장자가 아니면 건너뛴다
            if include_extensions and file_ext not in include_extensions:
                continue

            # 제외할 확장자가 설정된 경우, 해당 확장자는 복사하지 않는다
            if exclude_extensions and file_ext in exclude_extensions:
                continue

            # 파일 복사 (메타데이터 유지)
            shutil.copy2(source_path, target_path)

    # 모든작업 종료후 원본폴더째로 삭제
    shutil.rmtree(source_directory)

    print(f"📂 모든 파일이 {source_directory} → {target_directory} 로 복사되었습니다.")

def apply_brokenchain_to_structure(structure_list, brokenchain):
    """
    structure_list의 각 구간(start, end)에 brokenchain 값을 더해서
    같은 구조로 반환하는 함수.

    :param structure_list: {'bridge': [(start, end), ...], 'tunnel': [(start, end), ...]}
    :param brokenchain: float, 오프셋 값 (예: 0.0 또는 양수/음수)
    :return: 수정된 structure_list (같은 구조, 값은 offset 적용)
    """
    if brokenchain == 0.0:
        # 오프셋이 없으면 원본 그대로 반환
        return structure_list

    updated_structure = {'bridge': [], 'tunnel': []}

    for key in ['bridge', 'tunnel']:
        for start, end in structure_list.get(key, []):
            new_start = start + brokenchain
            new_end = end + brokenchain
            updated_structure[key].append((new_start, new_end))

    return updated_structure

class KmObjectApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.brokenchain = 0.0
        self.isbrokenchain = False
        self.title("KM Object 생성기")
        self.geometry("600x400")

        self.base_source_directory = 'c:/temp/km_post/소스/'  # 원본 소스 기본 경로
        self.source_directory = self.base_source_directory  # 실제 작업용 경로
        self.work_directory = ''  # 작업물이 저장될 위치
        self.target_directory = ''
        self.structure_excel_path = ''
        self.alignment_type = ''
        self.offset: float = 0.0
        self.create_widgets()

    def create_widgets(self):

        ttk.Label(self, text="KM Object 생성 프로그램", font=("Arial", 16, "bold")).pack(pady=10)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=5)

        ttk.Button(btn_frame, text="구조물 엑셀 파일 선택", command=self.select_excel_file).grid(row=0, column=0, padx=5)

        ttk.Button(self, text="작업 시작", command=self.run_main).pack(pady=10)

        self.log_box = tk.Text(self, height=15, font=("Consolas", 10))
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def log(self, msg):
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)

    def select_excel_file(self):
        filetypes = [("Excel files", "*.xls *.xlsx"), ("All files", "*.*")]
        path = filedialog.askopenfilename(title="구조물 정보 엑셀 파일 선택", filetypes=filetypes)
        if path:
            self.structure_excel_path = path
            self.log(f"선택된 엑셀 파일: {path}")

    def process_interval(self):
        top = tk.Toplevel()
        top.title("노선 구분 선택")
        tk.Label(top, text="노선의 종류를 선택하세요:").pack(pady=10)

        def select(value):
            self.alignment_type = value
            top.destroy()

        for option in ["일반철도", "도시철도", "고속철도"]:
            tk.Button(top, text=option, width=15, command=lambda v=option: select(v)).pack(pady=5)

        top.grab_set()  # 모달처럼 동작
        top.wait_window()

    def process_proken_chain(self):
        # Y/N 메시지박스
        result = messagebox.askyesno("파정 확인", "노선에 거리파정이 존재하나요?")
        if not result:
            return False

        # float 값 입력 받기
        while True:
            value = simpledialog.askstring("파정 입력", "거리파정 값을 입력하세요 (예: 12.34):")
            if value is None:  # 사용자가 취소를 눌렀을 때
                return False
            try:
                self.isbrokenchain = True if float(value) else False
                self.brokenchain = float(value)
                break
            except ValueError:
                messagebox.showerror("입력 오류", "숫자(float) 형식으로 입력하세요.")

        self.log(f"현재 노선의 거리파정 값: {self.brokenchain}")

    def process_offset(self):
        # float 값 입력 받기
        while True:
            value = simpledialog.askstring("오프셋 입력", "오프셋 값을 입력하세요 (예: 12.34):")
            if value is None:  # 사용자가 취소를 눌렀을 때
                return False
            try:
                self.offset = float(value)
                break
            except ValueError:
                messagebox.showerror("입력 오류", "숫자(float) 형식으로 입력하세요.")

        self.log(f"오프셋 값: {self.offset}")

    def run_main(self):
        try:
            # 디렉토리 설정
            self.log("작업 디렉토리 확인 중...")
            self.work_directory = 'c:/temp/km_post/result/'
            if not os.path.exists(self.work_directory):
                os.makedirs(self.work_directory)
                self.log(f"디렉토리 생성: {self.work_directory}")
            else:
                self.log(f"디렉토리 존재: {self.work_directory}")

            # 대상 디렉토리 선택
            self.log("대상 디렉토리 선택 중...")
            self.target_directory = select_target_directory()
            self.log(f"대상 디렉토리: {self.target_directory}")

            #노선 종류 입력받기
            self.process_interval()
            # ✅ 항상 base_source_directory에서 새로 경로 만들기
            self.source_directory = os.path.join(self.base_source_directory, self.alignment_type) + '/'
            self.log(f"소스 경로: {self.source_directory}")

            # ㅊ파정확인
            self.process_proken_chain()

            # 오프셋 적용
            self.process_offset()

            data = read_file()
            if not data:
                self.log("데이터가 비어 있습니다.")
                return

            start_blcok = int(find_block(data, start=True) + self.brokenchain)
            last_block = int(find_block(data, start=False) + self.brokenchain)
            self.log(f"시작 측점 = {start_blcok}")
            self.log(f"마지막 측점 = {last_block}")

            if not self.structure_excel_path:
                self.log("엑셀 파일이 선택되지 않았습니다.")
                messagebox.showwarning("경고", "구조물 정보 엑셀 파일을 선택해주세요.")
                return

            self.log("구조물 정보 불러오는 중...")
            structure_list = find_structure_section(self.structure_excel_path)
            # 구조물 측점 파정처리
            structure_list = apply_brokenchain_to_structure(structure_list, self.brokenchain)

            if structure_list:
                self.log("구조물 정보가 성공적으로 로드되었습니다.")
            else:
                self.log("구조물 정보가 없습니다.")

            intervel = 100 if self.alignment_type == '도시철도' else 200
            self.log("KM Object 생성 중...")
            index_datas, post_datas = create_km_object(start_blcok, last_block, structure_list, intervel, self.alignment_type, self.source_directory, self.work_directory, self.target_directory, self.offset)

            index_file = os.path.join(self.work_directory, 'km_index.txt')
            post_file = os.path.join(self.work_directory, 'km_post.txt')

            self.log(f"파일 작성: {index_file}")
            create_txt(index_file, index_datas)

            self.log(f"파일 작성: {post_file}")
            create_txt(post_file, post_datas)

            self.log("txt 작성이 완료됐습니다.")

            # 파일 복사
            self.log("결과 파일 복사 중...")
            copy_all_files(self.work_directory, self.target_directory, ['.csv', '.png', '.txt'], ['.dxf', '.ai'])

            self.log("모든 작업이 완료됐습니다.")
            messagebox.showinfo("완료", "KM Object 생성이 완료되었습니다.")

        except Exception as e:
            self.log(f"[오류] {str(e)}")
            messagebox.showerror("오류", f"작업 중 오류가 발생했습니다:\n{e}")

if __name__ == "__main__":
    app = KmObjectApp()
    app.mainloop()

    
