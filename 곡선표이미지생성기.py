import csv
from tkinter import filedialog
import tkinter as tk
from PIL import Image, ImageDraw, ImageFont
import os
import pandas as pd
import math
import re
import textwrap


'''
BVE곡선파일을 바탕으로 곡선표(준고속용)을 설치하는 프로그램
-made by dger -


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
# 기본 작업 디렉토리
default_directory = 'c:/temp/object/'
work_directory = None
# 사용자가 설정한 작업 디렉토리가 없으면 기본값 사용
if not work_directory:
    work_directory = default_directory

# 디렉토리가 존재하지 않으면 생성
if not os.path.exists(work_directory):
    os.makedirs(work_directory)

print(f"작업 디렉토리: {work_directory}")
    
def format_distance(number, decimal_places=2):
    negative = False
    if number < 0:
        negative = True
        number = abs(number)
        
    km = int(number) // 1000
    remainder = round(number % 1000, decimal_places)  # Round remainder to the specified decimal places
    
    # Format the remainder to have at least 'decimal_places' digits after the decimal point
    formatted_distance = "{:d}km{:0{}.{}f}".format(km, remainder, 4 + decimal_places, decimal_places)
    
    if negative:
        formatted_distance = "-" + formatted_distance
    
    return formatted_distance

def read_file():
    file_path = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("txt files", "*.txt"), ("All files", "*.*")])
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
            station, radius = map(float, row)
            station = int(station)
        except ValueError:
            print(f"잘못된 데이터 형식: {row}")
            continue

        if radius != previous_radius:
            filtered_data.append((station, radius))
            previous_radius = radius

    return filtered_data

def process_sections(data):
    sections = []
    current_section = []

    for row in data:
        try:
            station, radius = map(float, row)
            station = int(station)
        except ValueError:
            print(f"잘못된 데이터 형식: {row}")
            continue

        current_section.append((station, radius))

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

        for i, (station, radius) in enumerate(section):
            annotation = ""

            # 첫 번째 줄에 SP 추가
            if i == 0:
                annotation += ";SP"
            
            # 마지막 줄에 PS 추가
            if i == n - 1:
                annotation += ";PS"

            # STA 간 차이가 25보다 큰 경우 PC/CP 추가
            if i < n - 1:  # Ensure we're not at the last row
                prev_station, prev_radius = section[i - 1] if i > 0 else (None, None)
                next_station, next_radius = section[i + 1]
                
                if next_station - station > 75:
                    annotation += ";PC"
                elif i > 0 and station - prev_station > 75:
                    annotation += ";CP"

            annotated_section.append(f"{station},{radius}{annotation}")

        # SP와 PS만 있는 구간을 BC와 EC로 변경
        if len(annotated_section) == 2 and ";SP" in annotated_section[0] and ";PS" in annotated_section[1]:
            annotated_section[0] = annotated_section[0].replace(";SP", ";BC")
            annotated_section[1] = annotated_section[1].replace(";PS", ";EC")

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

    for line in file_content:  # file_content는 csv.reader가 반환한 리스트 형태
        # 리스트 형태의 line을 문자열로 변환
        line = ",".join(line)
        
        if line.startswith("구간"):
            current_section = int(line.split()[1][:-1])
            sections[current_section] = []
        elif current_section is not None and line.strip():
            sta, rest = line.split(',', 1)
            sta = int(sta)
            radius_tag = rest.split(';')
            radius = float(radius_tag[0])
            tags = radius_tag[1:] if len(radius_tag) > 1 else []
            sections[current_section].append((sta, radius, tags))

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
        for i, (start_sta, _, tags) in enumerate(points):
            if sta == start_sta:  # STA가 정확히 일치하는 경우
                for tag in tags:
                    key = f"IP{section_id}_{tag}"
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
    file_path = filedialog.askopenfilename(
        title="엑셀 파일 선택",
        filetypes=[("Excel Files", "*.xlsx")]
    )
    
    return file_path

#함수 종료
#MAIN 시작

# 파일 읽기
data = read_file()

# 구조물 정보 파일 경로 지정
openexcelfile = open_excel_file()
# 선택된 파일로 구조물 정보 가져오기
if openexcelfile:
    structure_list = find_structure_section(openexcelfile)
    print("구조물 정보가 성공적으로 로드되었습니다.")
else:
    print("엑셀 파일을 선택하지 않았습니다.")
    
if not data:
    print("데이터가 비어 있습니다.")
else:
    # 중복 제거
    unique_data = remove_duplicate_radius(data)
    
    # 구간 정의 및 처리
    sections = process_sections(unique_data)
    annotated_sections = annotate_sections(sections)

    # 결과 파일 저장
    output_file = work_directory + '주석처리된파일.txt'
    unique_file = work_directory + '1532326.txt'
    
    if not output_file:
        print("출력 파일을 선택하지 않았습니다.")
    else:
        with open(unique_file, 'w', encoding='utf-8') as file:
            for station, radius in unique_data:
                file.write(f"{station},{radius}\n")

        output_file = output_file
        with open(output_file, 'w', encoding='utf-8') as file:
            for i, section in enumerate(annotated_sections, start=1):
                file.write(f"구간 {i}:\n")
                for line in section:
                    file.write(f"{line}\n")
                file.write("\n")

        print(f"주석이 추가된 결과가 {output_file}에 저장되었습니다.")

    #이미지 저장
    PC_R_LIST = []
    last_PC_radius = None  # 마지막 PC 반지름을 추적
    objec_index_name = ''
    image_names = []
    isSPPS = False
    text_color = (255,255,255)
    structure_comment = []
    
    for i, section in enumerate(annotated_sections, start=1):
        # 1구간에 SP와 PS만 있는 경우를 확인
        if len(section) == 2 and 'SP' in section[0] and 'PS' in section[1]:
            section[0] = section[0].replace(";SP", ";BC")  # SP를 BC로 변경
            section[1] = section[1].replace(";PS", ";EC")  # PS를 EC로 변경
       
        for line in section:
            #IP별 곡선반경 추출
            if 'PC' in line:
            
                match = re.search(r",(-?[\d.]+);", line)

                if match:
                    extracted_number = int(float(match.group(1)))  # float → int 변환
                    PC_R_LIST.append((i, extracted_number))  # 올바르게 리스트에 추가
          
        for line in section:        
            #곡선형식별 처리
            if 'BC' in line or 'EC' in line or 'SP' in line or 'PC' in line or 'CP' in line or 'PS' in line:
                
                parts = line.split(',')
                sta = int(parts[0])
                parts2 =  parts[1].split(';')
                
                # 반경 찾기 (PC_R_LIST에서 현재 구간(i)과 일치하는 반경을 찾음)
                radius = next((r for sec, r in PC_R_LIST if sec == i), None)
                if radius is None:
                    radius = 0  # 기본값 (에러 방지)
                    
                structure = isbridge_tunnel(sta, structure_list)
                
                if radius < 0:
                    radius *= -1
                sec = parts2[1] if len(parts2) > 1 else None

                
                if 'SP' in line:
                    img_text = f'SP= {format_distance(sta, decimal_places=2)}'
                    img_bg_color = (34, 139, 34)
                    img_f_name = f'IP{i}_SP'
                    openfile_name = 'SP_' + structure + '용'
                    isSPPS = True
                    curvetype = 'SP'
                    
                elif 'PC' in line:
                    img_text = f'PC= {format_distance(sta, decimal_places=2)}\nR={radius}\nC=60'
                    img_bg_color = (255, 0, 0)
                    img_f_name = f'IP{i}_PC'
                    openfile_name = 'PC_' + structure + '용'
                    curvetype = 'PC'
                    
                elif 'CP' in line:

                    img_text = f'CP= {format_distance(sta, decimal_places=2)}\nR={radius}\nC=60'
                    img_bg_color = (255, 0, 0)
                    img_f_name = f'IP{i}_CP'
                    openfile_name = 'CP_' + structure + '용'
                    curvetype = 'CP'
                    
                elif 'PS' in line:
                    img_text = f'PS= {format_distance(sta, decimal_places=2)}'
                    img_bg_color = (34, 139, 34)
                    img_f_name = f'IP{i}_PS'
                    openfile_name = 'PS_' + structure + '용'
                    isSPPS = True
                    curvetype = 'PS'
                    
                elif 'BC' in line:
                    img_text = f'BC= {format_distance(sta, decimal_places=2)}'
                    img_bg_color = (255, 0, 0)
                    img_f_name = f'IP{i}_BC'
                    openfile_name = 'BC_' + structure + '용'
                    curvetype = 'BC'
                    
                elif 'EC' in line:
                    img_text = f'EC= {format_distance(sta, decimal_places=2)}'
                    img_bg_color = (255, 0, 0)
                    img_f_name = f'IP{i}_EC'
                    openfile_name = 'EC_' + structure + '용'
                    curvetype = 'EC'
                else:
                    print('에러')
                    img_text = 'XXXX'
                    img_bg_color = (0, 0, 0)
                    img_f_name = 'X'
                    curvetype = 'ERROR'
            
                create_text_image(img_text, img_bg_color, img_f_name, text_color, image_size=(300, 200), font_size=40)
                copy_and_export_csv(openfile_name, img_f_name,isSPPS,radius,curvetype)
                image_names.append(img_f_name)
                structure_comment.append(img_f_name + '-' + structure)
                
                if isSPPS and radius !=0:
                    #기존곡선표
                    img_bg_color_for_prev = (0,0,255)
                    img_f_name_for_prev = str(int(radius))

                    create_text_image(img_f_name_for_prev, img_bg_color_for_prev, img_f_name_for_prev, text_color, image_size=(500, 300), font_size=240)

        
        # 객체 인덱스 생성
        objec_index_name = ""
        objec_index_counter = 2025
        for img_name, stru in zip(image_names, structure_comment):
            objec_index_name += f".freeobj({objec_index_counter}) abcdefg/{img_name}.CSV\n"
            objec_index_counter += 1  # 카운터 증가

        
        
    create_object_index(objec_index_name)

# 데이터 파싱
with open(output_file, 'r', encoding='utf-8') as file:
            reader1 = csv.reader(file)
            lines1 = list(reader1)
            
OBJ_DATA = work_directory + 'object_index.txt'

with open(OBJ_DATA, 'r', encoding='utf-8') as file:
            reader2 = csv.reader(file)
            lines2 = list(reader2)
            
sections = parse_sections(lines1)

tag_mapping = parse_object_index(lines2)

# STA 값 검색
result_list =[]

for section_id, entries in sections.items():  # 모든 구간을 순회
    for sta_value, radius, tags in entries:  # 각 구간의 엔트리를 순회

        result = find_object_index(sta_value, sections, tag_mapping)

        '''
        # 결과 출력
        if result:
            print(f"STA {sta_value}에 대한 오브젝트 인덱스: {result}")
        else:
            print(f"STA {sta_value}에 대한 오브젝트 인덱스를 찾을 수 없습니다.")
        '''

        if not result == None:
            result_data = f'{sta_value},.freeobj 0;{result};\n'
            result_list.append(result_data)
        
#csv작성
create_curve_post_txt(result_list, structure_comment)

# 파일 삭제
os.remove(unique_file)
os.remove(output_file)
