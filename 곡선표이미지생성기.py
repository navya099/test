import csv
from tkinter import filedialog
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

'''
BVE곡선파일을 바탕으로 곡선표(준고속용)을 설치하는 프로그램
-made by dger -
VER 2025.02.25 11.48
#modifyed
코드 구조 리팩토링

입력파일:BVE에서 추출한 곡선파일(CURVE_INFO.TXT)

CURVE_INFO샘플
275,0
300,0
325,0
350,-632.636
375,-632.636
400,679.461
425,679.461
450,0
475,0

준비파일: base 오브젝트 sp토공용.csv 등
csv파일에는 텍스쳐명이 sp와 r 이어야함

출력파일: OBJECT인덱스 파일 , FREEOBJ구문파일, CSV오브젝트파일, PNG텍스쳐파일

'''

    
def format_distance(number):
    return f"{number / 1000:.3f}"

def read_file():
    
    file_path = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("txt files", "curve_info.txt"), ("All files", "*.*")])
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
            station = int(station)
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
            station = int(station)
        except ValueError:
            print(f"잘못된 데이터 형식: {row}")
            continue

        current_section.append((station, radius, cant))

        if radius == 0.0 and current_section:
            sections.append(current_section)
            current_section = []

    return sections

def annotate_sections(sections):
    annotated_sections = []

    for section in sections:
        if not section:
            continue

        annotated_section = []
        n = len(section)

        for i, (station, radius, cant) in enumerate(section):
            annotation = ""

            # 첫 번째 줄에 SP 추가
            if i == 0:
                annotation += "SP"
            
            # 마지막 줄에 PS 추가
            if i == n - 1:
                annotation += "PS"

            # STA 간 차이가 25보다 큰 경우 PC/CP 추가
            if i < n - 1:  # Ensure we're not at the last row
                prev_station, prev_radius, prev_cant = section[i - 1] if i > 0 else (None, None , None)
                next_station, next_radius, next_cant = section[i + 1]
                
                if next_station - station > 75:
                    annotation += "PC"
                elif i > 0 and station - prev_station > 75:
                    annotation += "CP"

            
            annotated_section.append(f"{station},{radius},{cant},{annotation}")

        # SP와 PS만 있는 구간을 BC와 EC로 변경
        if len(annotated_section) == 2 and "SP" in annotated_section[0] and "PS" in annotated_section[1]:
            annotated_section[0] = annotated_section[0].replace("SP", "BC")
            annotated_section[1] = annotated_section[1].replace("PS", "EC")
       
        # SPPS만 있는 구간을 삭제
        elif len(annotated_section) == 1 and "SPPS" in annotated_section[0]:
            continue  # SPPS만 있는 구간은 추가하지 않음
            
        annotated_sections.append(annotated_section)

    return annotated_sections


