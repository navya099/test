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
BVE구배파일을 바탕으로 기울기표(준고속용)을 설치하는 프로그램
-made by dger -


입력파일:BVE에서 추출한 구배파일(pitch_info.TXT)

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
# 기본 작업 디렉토리
default_directory = 'c:/temp/pitch/'
work_directory = None
# 사용자가 설정한 작업 디렉토리가 없으면 기본값 사용
if not work_directory:
    work_directory = default_directory

# 디렉토리가 존재하지 않으면 생성
if not os.path.exists(work_directory):
    os.makedirs(work_directory)

print(f"작업 디렉토리: {work_directory}")
    
def format_distance(number):
    number *= 0.001
    
    return "{:.3f}".format(number)

def read_file():
    root = tk.Tk()
    root.withdraw()  # Tkinter 창을 숨김
    file_path = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("txt files", "pitch_info.txt"), ("All files", "*.*")])
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
    previous_pitch = None

    for row in data:
        try:
            station, pitch = map(float, row)
            station = int(station)
        except ValueError:
            print(f"잘못된 데이터 형식: {row}")
            continue

        if pitch != previous_pitch:
            filtered_data.append((station, pitch))
            previous_pitch = pitch

    return filtered_data

def process_sections(data):
    sections = []  # 전체 섹션 리스트
    current_section = []  # 현재 섹션 리스트
    prev_station = None  # 이전 station 값을 저장할 변수

    for row in data:
        try:
            station, pitch = map(float, row)
            station = int(station)
        except ValueError:
            print(f"잘못된 데이터 형식: {row}")
            continue

        # 첫 번째 데이터이거나 station 차이가 75 이상이면 새로운 섹션 시작
        if prev_station is not None and (station - prev_station) >= 75:
            sections.append(current_section)  # 이전 섹션 저장
            current_section = []  # 새로운 섹션 초기화

        current_section.append((station, pitch))
        prev_station = station  # 현재 station을 prev_station으로 업데이트

    # 마지막 섹션 추가 (비어 있지 않을 경우)
    if current_section:
        sections.append(current_section)

    return sections

def is_multiple_of_25(number):
    return number % 25 == 0

def annotate_sections(sections):
    annotated_sections = []
    
    for section in sections:
        if not section:
            continue

        annotated_section = []
        n = len(section)

        # BVC, EVC 위치 계산
        BVC_station = section[0][0]
        EVC_station = section[-1][0]
        VCL = EVC_station - BVC_station
        
        # VIP 위치 계산 (BVC + 절반 거리)
        VIP_station = int(BVC_station + VCL / 2) if VCL != 0 else None
        if VIP_station is not None:
            is_multifle_25 = is_multiple_of_25(VIP_station)
        
        for i, (station, pitch) in enumerate(section):
            annotation = ""

            # 첫 번째 줄에 BVC 추가
            if i == 0:
                annotation += ";BVC"
            
            # 마지막 줄에 EVC 추가
            if i == n - 1:
                annotation += ";EVC"

            # VIP 위치가 존재하고 현재 station과 일치하면 VIP 추가
            if VIP_station is not None and station == VIP_station:
                annotation += ";VIP"

            annotated_section.append(f'{station},{pitch}{annotation}')

        # 현재 리스트에서 VIP_station이 존재하는지 정확히 확인
        existing_stations = {int(line.split(',')[0]) for line in annotated_section}

        # VIP가 존재하지 않으면 추가
        if VIP_station is not None and VIP_station not in existing_stations:
            annotated_section.append(f'{VIP_station},0;VIP')

        # 리스트 정렬
        annotated_section.sort(key=lambda x: float(x.split(',')[0]))
                               
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

