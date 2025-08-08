from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import re
import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import numpy as np
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import os
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import csv


'''
BVE구배파일을 바탕으로 기울기표(준고속용)을 설치하는 프로그램
-made by dger -
VER 2025.08.07
#add
종단 데이터구조 클래스화

입력파일:BVE에서 추출한 구배파일(pitch_info.TXT)

pitch_info 샘플
0,0
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

#클래스 정의
@dataclass
class VIPdata:
    """
    VIPdata는 종단 선형의 VIP (Vertical Intersection Point) 정보를 표현하는 데이터 클래스입니다.

    Attributes:
        VIPNO (int): VIP 번호.
        isvcurve (bool): 종곡선 여부 (True이면 종곡선이 존재함).
        seg (str): 종곡선의 형태 ('볼록형' 또는 '오목형').
        vradius (float): 종곡선 반경 R (미터 단위).
        vlength (float): 종곡선 길이 (미터 단위).
        next_slope (float): VIP 지점 이후의 종단 경사 (퍼밀 단위).
        prev_slope (float): VIP 지점 이전의 종단 경사 (퍼밀 단위).
        BVC_STA (float): 종곡선 시작점 (BVC).
        VIP_STA (float): VIP.
        EVC_STA (float): 종곡선 종료점 (EVC).
    """
    VIPNO: int = 0
    isvcurve: bool = False
    seg: str = ''
    vradius: float = 0.0
    vlength: float = 0.0
    next_slope: float = 0.0
    prev_slope: float = 0.0
    BVC_STA: float = 0.0
    VIP_STA: float = 0.0
    EVC_STA: float = 0.0

@dataclass
class ObjectDATA:
    VIPNO: int = 0
    vcurvetype: str = ''
    structure: str = ''
    station: float = 0.0
    object_index: int = 0
    filename: str = ''
    object_path: str = ''

def format_distance(number):
    number *= 0.001
    
    return "{:.3f}".format(number)

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
        title="기울기 정보 파일 선택",
        initialfile="pitch_info.txt",  # 사용자가 기본적으로 이 파일을 고르게 유도
        defaultextension=".txt",
        filetypes=[
            ("pitch_info.txt (기본 권장)", "pitch_info.txt"),
            ("모든 텍스트 파일", "*.txt"),
            ("모든 파일", "*.*")
        ]
    )

    if not file_path:
        print("[안내] 파일 선택이 취소되었습니다.")
        return []

    print("[선택된 파일]:", file_path)
    return try_read_file(file_path)

def remove_duplicate_pitch(data):
    filtered_data = []
    previous_pitch = None

    for row in data:
        try:
            station, pitch = map(float, row)
        except ValueError:
            print(f"잘못된 데이터 형식: {row}")
            continue

        if pitch != previous_pitch:
            filtered_data.append((station, pitch))
            previous_pitch = pitch

    return filtered_data

def process_sections(data, threshold=75.0, min_points=2):
    sections = []
    current_section = []
    prev_station = None

    for row in data:
        try:
            station, pitch = map(float, row)
        except (ValueError, TypeError):
            continue

        if prev_station is not None:
            gap = station - prev_station
            if gap >= threshold:
                if len(current_section) >= min_points:
                    sections.append(current_section)
                current_section = []

        current_section.append((station, pitch))
        prev_station = station

    if current_section and len(current_section) >= min_points:
        sections.append(current_section)

    return sections

#핵심로직(클래스화로 구조변경)
def annotate_sections(sections: list[list[tuple[float, float]]], broken_chain) -> list[VIPdata]:
    """
    주어진 종단 기울기 구간 데이터를 기반으로 VIP(Vertical Inflection Point) 정보를 생성합니다.

    각 구간은 시작점(BVC)과 끝점(EVC)을 기준으로 종곡선 제원을 계산하고,
    종곡선의 반경, 길이, 형태(오목/볼록)를 판별하여 VIPdata 객체로 반환합니다.

    Parameters:
        sections: list[list[tuple[float, float]]]
            - 각 구간은 (station, slope) 튜플의 리스트로 구성되며,
              station은 거리값(m), slope는 기울기(m/m)입니다.
            - 예: [[(1000.0, -0.025), (1100.0, 0.005)], [(1200.0, 0.005), (1300.0, -0.010)]]

    Returns:
        list[VIPdata]: VIPdata 객체들의 리스트
            - 각 VIPdata는 하나의 종곡선 구간에 대한 정보를 담고 있습니다.

    Notes:
        - 내부적으로 calculate_vertical_curve_radius() 및 get_vertical_curve_type()을 호출하여
          반지름과 곡선 유형을 결정합니다.
        - slope는 m/m 단위를 사용해야 하며, ‰ 단위일 경우 외부에서 변환이 필요합니다.
    """
    vipdatas: list[VIPdata] = []
    iscurve = False
    i = 1
    for section in sections:
        if not section:
            continue
        #BVC, EVC 추출
        bvc_staion, prev_pitch = section[0]
        evc_staion, next_pitch = section[-1]
        vip_staion = (evc_staion + bvc_staion) / 2

        #파정 적용
        bvc_staion += broken_chain
        evc_staion += broken_chain
        vip_staion += broken_chain

        #종곡선 제원 계산
        vertical_length = evc_staion - bvc_staion #종곡선 길이
        #종곡선 반경
        vertical_radius = calculate_vertical_curve_radius(vertical_length, prev_pitch, next_pitch)
        #오목형 볼록형 판단
        seg = get_vertical_curve_type(prev_pitch, next_pitch)

        #종곡선 여부 판단
        if len(section) < 3:
            isvcurve = False
        else:
            isvcurve = True
        vipdatas.append(VIPdata(
            VIPNO=i,
            isvcurve=isvcurve,
            seg=seg,
            vradius=vertical_radius,
            vlength=vertical_length,
            next_slope=next_pitch,
            prev_slope=prev_pitch,
            BVC_STA=bvc_staion,
            VIP_STA=vip_staion,
            EVC_STA=evc_staion
            )
        )
        i += 1

    return vipdatas

# DXF 파일을 생성하는 함수
class TunnelPitchCreator:
    """터널 구배 DXF 파일을 생성하는 클래스"""
    def __init__(self, work_directory):
        self.work_directory = work_directory

    def create_tunnel_pitch_image(self, filename, text):
        """터널 구배 DXF 생성"""
        doc = ezdxf.new()
        msp = doc.modelspace()

        # 기본 사각형 추가
        self.draw_rectangle(msp, 0, 0, 238, 150, color=8)

        # 텍스트 전처리 (공백 처리 등)
        formatted_result = self.format_text(text)

        # 정수부 및 소수부 분리
        formatted_text, text_x, text_y, is_negative = formatted_result[:4]
        
        # 텍스트 스타일 설정 및 추가
        style_name = 'GHS'
        doc.styles.add(style_name, font='H2GTRE.ttf')
        
        # 정수부 텍스트 추가
        self.create_text(msp, formatted_text, text_x, text_y, 59.9864, 1, style_name)

        # 소수부가 존재하면 추가
        if len(formatted_result) > 4:
            formatted_text2, text_x2, text_y2, height2 = formatted_result[4:]
            self.create_text(msp , formatted_text2, text_x2, text_y2, height2, 0.8162, style_name)
            if is_negative:
                x = 161.376
                y = 76.37
                
            else:
                x = 161.376
                y = 13.5468
            width = 10
            height= 10

            self.draw_rectangle_with_hatch(msp, x, y, width, height, color=1)#소수점 그리기

        # 화살표 추가
        if not 'L' in formatted_text:
            self.create_tunnel_pitch_arrow(msp, is_negative)

        # DXF 저장
        final_path = os.path.join(self.work_directory, filename)
        doc.saveas(final_path)
        return final_path

    def draw_rectangle(self, msp, x, y, width, height, color=0):
        """사각형을 생성하는 함수"""
        points = [(x, y), (x + width, y), (x + width, y + height), (x, y + height), (x, y)]
        msp.add_lwpolyline(points, close=True, dxfattribs={'color': color})

    def draw_rectangle_with_hatch(self, msp, x, y, width, height, color=0):
        """사각형을 생성하는 함수(해치포함)"""
        points = [(x, y), (x + width, y), (x + width, y + height), (x, y + height), (x, y)]
        msp.add_lwpolyline(points, close=True, dxfattribs={'color': color})
        hatch = msp.add_hatch(color=1)
        hatch.paths.add_polyline_path(points, is_closed=True)
        
    def format_text(self, text):
        """텍스트를 포맷팅하여 위치 값과 함께 반환"""
        is_negative = text.startswith('-')
        integer_part, decimal_part = text.lstrip('-').split('.') if '.' in text else (text.lstrip('-'), None)

        # 텍스트 길이에 따라 공백 처리
        if not is_negative:  # 상구배
            if len(text) == 1:#3
                formatted_text = '  L' if integer_part == '0' else '  ' + integer_part
            elif len(text) == 2:#13
                formatted_text = ' ' + integer_part
            elif len(text) == 3:#1.1
                formatted_text = ' ' + integer_part  # 정수부만 사용
            elif len(text) == 4:#27.4
                formatted_text = integer_part  # 정수부만 사용

            text_x, text_y = 60.7065, 13.5468  # 정수부 위치

            if decimal_part:  # 소수부가 있는 경우
                formatted_text2 = decimal_part  # 소수부만 사용
                text_x2, text_y2 = 176.0235, 28.5329  # 소수부 위치
                height2 = 45.043  # 소수부 글자 크기
                return formatted_text, text_x, text_y, is_negative, formatted_text2, text_x2, text_y2, height2

        else:  # 하구배
            if len(text) == 2:#-3
                formatted_text = '  L' if integer_part == '0' else '  ' + integer_part
            elif len(text) == 3:#-11
                formatted_text = ' ' + integer_part
            elif len(text) == 4:#-4.5
                formatted_text = ' ' + integer_part  # 정수부만 사용
            elif len(text) == 5:#-11.5
                formatted_text = integer_part  # 정수부만 사용

            text_x, text_y = 60.7065, 76.37  # 정수부 위치

            if decimal_part:  # 소수부가 있는 경우
                formatted_text2 = decimal_part  # 소수부만 사용
                text_x2, text_y2 = 176.0235, 91.3561  # 소수부 위치
                height2 = 45.043  # 소수부 글자 크기
                return formatted_text, text_x, text_y, is_negative, formatted_text2, text_x2, text_y2, height2

        return formatted_text, text_x, text_y, is_negative  # 소수부가 없으면 정수부만 반환

    def create_text(sefl, msp, text, text_x, text_y, height, width, style_name):
        msp.add_text(text, dxfattribs={
            'insert': (text_x, text_y), 
            'height': height, 
            'width': width, 
            'style': style_name, 
            'color': 1
        })
        
    def create_tunnel_pitch_arrow(self, msp, is_negative):
        """터널 구배 화살표 생성"""
        if not is_negative:  # 상구배
            points = [
                (115.825, 116.333), (135.8065, 136.3991), (155.8726, 116.333), (155.8726, 102.1935),
                (140.8865, 117.2643), (140.8865, 91.3561), (130.8111, 91.3561), (130.8111, 117.2643),
                (115.825, 102.1935)
            ]
        else:  # 하구배
            points = [
                (115.9096, 33.6129), (135.8911, 13.5468), (155.8726, 33.6129), (155.8726, 47.7524),
                (140.8865, 32.7663), (140.8865, 58.5898), (130.8958, 58.5898), (130.8958, 32.7663),
                (115.9096, 47.7524)
            ]

        # 화살표 추가
        msp.add_lwpolyline(points, close=True, dxfattribs={'color': 1})
        hatch = msp.add_hatch(color=1)
        hatch.paths.add_polyline_path(points, is_closed=True)
    
def replace_text_in_dxf(file_path, modified_path, sta, grade, seg, R):
    """DXF 파일의 특정 텍스트를 새 텍스트로 교체하고, 특정 레이어 가시성을 조절하는 함수"""
    try:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()

        # 🟢 특정 레이어의 TEXT 엔티티 찾아서 교체
        for entity in msp.query("TEXT"):
            if entity.dxf.layer == "측점":
                if len(sta) == 5:#3.456
                    sta = ' ' + sta
                    
                entity.dxf.text = sta  # STA 변경
                if len(sta) == 7:#123.456
                    entity.dxf.width = 0.9
                
            elif entity.dxf.layer == "구배":
                if len(grade) == 1:#2
                    grade = grade + ' '
                entity.dxf.text = grade  # 구배 변경
            elif entity.dxf.layer == "R":
                if R != 'None':
                    entity.dxf.text = R  #종곡선반경 변경
        # 🟢 레이어 가시성 조절 (볼록형: 표시, 오목형: 숨김)
        layers = doc.layers
        
        if seg == '오목형':
            layers.get(seg).on()
            layers.get('볼록형').off()
            
        elif seg == '볼록형':
            layers.get(seg).on()
            layers.get('오목형').off()
        
        # 변경된 DXF 저장
        doc.saveas(modified_path)
        #print("✅ DXF 수정 완료")
        return True

    except Exception as e:
        print(f"❌ DXF 수정 실패: {e}")
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

                #print(f"✅ 변환 완료: {output_path}")
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
            #print(f"✅ 여백 제거 및 크기 조정 완료: {output_path}")

        except Exception as e:
            print(f"❌ 이미지 처리 실패: {e}")
          
#기울기표용
class GradePost:
    def __init__(self, work_directory: str):
        self.work_directory = work_directory
        if not os.path.exists(self.work_directory):
            os.makedirs(self.work_directory)

    def create_text_image(self, text, font, text_color, image_size, rotate_angle=0):
        text_image = Image.new('RGBA', image_size, (255, 255, 255, 0))
        text_draw = ImageDraw.Draw(text_image)
        text_draw.text((20, 20), text, font=font, fill=text_color)
        rotated_text_image = text_image.rotate(rotate_angle, expand=True)
        bbox = rotated_text_image.getbbox()
        cropped_temp_img = rotated_text_image.crop(bbox) if bbox else rotated_text_image
        white_bg = Image.new('RGB', cropped_temp_img.size, (255, 255, 255))
        white_bg.paste(cropped_temp_img, (0, 0), cropped_temp_img.split()[3])
        return white_bg

    def create_arrow_symbol(self, image_size, text_color, is_negative):
        arrow_image = Image.new('RGBA', image_size, (255, 255, 255, 0))
        arrow_draw = ImageDraw.Draw(arrow_image)
        arrow_points = [(372, 70), (417, 42), (401, 15), (456, 38), (458, 98), (440, 73), (393, 104), (372, 70)]
        arrow_draw.polygon(arrow_points, fill=text_color, outline=text_color)
        return arrow_image.transpose(Image.FLIP_TOP_BOTTOM) if is_negative else arrow_image

    def create_grade_post(self, text, text2, filename, text_color, post_direction, image_size=(500, 400), font_size1=180, font_size2=100):
        img = Image.new('RGB', image_size, (255, 255, 255))
        draw = ImageDraw.Draw(img)
        try:
            font_main = ImageFont.truetype('c:/windows/fonts/HYGTRE.ttf', font_size1)
            font_sub = ImageFont.truetype("gulim.ttc", font_size2)
        except IOError:
            print("폰트 파일을 찾을 수 없습니다.")
            return

        is_negative = text.startswith('-')
        integer_part, decimal_part = text.lstrip('-').split('.') if '.' in text else (text.lstrip('-'), None)
        rotate_angle = -30 if is_negative else 30
        if text == '0':
            white_bg = img
        else:
            white_bg = self.create_text_image(integer_part, font_main, text_color, image_size, rotate_angle)
        post_positions = {'좌': (107, 70 if int(integer_part) > 9 else 110), '우': (110, 110)}
        img.paste(white_bg, post_positions.get(post_direction, (110, 110)))

        if decimal_part:
            font_decimal = ImageFont.truetype('c:/windows/fonts/HYGTRE.ttf', 75)
            decimal_bg = self.create_text_image(decimal_part, font_decimal, text_color, image_size, rotate_angle)
            decimal_positions = self.get_decimal_position(post_direction, integer_part, is_negative)
            img.paste(decimal_bg, decimal_positions)
        
        draw.line([(0, 280), (500, 280)], fill=text_color, width=10)
        distance_positions = self.get_distance_position(post_direction, text2)
        distance_text = f'L={text2}M' 
        draw.text(distance_positions, distance_text, font=font_sub, fill=text_color)
        if text == '0':
            arrow_image = self.create_L_symbol(image_size, text_color)
        else:
            arrow_image = self.create_arrow_symbol(image_size, text_color, is_negative)
        
        img.paste(arrow_image, (0, -120 if is_negative else 0), arrow_image)

        if not filename.endswith('.png'):
            filename += '.png'
        final_dir = os.path.join(self.work_directory, filename)
        img.save(final_dir)
        #print(f"최종 이미지 저장됨: {final_dir}")
        
    def get_decimal_position(self, post_direction, integer_part, is_negative):
        if post_direction == '좌':
            if int(integer_part) > 9:#구배가 2자리
                return (330, 140) if is_negative else (310, 40)
            else:#구배가 1자리
                return (240, 160) if is_negative else (200, 60)
        return (110, 110)  # '우' 기본 위치
    
    def get_distance_position(self, post_direction, integer_part):
        if post_direction == '좌':
            
            if len(integer_part) == 3:#거리가 3자리
                return (100,290)
            elif len(integer_part) == 4:#거리가 4자리
                return (75,290)
            else:
                return (60,290)
    def create_L_symbol(self, image_size, text_color):
        arrow_image = Image.new('RGBA', image_size, (255, 255, 255, 0))
        arrow_draw = ImageDraw.Draw(arrow_image)
        arrow_points = [(121, 42), (121, 242), (313, 242), (313, 181), (171, 181), (171, 42)]
        arrow_draw.polygon(arrow_points, fill=text_color, outline=text_color)
        return arrow_image
    
def copy_and_export_csv(open_filename: str, output_filename: str, curvetype: str, source_diretory: str, work_directory: str):
    # Define the input and output file paths
    open_file = source_diretory + open_filename + '.csv'
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
            if f'LoadTexture, {curvetype}_기울기표.png,' in line:
                line = line.replace(f'LoadTexture, {curvetype}_기울기표.png,', f'LoadTexture, {output_filename}_기울기표.png,')
            # Append the modified line to the new_lines list
            new_lines.append(line)
    
    # Open the output file for writing the modified lines
    with open(output_file, 'w', encoding='utf-8') as file:
        # Write the modified lines to the output file
        file.writelines(new_lines)





def create_pitch_post_txt(data_list: list[ObjectDATA], work_directory: str):
    """
    결과 데이터를 받아 파일로 저장하는 함수.
    """
    output_file = work_directory + "pitch_post.txt"  # 저장할 파일 이름

    with open(output_file, "w", encoding="utf-8") as file:
         for data in data_list:  # 두 리스트를 동시에 순회
            file.write(f"{data.station},.freeobj 0;{data.object_index};,;VIP{data.VIPNO}_{data.vcurvetype}-{data.structure}\n")  # 원하는 형식으로 저장


def create_pitch_index_txt(data_list: list[ObjectDATA], work_directory: str):
    """
    결과 데이터를 받아 파일로 저장하는 함수.
    """
    output_file = work_directory + "pitch_index.txt"  # 저장할 파일 이름

    with open(output_file, "w", encoding="utf-8") as file:
        for data in data_list:  # 두 리스트를 동시에 순회
            file.write(f".freeobj({data.object_index}) {data.object_path}/{data.filename}.csv\n")  # 원하는 형식으로 저장


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

def get_vertical_curve_type(start_grade: float, end_grade: float) -> str:
    if start_grade > end_grade:
        return "볼록형"  # 볼록형 (정상 곡선)
    else:
        return "오목형"  # 오목형 (골짜기 곡선)


def calculate_vertical_curve_radius(length: float, start_grade: float, end_grade: float) -> float:
    """
    종곡선 반지름(R)을 계산하는 함수

    Parameters:
        length (float): 종곡선 길이 (L), 단위: m
        start_grade (float): 시작 경사, 단위: m/m (예: -0.025 for -25‰)
        end_grade (float): 끝 경사, 단위: m/m

    Returns:
        float: 종곡선 반지름 R (단위: m)
    """
    delta_g = end_grade - start_grade  # 경사 변화량 (m/m)

    if delta_g == 0:
        return 0.0  # 구배 변화가 없으면 반지름은 무한대 (직선)

    radius = length / abs(delta_g)  # 반지름 계산 (단위: m)
    return radius


def format_grade(value):
    '''
    구배를 1000곱하고 변환 포맷
    '''
    return f"{value * 1000:.1f}".rstrip('0').rstrip('.')  # 소수점 이하 0 제거

#civil3d함수
'''WIP'''

def process_verticulcurve(vipdata: VIPdata, viptype: str, current_sta: float, current_structure: str, source_directory: str, work_directory: str):

    converter = DXF2IMG()

    grade_text = format_grade(vipdata.next_slope)
    station_text = f'{format_distance(current_sta)}'

    img_f_name = f'VIP{vipdata.VIPNO}_{viptype}'
    r = str(int(vipdata.vradius))
    
    file_path = source_directory + f'{viptype}.dxf'
    final_output_image = work_directory + img_f_name + '.png'

    modifed_path = work_directory + 'BVC-수정됨.dxf'
    replace_text_in_dxf(file_path, modifed_path, station_text, grade_text, vipdata.seg , r)

    output_paths = converter.convert_dxf2img([modifed_path], img_format='.png')
    converter.trim_and_resize_image(output_paths[0], final_output_image, target_size=(320, 200))

def process_vertical(vip: VIPdata, current_distance: float, pitchtype: str, structure: str, work_directory: str):
    grade_post_generator = GradePost(work_directory)
    tunnel_post_generator = TunnelPitchCreator(work_directory)
    converter = DXF2IMG()

    output_image = work_directory + 'output_image.png'
    filename = 'BVC-수정됨.dxf'

    current_grade = vip.next_slope
    img_text2 = format_grade(current_grade)#기울기표 구배문자
    img_text3 = f'{int(current_distance)}' #기울기표 거리문자
    img_bg_color2 = (255, 255, 255) #기울기표 문자                     
    img_f_name2 = f'VIP{vip.VIPNO}_{pitchtype}_기울기표'#기울기표 파일명
    openfile_name2 = f'기울기표_{structure}용'
    
    final_output_image = work_directory + img_f_name2 + '.png'    
    
    if structure == '터널':
        tunnel_post_generator.create_tunnel_pitch_image(filename, img_text2)
        modifed_path = work_directory + 'BVC-수정됨.dxf'
        output_paths = converter.convert_dxf2img([modifed_path], img_format='.png')
        converter.trim_and_resize_image(output_paths[0], final_output_image, target_size=(320, 200))
    else:
        grade_post_generator.create_grade_post(img_text2, img_text3, img_f_name2, (0, 0, 0), '좌')


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

def is_civil3d_format(lines):
    return any('pitch' in cell.lower() for line in lines for cell in line)

def convert_pitch_lines(lines):
    """
    .pitch 제거 → ; 를 ,로 변환 → 마지막 , 제거
    lines가 List[List[str]] 혹은 List[str]인 경우 모두 처리 가능
    """
    converted = []

    for line in lines:
        # line이 리스트이면 문자열로 결합
        if isinstance(line, list):
            line = ','.join(line)

        line = line.strip()

        # 1단계: ".CURVE" 등 대소문자 구분 없이 제거 (정규식 사용)
        line = re.sub(r'\.pitch', '', line, flags=re.IGNORECASE)

        #4단계: line의 각 요소 추출
        parts = line.split(',')
        if len(parts) == 1 or len(parts) == 0:
            print(f"[경고] 잘못된 행 형식: {line} → 건너뜀")
            continue  # 또는 raise ValueError(f"Invalid line format: {line}")
        try:
            if len(parts) == 2:
                sta, pitch = map(float, parts)
                pitch *= 0.001 #내부 단위 자료구조 통일을 위해 0.001곱하기
            else:
                raise ValueError

            converted.append((sta, pitch))

        except ValueError:
            print(f"[오류] 숫자 변환 실패: {line} → 건너뜀")
            continue

    return converted

def process_and_save_sections(lines: list[list[tuple[float, float]]], brokenchain) -> list[VIPdata]:
    """종곡선 정보를 처리하고 파일로 저장"""

    # 중복 제거
    # Civil3D 형식 여부 판단
    civil3d = is_civil3d_format(lines)
    unique_data = convert_pitch_lines(lines) if civil3d else remove_duplicate_pitch(lines)

    # 구간 정의 및 처리
    sections = process_sections(unique_data)
    vipdatas = annotate_sections(sections, brokenchain)

    return vipdatas

#1. 곡선 구간(Line) 생성 분리
def get_vcurve_lines(vip: VIPdata) -> list[list]:
    if vip.isvcurve:
        return [['BVC', vip.BVC_STA], ['VIP', vip.VIP_STA], ['EVC', vip.EVC_STA]]
    else:
        return [['VIP', vip.VIP_STA]]

def process_bve_profile(vipdats: list[VIPdata], structure_list, source_directory: str, work_directory: str):
    """주어진 구간 정보를 처리하여 이미지 및 CSV 생성"""
    #이미지 저장
    object_index = 3025
    objects = []
    object_folder = target_directory.split("Object/")[-1]

    for i, vip in enumerate(vipdats):
        print(f'현재 구간 VIP : {vip.VIPNO}')
        lines = get_vcurve_lines(vip)
        if not lines:
            continue

        # 일반철도 구배표용 구배거리
        if i < len(vipdats) - 1:
            current_distance = vipdats[i+1].VIP_STA - vip.VIP_STA
        else:
            current_distance = 0  # 기본값 (에러 방지)

        for key, value in lines:
            current_sta = value
            current_structure = isbridge_tunnel(current_sta, structure_list)
            if key == 'VIP':
                process_vertical(vip, current_distance, key,  current_structure, work_directory)
            process_verticulcurve(vip, key, value, current_structure, source_directory, work_directory)
            img_f_name = f'VIP{vip.VIPNO}_{key}'
            openfile_name = f'{key}_{current_structure}용'
            copy_and_export_csv(openfile_name, img_f_name, key, source_directory, work_directory)

            objects.append(ObjectDATA(
                VIPNO=vip.VIPNO,
                vcurvetype=key,
                structure=current_structure,
                station=value,
                object_index=object_index,
                filename=img_f_name,
                object_path=object_folder
                )
            )
            object_index += 1
        print(f'현재 구간 VIP ; {vip.VIPNO} - 완료')

    return objects


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


class PitchProcessingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.log_box = None
        self.title("Pitch 데이터 처리기")
        self.geometry("700x500")

        self.source_directory = 'c:/temp/pitch/소스/' #원본 소스 위치
        self.work_directory = ''
        self.target_directory = ''
        self.isbrokenchain: bool = False
        self.brokenchain: float = 0.0
        self.create_widgets()

    def create_widgets(self):
        label = ttk.Label(self, text="기울기 데이터 자동 처리 시스템", font=("Arial", 16, "bold"))
        label.pack(pady=10)

        self.log_box = tk.Text(self, height=20, wrap=tk.WORD, font=("Consolas", 10))
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        run_button = ttk.Button(self, text="기울기 데이터 처리 실행", command=self.run_main)
        run_button.pack(pady=10)

    def log(self, msg):
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)

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

    def run_main(self):
        try:
            # 디렉토리 설정
            self.log("작업 디렉토리 확인 중...")
            self.work_directory = 'c:/temp/pitch/result/'
            if not os.path.exists(self.work_directory):
                os.makedirs(self.work_directory)
                self.log(f"디렉토리 생성: {self.work_directory}")
            else:
                self.log(f"디렉토리 존재: {self.work_directory}")

            # 대상 디렉토리 선택
            self.log("대상 디렉토리 선택 중...")
            self.target_directory = select_target_directory()
            self.log(f"대상 디렉토리: {self.target_directory}")

            # ㅊ파정확인
            self.process_proken_chain()

            # 파일 읽기
            self.log("기울기 정보 파일 읽는 중...")
            data = read_file()
            if not data:
                self.log("파일 없음 또는 불러오기 실패.")
                return

            # 구조물 데이터 로드
            self.log("구조물 데이터 로드 중...")
            structure_list = load_structure_data()
            # 구조물 측점 파정처리
            structure_list = apply_brokenchain_to_structure(structure_list, self.brokenchain)
            # 곡선 데이터 처리

            self.log("BVE용 처리 시작...")
            vipdatas = process_and_save_sections(data, self.brokenchain)

            objectdatas = process_bve_profile(vipdatas, structure_list, self.source_directory, self.work_directory)

            # 최종 텍스트 생성
            if objectdatas:
                self.log("최종 결과 생성 중...")
                create_pitch_post_txt(objectdatas, self.work_directory)
                create_pitch_index_txt(objectdatas, self.work_directory)
                self.log("결과 파일 생성 완료!")
            self.log("BVE 작업 완료")

            copy_all_files(self.work_directory, self.target_directory, ['.csv', '.png', '.txt'], ['.dxf', '.ai'])
            self.log("모든 작업이 완료되었습니다.")

            messagebox.showinfo("완료", "Pitch 데이터 처리가 성공적으로 완료되었습니다.")

        except Exception as e:
            self.log(f"[오류] {str(e)}")
            messagebox.showerror("오류", f"처리 중 오류가 발생했습니다:\n{e}")


if __name__ == "__main__":
    app = PitchProcessingApp()
    app.mainloop()