def create_text_image(text, bg_color, filename, text_color, image_size=(500, 300), font_size=40):
    # 이미지 생성
    img = Image.new('RGB', image_size, color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # 폰트 설정
    font = ImageFont.truetype("gulim.ttc", font_size)

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
    
def copy_and_export_csv(open_filename='SP1700', output_filename='IP1SP',isSPPS = False, R= 3100, curvetype='SP'):
    # Define the input and output file paths
    open_file = work_directory + open_filename + '.csv'
    output_file = work_directory + output_filename + '.csv'
    
    # List to store modified lines
    new_lines = []
        
    # Open the input file for reading
    with open(open_file, 'r', encoding='utf-8') as file:
        # Iterate over each line in the input file
        for line in file:
            # Replace 'LoadTexture, SP.png,' with 'LoadTexture, output_filename.png,' if found
            if f'LoadTexture, {curvetype}.png,' in line:
                line = line.replace(f'LoadTexture, {curvetype}.png,', f'LoadTexture, {output_filename}.png,')
            if isSPPS:
                line = line.replace('LoadTexture, R.png,', f'LoadTexture, {R}.png,')
            
            # Append the modified line to the new_lines list
            new_lines.append(line)
    
    # Open the output file for writing the modified lines
    with open(output_file, 'w', encoding='utf-8') as file:
        # Write the modified lines to the output file
        file.writelines(new_lines)

def create_object_index(data):
    output_file = work_directory + 'object_index.txt'
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(data)

def parse_sections(file_content):
    """
    파일 내용에서 각 구간과 태그를 파싱하여 리스트로 반환.
    """
    sections = {}
    current_section = None
    tags = []
    for line in file_content:  # file_content는 csv.reader가 반환한 리스트 형태
        # 리스트 형태의 line을 문자열로 변환
        line = ",".join(line)
        
        if line.startswith("구간"):
            current_section = int(line.split()[1][:-1])
            sections[current_section] = []
        elif current_section is not None and line.strip():
            sta, radius , cant, tag = line.split(',', 3)
            
            sta = int(sta)
            radius = float(radius)
            cant = float(cant)
            sections[current_section].append((sta, radius, cant, tag))

    return sections




def parse_object_index(index_content):
    """
    object_index.txt 내용을 파싱하여 태그별 인덱스 매핑을 반환.
    """
    tag_mapping = {}

    for row in index_content:  # row는 리스트 형태
        if len(row) != 1:  # 한 줄이 하나의 문자열로 되어 있어야 함
            print(f"잘못된 줄 형식 건너뜀: {row}")
            continue

        line = row[0]  # 리스트 내부의 문자열을 꺼냄
        parts = line.split()  # 공백으로 분리
        if len(parts) < 2:  # 최소한 2개의 요소가 있어야 함
            print(f"잘못된 줄 형식 건너뜀: {line}")
            continue

        try:
            obj_name = parts[1].split('/')[-1].split('.')[0]  # e.g., 구간1_SP
            obj_index = int(parts[0].split('(')[-1].rstrip(')'))
            tag_mapping[obj_name] = obj_index
        except (IndexError, ValueError) as e:
            print(f"오류 발생: {e} - 줄 내용: {line}")
            continue

    return tag_mapping




def find_object_index(sta, sections, tag_mapping):
    """
    STA 값에 해당하는 구간과 태그를 찾아 오브젝트 인덱스를 반환.
    """
    for section_id, points in sections.items():
        for i, (start_sta, _, _, tags) in enumerate(points):
            if sta == start_sta:  # STA가 정확히 일치하는 경우
                key = f"IP{section_id}_{tags}"
                if key in tag_mapping:
                    return tag_mapping[key]
    return None

def create_curve_post_txt(data_list,comment):
    """
    결과 데이터를 받아 파일로 저장하는 함수.
    """
    output_file = work_directory + "curve_post.txt"  # 저장할 파일 이름
    #리스트에서 '\n'을 제거
    data_list = [data.strip() for data in data_list]
    with open(output_file, "w", encoding="utf-8") as file:
         for data, comm in zip(data_list, comment):  # 두 리스트를 동시에 순회
            file.write(f"{data},;{comm}\n")  # 원하는 형식으로 저장
            
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
        structure_list['bridge'].append((row['br_START_STA'], row['br_END_STA']))
    
    for _, row in df_tunnel.iterrows():
        structure_list['tunnel'].append((row['tn_START_STA'], row['tn_END_STA']))
    
    return structure_list

def isbridge_tunnel(sta, structure_list):
    """sta가 교량/터널/토공 구간에 해당하는지 구분하는 함수"""
    for start, end in structure_list['bridge']:
        if start <= sta <= end:
            return '교량'
    
    for start, end in structure_list['tunnel']:
        if start <= sta <= end:
            return '터널'
    
    return '토공'

def open_excel_file():
    """파일 선택 대화 상자를 열고, 엑셀 파일 경로를 반환하는 함수"""
    root = tk.Tk()
    root.withdraw()  # Tkinter 창을 숨김
    root.attributes("-topmost", True)
    
    file_path = filedialog.askopenfilename(
        title="엑셀 파일 선택",
        filetypes=[("Excel Files", "*.xlsx")]
    )
    
    return file_path

def create_png_from_ai(type1 = 'SP', text1 = '14.626',text2 = '150', filename = 'output.png'):
    
    ai_file = work_directory + type1 + '.AI'
    
    doc = fitz.open(ai_file)


    # 텍스트 정보 (소수점 자릿수 계산)
    text_parts = text1.split('.')  # 소수점을 기준으로 나누기
    if len(text_parts) == 2:  # 소수점이 있는 경우
        digit = len(text_parts[0])  # 소수점 뒤 자릿수
    else:
        digit = 0  # 소수점이 없으면 자릿수는 0
    
        # 조정값 설정 (자리수에 따라 텍스트 좌표를 조정)
    if digit == 1:
        cooradjust = 20  # 1자리일 경우 좌표 조정 없음
    elif digit == 2:
        cooradjust = 0  # 2자리일 경우 좌표를 왼쪽으로 조정
    elif digit == 3:
        cooradjust = -10  # 3자리일 경우 좌표를 더 왼쪽으로 조정
    else:
        cooradjust = 0  # 그 외의 경우 오른쪽으로 조정

    if type1 == 'PC' or type1 == 'CP' or type1 == 'BC' or type1 == 'EC':
        x = 121 + cooradjust
        y = 92
    else:
        x = 121 + cooradjust
        y = 115
    # 텍스트 정보(3자리 기준 -10)

    style = "helvetica"
    size = 160.15  # pt 텍스트크기
    color = (255/255, 255/255, 255/255)  # 흰색 (0-1 범위로 변환)

    pt =  2.83465
    # 🔹 mm -> pt 변환 (1mm = 2.83465 pt)
    x_pt = x * pt
    y_pt = y * pt

    size_pt = size  # 이미 pt로 제공되므로 그대로 사용



    # 🔹 텍스트 삽입
    insert_x = x_pt
    insert_y = y_pt

    for page in doc:
        # 텍스트 삽입
        page.insert_text((insert_x, insert_y), text1, fontname=style, fontsize=size_pt, color=color)
    
    # 🔹 원본 크기 가져오기
    page = doc[0]  # 첫 번째 페이지 기준
    pix = page.get_pixmap()
    orig_width, orig_height = pix.width, pix.height

    # 🔹 비율 유지하여 300x200에 맞게 조정
    target_width, target_height = 300, 200
    scale = min(target_width / orig_width, target_height / orig_height)  # 가장 작은 비율 선택
    new_width = int(orig_width * scale)
    new_height = int(orig_height * scale)

    # 🔹 변환 적용 및 PNG 저장
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
    save_file = work_directory + filename + '.png'
    pix.save(save_file)

def create_png_from_ai2(text1 = '600', filename = 'output.png'):
    
    ai_file = work_directory  + '곡선표(일반철도).AI'
    
    doc = fitz.open(ai_file)


    # 텍스트 정보 (소수점 자릿수 계산)
    
    if len(text1) == 3:  # 소수점이 있는 경우
        digit = 3
        x = 8.69
        y = 275
    elif len(text1) == 4:  # 소수점이 있는 경우
        digit = 4
        x = 121 + cooradjust
        y = 92
    elif len(text1) == 5:  # 소수점이 있는 경우
        digit = 5
    elif len(text1) == 6:  # 소수점이 있는 경우
        digit = 6
        x = 0
        y = 0
    # 텍스트 정보(3자리 기준 -10)

    style = "HY견고딕"
    size = 353.11  # pt 텍스트크기
    color = (255/255, 255/255, 255/255)  # 흰색 (0-1 범위로 변환)

    pt =  2.83465
    # 🔹 mm -> pt 변환 (1mm = 2.83465 pt)
    x_pt = x * pt
    y_pt = y * pt

    size_pt = size  # 이미 pt로 제공되므로 그대로 사용



    # 🔹 텍스트 삽입
    insert_x = x_pt
    insert_y = y_pt

    for page in doc:
        # 텍스트 삽입
        page.insert_text((insert_x, insert_y), text1, fontname=style, fontsize=size_pt, color=color)
    
    # 🔹 원본 크기 가져오기
    page = doc[0]  # 첫 번째 페이지 기준
    pix = page.get_pixmap()
    orig_width, orig_height = pix.width, pix.height

    # 🔹 비율 유지하여 300x200에 맞게 조정
    target_width, target_height = 300, 200
    scale = min(target_width / orig_width, target_height / orig_height)  # 가장 작은 비율 선택
    new_width = int(orig_width * scale)
    new_height = int(orig_height * scale)

    # 🔹 변환 적용 및 PNG 저장
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
    save_file = work_directory + filename + '.png'
    pix.save(save_file)

#클래스
def replace_text_in_dxf(file_path, modifed_path, new_text):
    """DXF 파일의 특정 텍스트를 새 텍스트로 교체하는 함수"""
    try:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()

        # 교체할 텍스트 결정 (텍스트 길이에 따라)
        text_mapping = {
            3: '100',
            4: '2000',
            5: '15000',
            6: '150000'
        }
        old_text = text_mapping.get(len(new_text), None)

        if old_text is None:
            print(f"⚠️ 지원되지 않는 텍스트 길이: {new_text}")
            return False

        # DXF 텍스트 엔티티 수정
        for entity in msp.query("TEXT"):
            if entity.dxf.text == old_text:
                entity.dxf.text = new_text  # 텍스트 교체
            else:
                entity.dxf.text = ''  # 나머지 텍스트 삭제

        # 변경된 DXF 저장
        doc.saveas(modifed_path)
        print("✅ 텍스트 교체 완료")
        return True

    except Exception as e:
        print(f"❌ DXF 텍스트 교체 실패: {e}")
        return False


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
            print(f"✅ 여백 제거 및 크기 조정 완료: {output_path}")

        except Exception as e:
            print(f"❌ 이미지 처리 실패: {e}")    

def write_unique_file(filename, unique_data):
    """unique_file을 저장하는 함수"""
    with open(filename, 'w', encoding='utf-8') as file:
        for station, radius, cant in unique_data:
            file.write(f"{station},{radius},{cant}\n")

def write_annotated_sections(filename, annotated_sections):
    """annotated_sections_file을 저장하는 함수"""
    with open(filename, 'w', encoding='utf-8') as file:
        for i, section in enumerate(annotated_sections, start=1):
            file.write(f"구간 {i}:\n")
            for line in section:
                file.write(f"{line}\n")
            file.write("\n")

def write_sections(filename, sections):
    """sections_file을 저장하는 함수"""
    with open(filename, 'w', encoding='utf-8') as file:
        for line in sections:
            file.write(f'{line}\n')

def get_output_file_paths(work_directory):
    """출력 파일 경로 설정"""
    return {
        'unique_file': os.path.join(work_directory, 'unique_file.txt'),
        'annotated_sections_file': os.path.join(work_directory, 'annotated_sections_file.txt'),
        'sections_file': os.path.join(work_directory, 'sections.txt'),
    }


def process_and_save_sections(work_directory, data):
    """곡선 정보를 처리하고 파일로 저장"""
    print("곡선 정보가 성공적으로 로드되었습니다.")

    # 중복 제거
    unique_data = remove_duplicate_radius(data)

    # 구간 정의 및 처리
    sections = process_sections(unique_data)
    annotated_sections = annotate_sections(sections)

    # 파일 경로 설정
    file_paths = get_output_file_paths(work_directory)

    # 파일 저장
    write_unique_file(file_paths['unique_file'], unique_data)
    write_annotated_sections(file_paths['annotated_sections_file'], annotated_sections)
    write_sections(file_paths['sections_file'], sections)

    return file_paths, annotated_sections

def extract_PC_radius(annotated_sections):
    """PC 곡선 반경 리스트 추출"""
    PC_R_LIST = []
    for i, section in enumerate(annotated_sections, start=1):
        for line in section:
            if 'PC' in line:
                parts = line.split(',')
                R = float(parts[1])
                PC_R_LIST.append((i, int(abs(R))))  # 반경 절댓값 사용
    return PC_R_LIST

def process_curve_type(line, i, PC_R_LIST, structure_list):
    """곡선 형식별 이미지 및 CSV 생성"""
    parts = line.split(',')
    sta = int(parts[0])
    cant = f'{float(parts[2]) * 1000:.0f}'
    
    # 반경 찾기
    radius = next((r for sec, r in PC_R_LIST if sec == i), 0)
    
    # 구조물 정보 확인
    structure = isbridge_tunnel(sta, structure_list)

    # 곡선 종류 매핑
    curve_types = {
        'SP': {'bg_color': (34, 139, 34), 'prefix': 'SP'},
        'PC': {'bg_color': (255, 0, 0), 'prefix': 'PC'},
        'CP': {'bg_color': (255, 0, 0), 'prefix': 'CP'},
        'PS': {'bg_color': (34, 139, 34), 'prefix': 'PS'},
        'BC': {'bg_color': (255, 0, 0), 'prefix': 'BC'},
        'EC': {'bg_color': (255, 0, 0), 'prefix': 'EC'}
    }

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

def process_dxf_image(radius, work_directory):
    """DXF 파일 수정 및 이미지 변환"""
    img_f_name_for_prev = str(int(radius))
    file_path = work_directory  + '곡선표.dxf'
    modifed_path = work_directory + '곡선표-수정됨.dxf'
    final_output_image = os.path.join(work_directory, img_f_name_for_prev + '.png')

    replace_text_in_dxf(file_path, modifed_path, img_f_name_for_prev)
    converter = DXF2IMG()
    output_paths = converter.convert_dxf2img([modifed_path], img_format='.png')

    if output_paths:
        converter.trim_and_resize_image(output_paths[0], final_output_image, target_size=(500, 300))

def process_sections_for_images(annotated_sections, structure_list, work_directory):
    """주어진 구간 정보를 처리하여 이미지 및 CSV 생성"""
    PC_R_LIST = extract_PC_radius(annotated_sections)

    image_names = []
    structure_comment = []
    objec_index_name = ''
    objec_index_counter = 2025

    for i, section in enumerate(annotated_sections, start=1):
        for line in section:
            if any(key in line for key in ['BC', 'EC', 'SP', 'PC', 'CP', 'PS']):
                img_f_name, structure, isSPPS, radius, curvetype = process_curve_type(line, i, PC_R_LIST, structure_list)

                if img_f_name:
                    image_names.append(img_f_name)
                    structure_comment.append(f'{img_f_name}-{structure}')

                    if isSPPS and radius != 0:
                        process_dxf_image(radius, work_directory)

    # 객체 인덱스 생성
    object_folder = target_directory.split("Object/")[-1]
    for img_name, stru in zip(image_names, structure_comment):
        objec_index_name += f".freeobj({objec_index_counter}) {object_folder}/{img_name}.CSV\n"
        objec_index_counter += 1

    # 오브젝트 인덱스 파일 생성
    create_object_index(objec_index_name)

    return structure_comment

def find_STA(sections_line1, tag_mapping):
    # STA 값 검색
    result_list =[]

    for section_id, entries in sections_line1.items():  # 모든 구간을 순회
        for sta_value, radius, _, tags in entries:  # 각 구간의 엔트리를 순회

            result = find_object_index(sta_value, sections_line1, tag_mapping)

            if not result == None:
                result_data = f'{sta_value},.freeobj 0;{result};\n'
                result_list.append(result_data)
    return result_list

def read_filedata(data):
    with open(data, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        lines = list(reader)
    return lines

def load_structure_data():
    """구조물 정보 로드"""
    openexcelfile = open_excel_file()
    if openexcelfile:
        structure_list = find_structure_section(openexcelfile)
        print("구조물 정보가 성공적으로 로드되었습니다.")
    else:
        print("엑셀 파일을 선택하지 않았습니다.")
        structure_list = []  # 기본 빈 리스트 반환
    return structure_list

def process_curve_data(work_directory, data, structure_list):
    """곡선 데이터 처리 (파일 저장 및 이미지 & CSV 생성)"""
    if not data:
        print("curve_info가 비어 있습니다.")
        return None, None

    # 중복 제거 및 섹션 처리
    file_paths, annotated_sections = process_and_save_sections(work_directory, data)

    # 이미지 및 CSV 생성
    structure_comment = process_sections_for_images(annotated_sections, structure_list, work_directory)

    return file_paths, structure_comment

def parse_and_match_data(work_directory, file_paths):
    """파일 데이터 파싱 및 태그 매핑"""
    if not file_paths:
        return None

    # 주석처리된 파일 읽기
    annotated_sections_file = file_paths['annotated_sections_file']
    annotated_sections_file_readdata = read_filedata(annotated_sections_file)

    # 오브젝트 인덱스 파일 읽기
    OBJ_DATA = os.path.join(work_directory, 'object_index.txt')
    object_index_file_read_data = read_filedata(OBJ_DATA)

    # 데이터 파싱
    annotated_sections_file_parse = parse_sections(annotated_sections_file_readdata)
    tag_mapping = parse_object_index(object_index_file_read_data)

    # 매칭
    result_list = find_STA(annotated_sections_file_parse, tag_mapping)

    return result_list

def cleanup_files(file_paths):
    """불필요한 파일 삭제"""
    if file_paths:
        for key, file_path in file_paths.items():
            os.remove(file_path)
            print(f"{key} 파일 삭제 완료: {file_path}")

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

    print(f"📂 모든 파일이 {source_directory} → {target_directory} 로 복사되었습니다.")



def select_target_directory():
    """폴더 선택 다이얼로그를 띄워 target_directory를 설정"""
    global target_directory
    root = tk.Tk()
    root.withdraw()  # GUI 창 숨기기

    target_directory = filedialog.askdirectory(initialdir=default_directory, title="대상 폴더 선택")

    if target_directory:
        print(f"📁 선택된 대상 폴더: {target_directory}")
    else:
        print("❌ 대상 폴더가 선택되지 않았습니다.")

       
#함수 종료
#MAIN 시작
# ================== MAIN START ==================

# 기본 작업 디렉토리(#전역변수)
default_directory = 'c:/temp/curve/'
work_directory = None
target_directory = None

# 사용자가 설정한 작업 디렉토리가 없으면 기본값 사용
if not work_directory:
    work_directory = default_directory

# 디렉토리가 존재하지 않으면 생성
if not os.path.exists(work_directory):
    os.makedirs(work_directory)

print(f"작업 디렉토리: {work_directory}")

select_target_directory()

# 곡선 정보 파일 읽기
data = read_file()

# 구조물 데이터 로드
structure_list = load_structure_data()

# 곡선 데이터 처리
file_paths, structure_comment = process_curve_data(work_directory, data, structure_list)

# 데이터 파싱 및 매칭
result_list = parse_and_match_data(work_directory, file_paths)

# 최종 CSV 생성
if result_list:
    create_curve_post_txt(result_list, structure_comment)

# 파일 정리
cleanup_files(file_paths)

#파일 복사
copy_all_files(work_directory,target_directory, ['.csv', '.png', '.txt'], ['.dxf', '.ai'])
print('모든 작업이 끝났습니다.')