#기울기표용
def create_text_image3(text, text2 , bg_color, filename, text_color, image_size=(500, 300), font_size=40):
    # 이미지 생성
    img = Image.new('RGB', image_size, color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # 폰트 설정
    font = ImageFont.truetype("gulim.ttc", 150)
    # 폰트 설정
    font2 = ImageFont.truetype("gulim.ttc", 60)
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

    
    #구배문자
    draw.text((20, 0), text, font=font, fill=text_color , rotate= 25)

    #구간거리

    draw.text((20, 250), f'{text2}M', font=font2, fill=text_color)
    
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
                    key = f"VIP{section_id}_{tag}"
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
    # 대화 상자가 항상 최상위로 표시되도록 설정
    root.attributes("-topmost", True)
    
    file_path = filedialog.askopenfilename(
        title="엑셀 파일 선택",
        filetypes=[("Excel Files", "*.xlsx")]
    )
    
    return file_path

def get_vertical_curve_type(start_grade, end_grade):
    if start_grade > end_grade:
        return "볼록형"  # 볼록형 (정상 곡선)
    else:
        return "오목형"  # 오목형 (골짜기 곡선)


def round_to_nearest_25(value):
    """주어진 값을 12.5 기준으로 25의 배수로 반올림"""
    return round(value / 25) * 25

def calculate_vertical_curve_radius(length, start_grade, end_grade):
    """
    종곡선 반지름을 계산하는 함수
    :param length: 종곡선 길이 (L)
    :param start_grade: 시작 구배 (‰ 단위, 예: -25.0 → -25‰)
    :param end_grade: 끝 구배 (‰ 단위)
    :return: 반지름 (R)
    """
    delta_g = end_grade - start_grade  # 구배 변화량

    if delta_g == 0:  
        return 0  # 구배 변화가 없으면 반지름은 무한대 (직선 구간)
    
    radius = length / delta_g
    return abs(radius) * 1000  # 반지름은 항상 양수

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
    GRADE_LIST = []
    VIP_STA_LIST = []
    L_LIST = []
    VCL_LIST = []
    
    last_PC_radius = None  # 마지막 PC 반지름을 추적
    objec_index_name = ''
    image_names = []
    isSPPS = False
    text_color = (0,0,0)
    structure_comment = []
    
    for i, section in enumerate(annotated_sections, start=1):
        for line in section:
            #VIP별 기울기 추출
            if 'BVC' in line:
                match = re.search(r'(\d+),', line)
                if match:
                    BVC_STA = int(match.group(1)) # int변환

                    #print(f'BCE:{BVC_STA}')
                    
            if 'EVC' in line:
            
                match = re.search(r",(-?[\d.]+);", line)

                if match:
                    extracted_number = float(match.group(1)) * 1000  # float변환 후 1000 배율
                    GRADE_LIST.append((i, extracted_number))  # 올바르게 리스트에 추가

                match2 = re.search(r'(\d+),', line)
                if match2:
                    EVC_STA = int(match2.group(1)) # int변환
                    #print(f'EVC:{EVC_STA}')
                    
            #VCL 계산
            if BVC_STA or EVC_STA:
                VCL = EVC_STA - BVC_STA
                if VCL >= 0:
                    VCL_LIST.append((i, VCL))
                    #print(f'VCL = {VCL}')
                    
            #VIP별 거리추출
            if 'VIP' in line:
                #sample 168362,0;VIP
                match = re.search(r'(\d+),', line)
                if match:
                    extracted_number = int(match.group(1)) # int변환
                    VIP_STA_LIST.append((i, extracted_number))  # 올바르게 리스트에 추가
            if VIP_STA_LIST:
            #VIP_STA_LIST의 각 요소를들 뺄셈하여 L_LIST에 추가
                # VIP_STA_LIST의 각 요소를 뺄셈하여 L_LIST에 추가
                L_LIST = [(VIP_STA_LIST[j + 1][0], VIP_STA_LIST[j + 1][1] - VIP_STA_LIST[j][1]) for j in range(len(VIP_STA_LIST) - 1)]

    for i, section in enumerate(annotated_sections, start=1):

        #이전 구간의 기울기 찾기
        prev_grade = next((grade for sec, grade in GRADE_LIST if sec == i -1), 0)
        # 현재 구간의 기울기 찾기
        current_grade = next((grade for sec, grade in GRADE_LIST if sec == i), 0)

        # 다음 구간의 기울기 찾기 (존재하면 가져오고, 없으면 0)
        next_grade = next((grade for sec, grade in GRADE_LIST if sec == i + 1), 0)

        #종곡선 모양 판별:볼록형인지 오목형인지
        isSagCrest = get_vertical_curve_type(prev_grade, current_grade)
                
        # VIP 점 찾기 (VIP_STA_LIST 현재 구간(i)과 일치하는 반경을 찾음)
        VIP_STA = next((r for sec, r in VIP_STA_LIST if sec == i), None)
        if VIP_STA is None:
            VIP_STA = 0  # 기본값 (에러 방지)

        #일반철도 구배표용 구배거리
        current_distance = next((r for sec, r in L_LIST if sec == i), None)
        if current_distance is None:
            current_distance = 0  # 기본값 (에러 방지)

        #R 계산용 VCL
        VCL = next((r for sec, r in VCL_LIST if sec == i), None)
       
        R = int(calculate_vertical_curve_radius(VCL, prev_grade, current_grade))
        
        for line in section:        
            #곡선형식별 처리
            if 'BVC' in line or 'EVC' in line or 'VIP' in line:
                
                parts = line.split(',')
                sta = int(parts[0])
                parts2 =  parts[1].split(';')


                
                
                structure = isbridge_tunnel(sta, structure_list)

                sec = parts2[1] if len(parts2) > 1 else None

                

                
                if 'BVC' in line:
                    pitchtype = 'BVC'
                    img_text = f'{format_distance(sta)}\n{prev_grade}'
                    img_bg_color = (255, 255, 255)
                    img_f_name = f'VIP{i}_{pitchtype}'
                    openfile_name = f'{pitchtype}_{structure}용'
                    
                elif 'EVC' in line:
                    pitchtype = 'EVC'
                    img_text = f'{format_distance(sta)}\n{current_grade}'
                    img_bg_color = (255, 255, 255)
                    img_f_name = f'VIP{i}_{pitchtype}'
                    openfile_name = f'{pitchtype}_{structure}용'
                    
                
                elif 'VIP' in line:
                    pitchtype = 'VIP'
                    img_text = f'{format_distance(sta)}\n{R}'#종곡선표
                    img_text2 = f'{current_grade}'#기울기표 구배문자
                    img_text3 = f'L={current_distance}' #기울기표 거리문자
                    img_bg_color = (255, 212, 0) #기울기표 배경
                    img_bg_color2 = (255, 255, 255) #기울기표 문자색
                    img_f_name = f'VIP{i}_{pitchtype}'#종곡선표 파일명
                    img_f_name2 = f'VIP{i}_{pitchtype}_기울기표'#기울기표 파일명
                    openfile_name = f'{pitchtype}_{structure}용'
                    openfile_name2 = f'기울기표_{structure}용'
                    #기울기표 출력
                    create_text_image3(img_text2, img_text3, img_bg_color2, img_f_name2, text_color, image_size=(500, 400), font_size=40)
                    
                else:
                    print('에러')
                    img_text = 'XXXX'
                    img_bg_color = (0, 0, 0)
                    img_f_name = 'X'
                    pitchtype = 'ERROR'
                    openfile_name = 'UNNKOWN'

                #종곡선표 출력
                create_text_image(img_text, img_bg_color, img_f_name, text_color, image_size=(345, 200), font_size=40)


                copy_and_export_csv(openfile_name, img_f_name,isSPPS,current_grade,pitchtype)
                image_names.append(img_f_name)
                structure_comment.append(img_f_name + '-' + structure)
                
        # 객체 인덱스 생성
        objec_index_name = ""
        objec_index_counter = 3025
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
            continue
        '''
        
        if not result == None:
            result_data = f'{sta_value},.freeobj 0;{result};\n'
            result_list.append(result_data)
        
#csv작성
create_curve_post_txt(result_list, structure_comment)

# 파일 삭제
os.remove(unique_file)
os.remove(output_file)

