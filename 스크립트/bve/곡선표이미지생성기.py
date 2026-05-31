import csv
from dataclasses import dataclass
from enum import Enum
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
import matplotlib
matplotlib.use('Agg')
'''
BVE곡선파일을 바탕으로 곡선표(준고속용)을 설치하는 프로그램
-made by dger -
VER 2025.08.26
#modifyed
곡선 데이터 클래스화로 코드개선

입력파일:BVE에서 추출한 곡선파일(CURVE_INFO.TXT)

CURVE_INFO샘플(0부터 끝까지)
0,0
25,0
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
    IPNO: int = 0
    curvetype: str = ''
    structure: str = ''
    station: float = 0.0
    object_index: int = 0
    filename: str = ''
    object_path: str = ''
    speed: int = 0
    offset: tuple[float, float] = (0, 0)
    rotation: float = 0.0


def format_distance(number):
    return f"{number / 1000:.3f}"

def try_read_file(file_path, encodings=('utf-8', 'euc-kr')):
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                return list(csv.reader(file))
        except UnicodeDecodeError:
            print(f"[경고] {encoding} 인코딩 실패. 다음 인코딩으로 시도합니다.")
    print("[오류] 지원되는 인코딩으로 파일을 읽을 수 없습니다.")
    return []

def read_file():
    file_path = filedialog.askopenfilename(
        title="곡선 정보 파일 선택",
        initialfile="curve_info.txt",  # 사용자가 기본적으로 이 파일을 고르게 유도
        defaultextension=".txt",
        filetypes=[
            ("curve_info.txt (기본 권장)", "curve_info.txt"),
            ("모든 텍스트 파일", "*.txt"),
            ("모든 파일", "*.*")
        ]
    )

    if not file_path:
        print("[안내] 파일 선택이 취소되었습니다.")
        return []

    print("[선택된 파일]:", file_path)
    return file_path

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

#핵심로직(클래스화로 구조변경)
def annotate_sections(sections ,brokenchain):
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
            # STA 결정 직후
            BC_STA = section[0][0]
            EC_STA = section[-1][0]
            BC_STA += brokenchain
            EC_STA += brokenchain

            # IPdata 생성 (예시, 필요에 따라 STA값 할당 조정)
            ipdata = IPdata(
                IPNO=i,
                curvetype=curvetype,
                curve_direction=direction,
                radius=abs(selected_radius),
                cant=abs(selected_cant),
                BC_STA=BC_STA,
                EC_STA=EC_STA
            )
            ipdatas.append(ipdata)
            i += 1
        if curvetype == '완화곡선':
            SP_STA = section[0][0]
            PC_STA = pc_sta
            CP_STA = cp_sta
            PS_STA = section[-1][0]

            SP_STA += brokenchain
            PC_STA += brokenchain
            CP_STA += brokenchain
            PS_STA += brokenchain
            ipdata = IPdata(
                IPNO=i,
                curvetype=curvetype,
                curve_direction=direction,
                radius=abs(selected_radius),
                cant=abs(selected_cant),
                SP_STA=SP_STA,
                PC_STA=PC_STA,
                CP_STA=CP_STA,
                PS_STA=PS_STA
            )
            ipdatas.append(ipdata)
            i += 1

    return ipdatas
    
def copy_and_export_csv(open_filename='SP1700', output_filename='IP1SP',isSPPS = False, R= 3100, curvetype='SP', source_directory='', work_directory=''):
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
            if f'LoadTexture, {curvetype}.png,' in line:
                line = line.replace(f'LoadTexture, {curvetype}.png,', f'LoadTexture, {output_filename}.png,')
            if 'LoadTexture, R.png,'in line:
                line = line.replace('LoadTexture, R.png,', f'LoadTexture, {output_filename}_{R}.png,')
     
            # Append the modified line to the new_lines list
            new_lines.append(line)

    # Open the output file for writing the modified lines
    with open(output_file, 'w', encoding='utf-8') as file:
        # Write the modified lines to the output file
        file.writelines(new_lines)

    return output_file

def create_curve_post_txt(data_list: list[ObjectDATA], output_file):
    """
    결과 데이터를 받아 파일로 저장하는 함수.
    """
    with open(output_file, "w", encoding="utf-8") as file:
         for data in data_list:  # 두 리스트를 동시에 순회
            file.write(f"{data.station},.freeobj 0;{data.object_index};-{data.offset[0]};{data.offset[1]};{data.rotation};,;IP{data.IPNO}_{data.curvetype}-{data.structure}\n")  # 원하는 형식으로 저장

def create_curve_index_txt(data_list: list[ObjectDATA], output_file):
    """
    결과 데이터를 받아 파일로 저장하는 함수.
    """
    with open(output_file, "w", encoding="utf-8") as file:
         for data in data_list:  # 두 리스트를 동시에 순회
            file.write(f".freeobj({data.object_index}) {data.object_path}/{data.filename}.csv\n")  # 원하는 형식으로 저장


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


def find_curve_section(filepath):
    df = pd.read_excel(filepath,  header=4)

    ip_list = []
    current_ip = None
    ip_counter = 1

    for _, row in df.iterrows():
        point_type = row['구분'].strip() if pd.notna(row['구분']) else ''
        sta = row['측점'] if pd.notna(row['측점']) else 0.0
        direction = row['방향'] if pd.notna(row['방향']) else ''
        radius = row['반지름'] if pd.notna(row['반지름']) else 0.0

        if point_type == 'SP:':
            if current_ip:  # 이전 IP 저장
                ip_list.append(current_ip)
            current_ip = IPdata(IPNO=ip_counter)
            ip_counter += 1
            current_ip.SP_STA = sta
            current_ip.curve_direction = CurveDirection.LEFT if direction =='-' else CurveDirection.RIGHT
            current_ip.curvetype = '완화곡선'
        elif point_type == 'PC:':
            if current_ip:
                current_ip.PC_STA = sta
                current_ip.radius = radius

        elif point_type == 'CP:':
            if current_ip:
                current_ip.CP_STA = sta

        elif point_type == 'PS:':
            if current_ip:
                current_ip.PS_STA = sta
                ip_list.append(current_ip)
                current_ip = None

        elif point_type == 'BC:':
            if current_ip:
                ip_list.append(current_ip)
            current_ip = IPdata(IPNO=ip_counter)
            ip_counter += 1
            current_ip.BC_STA = sta
            current_ip.radius = radius
            current_ip.curve_direction = CurveDirection.LEFT if direction == '-' else CurveDirection.RIGHT
            current_ip.curvetype = '원곡선'
        elif point_type == 'EC:':
            if current_ip:
                current_ip.EC_STA = sta
                ip_list.append(current_ip)
                current_ip = None

    return ip_list

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
    root.attributes("-topmost", True)
    
    file_path = filedialog.askopenfilename(
        title="엑셀 파일 선택",
        filetypes=[("Excel Files", "*.xlsx")]
    )
    
    return file_path

#######이미지 생성 로직
def create_png_from_ai(type1 = 'SP', text1 = '14.626',text2 = '150', filename = 'output.png', source_directory='', work_directory=''):
    
    ai_file = source_directory + type1 + '.AI'
    
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

# DXF 파일을 생성하는 함수
def create_tunnel_curve_image(filename, text, work_directory):
    doc = ezdxf.new()  # 새로운 DXF 문서 생성
    msp = doc.modelspace()

    # 사각형의 크기 설정
    width = 240
    height = 200
    start_point = (0, 0)
    insert_x, insert_y = start_point[0], start_point[1]

    # 사각형의 4개 점 계산
    left_bottom = (insert_x, insert_y)
    right_bottom = (insert_x + width, insert_y)
    right_top = (insert_x + width, insert_y + height)
    left_top = (insert_x, insert_y + height)

    # 사각형을 그리기 위해 4개의 점을 이어서 폴리라인 추가
    msp.add_lwpolyline([left_bottom, right_bottom, right_top, left_top, left_bottom], close=True)

    # 해치 추가
    hatch = msp.add_hatch(color=5)
    hatch.paths.add_polyline_path([left_bottom, right_bottom, right_top, left_top], is_closed=True)

    # 텍스트 길이에 따른 위치 지정
    if len(text) == 3:
        width = 1.056
    elif len(text) == 4:
        width = 0.792
    elif len(text) == 5:
        width = 0.633
    else:
        width = 1
    text_x, text_y = 49.573, 65.152
    style_name = 'GHS'

    # 텍스트 스타일 생성
    try:
        doc.styles.add(style_name, font= 'H2GTRE.ttf')
    except:
        doc.styles.add(style_name, font='HYGTRE.ttf')

    # 텍스트 추가
    msp.add_text(text, dxfattribs={'insert': (text_x, text_y), 'height': 75, 'width': width, 'style': style_name})

    # 파일 확장자 확인
    if not filename.endswith('.dxf'):
        filename += '.dxf'

    # DXF 파일 저장
    final_dir = work_directory + filename
    doc.saveas(filename)
    
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

        except Exception as e:
            print(f"❌ 이미지 처리 실패: {e}")    
#######이미지 생성 로직 끝


def convert_curve_lines(lines):
    """
    .CURVE 제거 → ; 를 ,로 변환 → 마지막 , 제거
    lines가 List[List[str]] 혹은 List[str]인 경우 모두 처리 가능
    """
    converted = []

    for line in lines:
        # line이 리스트이면 문자열로 결합
        if isinstance(line, list):
            line = ','.join(line)

        line = line.strip()

        # 1단계: ".CURVE" 등 대소문자 구분 없이 제거 (정규식 사용)
        line = re.sub(r'\.curve', '', line, flags=re.IGNORECASE)

        # 2단계: ; → , 변환
        line = line.replace(';', ',')

        # 3단계: 마지막 글자가 ,이면 제거
        if line.endswith(','):
            line = line[:-1]

        #4단계: line의 각 요소 추출
        parts = line.split(',')
        if len(parts) == 1 or len(parts) == 0:
            print(f"[경고] 잘못된 행 형식: {line} → 건너뜀")
            continue  # 또는 raise ValueError(f"Invalid line format: {line}")
        try:
            if len(parts) == 2:
                sta, radius = map(float, parts)
                cant = 0.0
            elif len(parts) >= 3:
                sta, radius, cant = map(float, parts[:3])  # 3개 이상이면 앞 3개만 사용
            else:
                raise ValueError

            converted.append((sta, radius, cant))

        except ValueError:
            print(f"[오류] 숫자 변환 실패: {line} → 건너뜀")
            continue

    return converted



def is_civil3d_format(lines):
    try:
        return any('curve' in cell.lower() for line in lines for cell in line)
    except Exception as e:
        return False

def process_and_save_sections(lines , brokenchain):
    """곡선 정보를 처리하고 파일로 저장"""
    print("곡선 정보가 성공적으로 로드되었습니다.")

    # 중복 제거
    # Civil3D 형식 여부 판단
    civil3d = is_civil3d_format(lines)

    # Civil3D면 중복 반지름 제거
    unique_data = convert_curve_lines(lines) if civil3d else remove_duplicate_radius(lines)

    # 구간 정의 및 처리
    sections = process_sections(unique_data)
    ipdatas = annotate_sections(sections, brokenchain)

    return ipdatas

def process_dxf_image(img_f_name, structure, radius, source_directory, work_directory):
    """DXF 파일 수정 및 이미지 변환"""
    img_f_name_for_prev = str(int(radius))
    file_path = source_directory  + '곡선표.dxf'
    modifed_path = work_directory + '곡선표-수정됨.dxf'
    final_output_image = os.path.join(work_directory, img_f_name_for_prev + '.png')
    img_f_name_for_tunnel = f'{img_f_name}_{img_f_name_for_prev}'
    converter = DXF2IMG()
    
    if structure == '터널':
        create_tunnel_curve_image(modifed_path, img_f_name_for_prev, work_directory)
        target_size = (238,200)
    else:
        replace_text_in_dxf(file_path, modifed_path, img_f_name_for_prev)
        target_size = (500,300)
        
    final_output_image = os.path.join(work_directory, img_f_name_for_tunnel + '.png')
        
    output_paths = converter.convert_dxf2img([modifed_path], img_format='.png')

    if output_paths:
        converter.trim_and_resize_image(output_paths[0], final_output_image, target_size)


#도시철도용 곡선처리
def citylineprocess(curve_type: str, radius: float, cant: float, tcl: int,
                    img_f_name: str, source_directory: str, work_directory: str):
    def cal_slack(rad: float) -> float:
        slack = 2400 / rad
        return slack - 5 if slack >= 30 else slack

    def cal_speed(radius: float) -> float:
        return (radius * 160 / 11.8) ** 0.5

    def cal_cant(speed: float, radius: float, original_cant: float) -> float:
        if original_cant == 0:
            value = 11.8 * (speed ** 2) / radius
            return min(value, 160)
        return original_cant

    def modify_dxf(origin_file_path: str, new_file_path: str,
                   current_curve_type: str, current_radius: str,
                   current_cant: str, slack: str, tcl_value: int) -> bool:
        try:
            doc = ezdxf.readfile(origin_file_path)
            msp = doc.modelspace()
            layers = doc.layers

            if current_curve_type in ['BTC', 'BCC', 'ECC', 'ETC']:
                layers.get('제원문자-앞').on()
                layers.get('제원문자-중간').on()
                layers.get('제원문자-뒤').on()
            elif current_curve_type in ['BC', 'EC']:
                layers.get('제원문자-앞').on()
                layers.get('제원문자-뒤').on()

            for entity in msp.query("TEXT"):
                if current_curve_type in ['BTC', 'BCC', 'ECC', 'ETC']:
                    if entity.dxf.layer == "제원문자-앞":
                        entity.dxf.text = current_curve_type[0]
                    elif entity.dxf.layer == "제원문자-중간":
                        entity.dxf.text = current_curve_type[1]
                    elif entity.dxf.layer == "제원문자-뒤":
                        entity.dxf.text = current_curve_type[2]
                elif current_curve_type in ['BC', 'EC']:
                    if entity.dxf.layer == "제원문자-앞":
                        entity.dxf.text = current_curve_type[0]
                    elif entity.dxf.layer == "제원문자-뒤":
                        entity.dxf.text = current_curve_type[1]

                if current_curve_type in ['BCC', 'BC', 'EC', 'ECC']:
                    layers.get('R').on()
                    layers.get('C').on()
                    layers.get('S').on()

                    if entity.dxf.layer == "R":
                        entity.dxf.text = current_radius
                    elif entity.dxf.layer == "C":
                        entity.dxf.text = current_cant
                    elif entity.dxf.layer == "S":
                        entity.dxf.text = slack
                elif current_curve_type in ['BTC', 'ETC']:
                    layers.get('TCL').on()
                    if entity.dxf.layer == "TCL":
                        entity.dxf.text = str(tcl_value)

            doc.saveas(new_file_path)

            return True

        except Exception as e:
            print(f"❌ DXF 텍스트 교체 실패: {e}")
            return False

    def process_speed_limit_post(speedfile_path: str, modified_speedfile_path: str,
                                 radius: float, speed_value: int) -> bool:
        try:
            doc = ezdxf.readfile(speedfile_path)
            msp = doc.modelspace()

            for entity in msp.query("TEXT"):
                if entity.dxf.layer == "V":
                    entity.dxf.text = str(speed_value)
                if entity.dxf.layer == "R":
                    entity.dxf.text = str(int(radius))

            doc.saveas(modified_speedfile_path)

            return True

        except Exception as e:
            print(f"❌ 속도 제한 DXF 텍스트 교체 실패: {e}")
            return False

    curve_map = {
        'SP': 'BTC', 'PC': 'BCC', 'CP': 'ECC', 'PS': 'ETC',
        'BC': 'BC', 'EC': 'EC'
    }
    new_curve_type = curve_map.get(curve_type, curve_type)

    speed = cal_speed(radius)
    cant_val = cal_cant(speed, radius, cant)

    r_text = f'R={int(radius)}'
    c_text = f'C={int(cant_val)}'
    s_text = f'S={int(cal_slack(radius))}'

    file_path = os.path.join(source_directory, '곡선표.dxf')
    modified_path = os.path.join(work_directory, '곡선표-수정됨.dxf')
    speedfile_path = os.path.join(source_directory, '속도제한표.dxf')
    modified_speedfile_path = os.path.join(work_directory, '속도제한표-수정됨.dxf')

    img_f_name_for_speed = f'{img_f_name}_{int(radius)}'
    final_output_image = os.path.join(work_directory, img_f_name + '.png')
    speedlimit_image = os.path.join(work_directory, img_f_name_for_speed + '.png')

    converter = DXF2IMG()

    if modify_dxf(file_path, modified_path, new_curve_type, r_text, c_text, s_text, tcl):
        output_paths = converter.convert_dxf2img([modified_path], img_format='.png')
        if output_paths:
            converter.trim_and_resize_image(output_paths[0], final_output_image, (300, 210))

    if new_curve_type in ['BC', 'BCC']:
        if speed < 120:
            if process_speed_limit_post(speedfile_path, modified_speedfile_path, radius, int(speed)):
                output_paths = converter.convert_dxf2img([modified_speedfile_path], img_format='.png')
                if output_paths:
                    converter.trim_and_resize_image(output_paths[0], speedlimit_image, (200, 200))


def insert_speedlimt_syntax(open_filename: str, struecture: str, source_directory: str, work_directory: str):
    # 기존 파일의 최하단에 source_file의 모든 내용을 붙여넣기

    source_file = source_directory + f'속도제한표-{struecture}용.csv'

    # 기존 파일 내용 읽기
    with open(open_filename, 'r', encoding='utf-8') as f:
        original_lines = f.readlines()

    # 추가할 내용 읽기
    with open(source_file, 'r', encoding='utf-8') as f:
        add_lines = f.readlines()

    # 합쳐서 output_file에 쓰기
    with open(open_filename, 'w', encoding='utf-8') as f:
        f.writelines(original_lines)
        f.writelines(add_lines)

    print(f"✅ '{open_filename}.csv' 파일에 속도제한표 내용 추가 완료")


def modify_r_text_in_file(file_path, output_filename, R: str):
    new_lines = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if 'LoadTexture, R.png,' in line:
                line = line.replace('LoadTexture, R.png,', f'LoadTexture, {output_filename}_{R}.png,')
            new_lines.append(line)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

def cal_speed(radius: float) -> float:
    return (radius * 160 / 11.8) ** 0.5

#핵심 로직2 (클래스화 구조변경)
def process_sections_for_images(start, end, ipdatas: list[IPdata], structure_list ,source_directory, work_directory, target_directory, altype: str, offset):
    """주어진 구간 정보를 처리하여 이미지 및 CSV 생성"""

    object_path = ''
    object_index = 2025
    line = []
    objects = []
    isSPPS = None
    object_folder = target_directory.split("Object/")[-1]

    for i, ip in enumerate(ipdatas):
        if not start <= ip.SP_STA <= end or start <= ip.BC_STA <= end:
            print(f"범위를 벗어났습니다. 해당 구간은 건너뜁니다.")
            continue
        lines = get_curve_lines(ip)

        if not lines:
            continue

        for key, value in lines:
            # 구조물 정보 확인
            isSPPS = True if key in ['SP','PS', 'BC', 'EC'] else False
            tcl = 'TCL=' + str(int(ip.PC_STA - ip.SP_STA)) if ip.curvetype == '완화곡선' else 0
            speed = int(cal_speed(ip.radius))
            structure = isbridge_tunnel(value, structure_list) # 구조물(토공,교량,터널)
            img_text = format_distance(value) # 측점문자 포맷
            img_f_name = f'IP{i + 1}_{key}' # i는 0부터임으로 1+
            openfile_name = f'{key}_{structure}용' #소스폴더에서 열 파일명.csv원본
            if altype == '도시철도':
                citylineprocess(key, ip.radius, ip.cant, tcl, img_f_name, source_directory, work_directory)

                output_file = copy_and_export_csv(openfile_name, img_f_name, isSPPS, int(ip.radius), key, source_directory,
                                    work_directory)  # csv 원본복사 후 추출함수
                if speed < 120 and key in ['BC', 'PC']:
                    insert_speedlimt_syntax(output_file, structure, source_directory, work_directory) #속도제한표 추가
                    modify_r_text_in_file(output_file, img_f_name, str(int(ip.radius)))
            else:
                create_png_from_ai(key, img_text, str(ip.cant), img_f_name, source_directory, work_directory) #이미지 생성 함수

                if isSPPS:
                    process_dxf_image(img_f_name, structure, ip.radius, source_directory, work_directory)
                output_file = copy_and_export_csv(openfile_name, img_f_name, isSPPS, int(ip.radius), key, source_directory, work_directory) # csv 원본복사 후 추출함수
            #print(object_path)
            #print(f'{img_f_name}-{openfile_name}-{key}:{img_text}-{objec_index}')
            #클래스에ㅐ 속성 추가
            objects.append(ObjectDATA(
                IPNO=ipdatas[i].IPNO,
                curvetype=key,
                structure=structure,
                station=value,
                object_index=object_index,
                filename=img_f_name,
                object_path=object_folder,
                speed=speed,
                offset=(offset[structure][0], offset[structure][1]),
                rotation=0
                )
            )
            object_index += 1
    return objects

#1. 곡선 구간(Line) 생성 분리
def get_curve_lines(ip: IPdata) -> list[list]:
    if ip.curvetype == '원곡선':
        return [['BC', ip.BC_STA], ['EC', ip.EC_STA]]
    elif ip.curvetype == '완화곡선':
        return [['SP', ip.SP_STA], ['PC', ip.PC_STA], ['CP', ip.CP_STA], ['PS', ip.PS_STA]]
    return []

#2. ObjectDATA 생성 분리
def create_objectdata(ip: IPdata, ip_index: int, key: str, value: float, structure: str, object_index: int, folder_name: str) -> ObjectDATA:
    filename = f'IP{ip_index + 1}_{key}'
    return ObjectDATA(
        IPNO=ip.IPNO,
        curvetype=key,
        structure=structure,
        station=value,
        object_index=object_index,
        filename=filename
    )
#3. object_path 생성 (인덱스 파일 한 줄) 분리
def create_object_path(object_index: int, folder_name: str, filename: str) -> str:
    return f".freeobj({object_index}) {folder_name}{filename}.CSV\n"


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


def process_curve_data(start, end, source_directory, work_directory, target_directory, data, structure_list, brokenchain, altype: str, flag: str, offset):
    """곡선 데이터 처리 (파일 저장 및 이미지 & CSV 생성)"""
    if not data:
        print("curve_info가 비어 있습니다.")
        return None, None
    if flag == 'BVE':
        # 중복 제거 및 섹션 처리
        ipdatas = process_and_save_sections(data, brokenchain)
    else:
        ipdatas = data
    # 이미지 및 CSV 생성
    objectdatas = process_sections_for_images(start, end, ipdatas, structure_list, source_directory, work_directory, target_directory, altype, offset)

    return objectdatas

def copy_all_files(source_directory, target_directory, include_extensions=None, exclude_extensions=None,
                   is_delete_original=True):
    """
    원본 폴더의 모든 파일을 대상 폴더로 복사 (대상 폴더의 모든 데이터 제거)

    :param source_directory: 원본 폴더 경로
    :param target_directory: 대상 폴더 경로
    :param include_extensions: 복사할 확장자의 리스트 (예: ['.txt', '.csv'] → 이 확장자만 복사)
    :param exclude_extensions: 제외할 확장자의 리스트 (예: ['.log', '.tmp'] → 이 확장자는 복사 안 함)
    :param is_delete_original: 원본 삭제유무
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
    if is_delete_original:
        shutil.rmtree(source_directory)

    print(f"📂 모든 파일이 {source_directory} → {target_directory} 로 복사되었습니다.")

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

def create_speed_limit(datalist: list[ObjectDATA], work_directory: str):
    """
        결과 데이터를 받아 파일로 저장하는 함수.
        """
    output_file = work_directory + "speed_limit.txt"  # 저장할 파일 이름

    with open(output_file, "w", encoding="utf-8") as file:
        for data in datalist:  # 두 리스트를 동시에 순회
            file.write(f',;IPNO {data.IPNO}\n')
            if data.curvetype in ['BC', 'SP']:
                file.write(f"{data.station},.LIMIT {data.speed};\n")  # 원하는 형식으로 저장
            elif data.curvetype in ['EC', 'PS']:
                file.write(f"{data.station},.LIMIT 0;\n")  # 원하는 형식으로 저장

#메인 gui클래스
class CurveProcessingApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.offset = 0.0
        self.alignment_type = ''
        self.base_source_directory = 'c:/temp/curve/소스/'
        self.log_box = None
        self.title("곡선 데이터 처리기")
        self.geometry("650x450")

        self.source_directory = self.base_source_directory #원본 소스 위치
        self.work_directory = '' #작업물이 저장될 위치
        self.target_directory = ''
        self.isbrokenchain: bool = False
        self.brokenchain: float = 0.0
        self.create_widgets()

    def create_widgets(self):
        label = ttk.Label(self, text="곡선 데이터 자동 처리 시스템", font=("Arial", 16, "bold"))
        label.pack(pady=10)
        input_frame = ttk.Frame(self.master)
        input_frame.pack(pady=10)
        # 🔹 시작 측점 입력
        ttk.Label(input_frame, text="시작 측점").grid(row=0, column=0, sticky="e", padx=5)

        self.start_station_var = tk.DoubleVar(value=33300)
        ttk.Entry(
            input_frame,
            textvariable=self.start_station_var,
            width=15
        ).grid(row=0, column=1, padx=5)
        # 🔹 끝 측점 입력
        ttk.Label(input_frame, text="끝 측점").grid(row=0, column=2, sticky="e", padx=5)

        self.end_station_var = tk.DoubleVar(value=95000)
        ttk.Entry(
            input_frame,
            textvariable=self.end_station_var,
            width=15
        ).grid(row=0, column=3, padx=5)

        # 🔹 파정 입력
        ttk.Label(input_frame, text="파정").grid(row=0, column=4, sticky="e", padx=5)

        self.brokenchain_var = tk.DoubleVar(value=0.0)
        ttk.Entry(
            input_frame,
            textvariable=self.brokenchain_var,
            width=15
        ).grid(row=0, column=5, padx=5)

        # 🔹 오프셋 입력
        offset_frame = ttk.LabelFrame(self, text="구조물별 offset 설정")
        offset_frame.pack(pady=10)

        ttk.Label(offset_frame, text="토공").grid(row=0, column=0, sticky="e", padx=5)
        self.e_xoffset_var = tk.DoubleVar(value=3.3)
        ttk.Entry(offset_frame, textvariable=self.e_xoffset_var, width=15).grid(row=0, column=1, padx=5)
        self.e_yoffset_var = tk.DoubleVar(value=0.0)
        ttk.Entry(offset_frame, textvariable=self.e_yoffset_var, width=15).grid(row=0, column=2, padx=5)

        ttk.Label(offset_frame, text="교량").grid(row=1, column=0, sticky="e", padx=5)
        self.b_xoffset_var = tk.DoubleVar(value=3)
        ttk.Entry(offset_frame, textvariable=self.b_xoffset_var, width=15).grid(row=1, column=1, padx=5)
        self.b_yoffset_var = tk.DoubleVar(value=0.0)
        ttk.Entry(offset_frame, textvariable=self.b_yoffset_var, width=15).grid(row=1, column=2, padx=5)

        ttk.Label(offset_frame, text="터널").grid(row=2, column=0, sticky="e", padx=5)
        self.t_xoffset_var = tk.DoubleVar(value=4.546)
        ttk.Entry(offset_frame, textvariable=self.t_xoffset_var, width=15).grid(row=2, column=1, padx=5)
        self.t_yoffset_var = tk.DoubleVar(value=0.0)
        ttk.Entry(offset_frame, textvariable=self.t_yoffset_var, width=15).grid(row=2, column=2, padx=5)

        log_frame = ttk.Frame(self)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.log_box = tk.Text(log_frame, height=20, wrap=tk.WORD, font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=scrollbar.set)

        self.log_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        run_button = ttk.Button(button_frame, text="실행", command=self.run_main)
        run_button.pack(pady=10)
        exit_button = ttk.Button(button_frame, text="종료", command=self.destroy)
        exit_button.pack(pady=10)

    def log(self, message):
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)
        self.log_box.update_idletasks()  # UI 즉시 갱신

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

    def run_main(self):
        try:
            # 디렉토리 설정
            self.log("작업 디렉토리 확인 중...")
            self.work_directory = 'c:/temp/curve/result/'
            if not os.path.exists(self.work_directory):
                os.makedirs(self.work_directory)
                self.log(f"디렉토리 생성: {self.work_directory}")
            else:
                self.log(f"디렉토리 존재: {self.work_directory}")

            # 대상 디렉토리 선택
            self.log("대상 디렉토리 선택 중...")
            self.target_directory = select_target_directory()
            self.log(f"대상 디렉토리: {self.target_directory}")

            # 노선 종류 입력받기
            self.process_interval()
            # ✅ 항상 base_source_directory에서 새로 경로 만들기
            self.source_directory = os.path.join(self.base_source_directory, self.alignment_type) + '/'
            self.log(f"소스 경로: {self.source_directory}")
            # 소스폴더의 모든 내용을 작업폴더에 복사
            copy_all_files(self.source_directory, self.work_directory, ['.bmp', '.png', '.jpg', '.jpeg'],
                           ['.dxf', '.ai', '.csv'], is_delete_original=False)
            # ㅊ파정확인
            self.brokenchain = self.brokenchain_var.get()
            if self.brokenchain != 0.0:
                self.isbrokenchain = True
            else:
                self.isbrokenchain = False

            # 오프셋 적용
            self.offset = {
                '토공': (self.e_xoffset_var.get(), self.e_yoffset_var.get()),
                "교량": (self.b_xoffset_var.get(), self.b_yoffset_var.get()),
                "터널": (self.t_xoffset_var.get(), self.t_yoffset_var.get())
            }

            # 시작 끝 측점 확인
            start_sta = self.start_station_var.get()
            end_sta = self.end_station_var.get()
            if start_sta >= end_sta:
                self.log("⚠️ 시작 측점은 끝 측점보다 작아야 합니다.")
                return
            # 곡선 정보 파일 읽기
            self.log("곡선 정보 파일 읽는 중...")
            data = None
            try:
                file_path = read_file()
                ext = os.path.splitext(file_path)[1].lower()
                if ext == ".txt":
                    data = try_read_file(file_path) #TXT 읽기 시도
                    self.log('bve txt타입 감지됨')
                    flag = 'BVE'
                elif ext == ".xlsx":
                    data =  find_curve_section(file_path) #xlsx읽기 시도
                    self.log('civil3d xlsx 타입 감지됨')
                    flag = 'CIVIL3D'
                else:
                    self.log(f"지원하지 않는 형식: {ext}")
                    return
            except Exception as e:
                self.log('파일처리 예외발생 {e}')
                flag = None
                return
            # 구조물 데이터 로드
            self.log("구조물 데이터 로드 중...")
            structure_list = load_structure_data()
            #구조물 측점 파정처리
            structure_list = apply_brokenchain_to_structure(structure_list, self.brokenchain)
            # 곡선 데이터 처리
            self.log("곡선 데이터 처리 중...")
            objectdatas = process_curve_data(start_sta, end_sta, self.source_directory, self.work_directory, self.target_directory, data, structure_list, self.brokenchain, self.alignment_type, flag, self.offset)

            # 최종 텍스트 생성
            if objectdatas:
                self.log("최종 결과 생성 중...")
                post_file = os.path.join(self.work_directory, 'curve_post.txt')
                index_file = os.path.join(self.work_directory, 'curve_index.txt')
                create_curve_post_txt(objectdatas, post_file)
                create_curve_index_txt(objectdatas, index_file)
                create_speed_limit(objectdatas, self.work_directory)
                self.log("결과 파일 생성 완료!")

            # 파일 복사
            self.log("결과 파일 복사 중...")
            copy_all_files(self.work_directory, self.target_directory, ['.csv', '.png', '.txt'], ['.dxf', '.ai'])

            self.log("✅ 모든 작업이 성공적으로 완료되었습니다.")
            messagebox.showinfo("완료", "곡선 데이터 처리 완료!")

        except Exception as e:
            self.log(f"[오류] {str(e)}")
            messagebox.showerror("오류", f"실행 중 오류 발생:\n{e}")

if __name__ == "__main__":
    app = CurveProcessingApp()
    app.mainloop()

