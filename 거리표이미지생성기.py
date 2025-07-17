import csv
from tkinter import filedialog
import tkinter as tk
from PIL import Image, ImageDraw, ImageFont
import os
import pandas as pd
import math
import re
import textwrap
import sys
import time  # 진행률 테스트용
from tqdm.notebook import tqdm # 이 부분만 변경

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
# 기본 작업 디렉토리
default_directory = 'c:/temp/km_post/'
work_directory = None
# 사용자가 설정한 작업 디렉토리가 없으면 기본값 사용
if not work_directory:
    work_directory = default_directory

# 디렉토리가 존재하지 않으면 생성
if not os.path.exists(work_directory):
    os.makedirs(work_directory)

print(f"작업 디렉토리: {work_directory}")

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

def find_last_block(data):
    last_block = None  # None으로 초기화하여 값이 없을 때 오류 방지
    for line in data:
        if isinstance(line, str):  # 문자열인지 확인
            match = re.search(r'(\d+),', line)
            if match:
                last_block = int(match.group(1))  # 정수 변환하여 저장
    
    return last_block  # 마지막 블록 값 반환


def create_km_image(text, bg_color, filename, text_color, image_size=(500, 300), font_size=40):
    # 이미지 생성
    img = Image.new('RGB', image_size, color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # 폰트 설정
    font = ImageFont.truetype('c:/windows/fonts/HYGTRE.ttf', font_size)

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

def create_m_image(text, text2, bg_color, filename, text_color, image_size=(500, 300), font_size=40, font_size2=40 ):
    # 이미지 생성
    img = Image.new('RGB', image_size, color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # 폰트 설정
    font = ImageFont.truetype('c:/windows/fonts/HYGTRE.ttf', font_size)
    font2 = ImageFont.truetype('c:/windows/fonts/HYGTRE.ttf', font_size2)

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
    
def copy_and_export_csv(open_filename='km표-토공용', output_filename='13460', ptype = 'km표'):
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
            if f'LoadTexture, {ptype}.png,' in line:
                line = line.replace(f'LoadTexture, {ptype}.png,', f'LoadTexture, {output_filename}.png,')

            # Append the modified line to the new_lines list
            new_lines.append(line)
    
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

def create_km_object(last_block, structure_list):
    last_block = (last_block // 200)
    index_datas=[]
    post_datas= []
    structure_comment=[]
    first_index = 4025
    
    print('-----이미지 생성중-----\n')
    for i in range(last_block):
        current_sta = i * 200
        current_structure = isbridge_tunnel(current_sta, structure_list)
        if current_sta % 1000 == 0: #1000의 배수이면
            post_type = 'km표'
                       
        elif current_sta % 200 == 0:#1000의 배수는 제외
            post_type = 'm표'

        # 소수점 앞뒤 자리 나누기
        current_km_int =  current_sta * 0.001
        km_string, m_string = str(current_km_int).split('.')

        img_text1 = f'{km_string}'
        img_text2 = f'{m_string}'
        img_bg_color = (2, 6, 140)
        text_color = (255,255,255)
        img_f_name = f'{current_sta}'
        openfile_name = f'{post_type}_{current_structure}용'

        if len(img_text2) !=1 :#글자수가 1이 아니면 강제로 1로 적용 예)60 >6
           img_text2 = resize_to_length(img_text2, desired_length=1)
        if post_type == 'km표':
            create_km_image(img_text1, img_bg_color, img_f_name, text_color, image_size=(500, 300), font_size=235)
            
        elif post_type == 'm표':
            if int(m_string) != 0:
                create_m_image(img_text1, img_text2, img_bg_color, img_f_name, text_color, image_size=(250, 400), font_size=144, font_size2=192 )

        #텍스쳐와 오브젝트 csv생성
        copy_and_export_csv(openfile_name, img_f_name, post_type)
        
        index = first_index + i

        #구문데이터 생성
        index_data = create_km_index_data(index , current_sta)
        post_data = create_km_post_data(index , current_sta, current_structure)

        #리스트에 추가
        index_datas.append(index_data)
        post_datas.append(post_data)
    print("\n구문 생성 완료!")      
    print("\n이미지 생성 완료!")
    
   
    return index_datas, post_datas   

def create_km_index_data(idx, sta):
    data = f'.freeobj({idx}) abcdefg/{sta}.csv\n'
    return data

def create_km_post_data(idx, sta, struc):
    data = f'{sta},.freeobj 0;{idx};,;{struc}\n'
    return data

def create_txt(output_file, data):
    with open(output_file, 'w', encoding='utf-8') as file:
        for line in data:
            file.write(line)
    
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

class KmObjectApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("KM Object 생성기")
        self.geometry("600x400")

        self.work_directory = 'c:/temp/km/'  # 필요 시 변경 가능
        if not os.path.exists(self.work_directory):
            os.makedirs(self.work_directory)

        self.structure_excel_path = None

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

    def run_main(self):
        try:
            self.log("파일 읽는 중...")
            data = read_file()
            if not data:
                self.log("데이터가 비어 있습니다.")
                return

            last_block = find_last_block(data)
            self.log(f"마지막 측점 = {last_block}")

            if not self.structure_excel_path:
                self.log("엑셀 파일이 선택되지 않았습니다.")
                messagebox.showwarning("경고", "구조물 정보 엑셀 파일을 선택해주세요.")
                return

            self.log("구조물 정보 불러오는 중...")
            structure_list = find_structure_section(self.structure_excel_path)
            if structure_list:
                self.log("구조물 정보가 성공적으로 로드되었습니다.")
            else:
                self.log("구조물 정보가 없습니다.")

            self.log("KM Object 생성 중...")
            index_datas, post_datas = create_km_object(last_block, structure_list)

            index_file = os.path.join(self.work_directory, 'km_index.txt')
            post_file = os.path.join(self.work_directory, 'km_post.txt')

            self.log(f"파일 작성: {index_file}")
            create_txt(index_file, index_datas)

            self.log(f"파일 작성: {post_file}")
            create_txt(post_file, post_datas)

            self.log("txt 작성이 완료됐습니다.")
            self.log("모든 작업이 완료됐습니다.")
            messagebox.showinfo("완료", "KM Object 생성이 완료되었습니다.")

        except Exception as e:
            self.log(f"[오류] {str(e)}")
            messagebox.showerror("오류", f"작업 중 오류가 발생했습니다:\n{e}")

if __name__ == "__main__":
    app = KmObjectApp()
    app.mainloop()

    
