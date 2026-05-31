import random
import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import math
import re
import numpy as np
from enum import Enum
from shapely.geometry import Point, LineString
import matplotlib.pyplot as plt
import ezdxf  # Import ezdxf for saving to DXF

def load_coordinates():
    coord_filepath = 'c:/temp/bve_coordinates.txt'
    return read_polyline(coord_filepath)

def read_polyline(file_path):
    points = []
    with open(file_path, 'r') as file:
        for line in file:
            x, y, z = map(float, line.strip().split(','))
            points.append((x, y, z))
    return points

def get_elevation_pos(pos, polyline_with_sta):
    new_z = None
    
    for i in range(len(polyline_with_sta) - 1):
        sta1, x1, y1, z1 = polyline_with_sta[i]#현재값
        sta2, x2, y2, z2 = polyline_with_sta[i + 1]#다음값
        L = sta2 - sta1
        L_new = pos - sta1
        
        if sta1 <= pos < sta2:
            new_z = calculate_height_at_new_distance(z1, z2, L, L_new)
            return new_z


    return new_z

def calculate_height_at_new_distance(h1, h2, L, L_new):
    """주어진 거리 L에서의 높이 변화율을 기반으로 새로운 거리 L_new에서의 높이를 계산"""
    h3 = h1 + ((h2 - h1) / L) * L_new
    return h3


#그래프 생성
def plot_polyline_and_points(polyline_with_sta,params):
    pos = params['pos']
    next_pos = params['next_pos']
    mast_height=params['mast_height']
    contact_height=params['contact_height']
    pos_z=params['pos_z']
    next_pos_z=params['next_pos_z']
    anlge=params['anlge']

    #폴리선 플롯
    sta = [point[0] for point in polyline_with_sta]
    polyline_x = [point[0] for point in polyline_with_sta]
    polyline_y = [point[3] for point in polyline_with_sta]
    #plt.plot(polyline_x, polyline_y, label="Polyline", color='r')
    selected_x =[]
    selected_y = []
    
    # Scatter plot for all polyline points
    for x, y in zip(polyline_x, polyline_y):
        if pos - 100 <= x <= next_pos + 100:
            selected_x.append(x)
            selected_y.append(y)
            
            plt.text(x, y, x , fontsize=12, color='red')

    # 선택된 점들만 연결하여 선 그리기
    if len(selected_x) > 1:
        plt.plot(selected_x, selected_y, label="Polyline", color='r', linestyle='-', linewidth=2)

    #측점 플롯
    plt.text(pos, pos_z, f"{pos}", fontsize=10, color='black')
    plt.text(next_pos, next_pos_z, f"{next_pos}", fontsize=10, color='black')
    
    #전주 플롯
    plt.plot([pos, pos], [pos_z, pos_z + mast_height], 'b-', label="mast")
    plt.plot([next_pos, next_pos], [next_pos_z, next_pos_z + mast_height], 'b-')

    #전선 플롯
    plt.plot([pos, next_pos], [pos_z + contact_height, next_pos_z + contact_height], 'g--', label="wire")

    plt.title("Railway Polyline and Points Visualization")
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.legend()
    #plt.axis('equal')
    plt.grid(True)
    plt.show()
    
def calculate_slope(h1, h2, gauge):
    """주어진 높이 차이와 수평 거리를 바탕으로 기울기(각도) 계산"""
    slope = (h2 - h1) / gauge  # 기울기 값 (비율)
    return math.degrees(math.atan(slope))  # 아크탄젠트 적용 후 degree 변환

def change_permile_to_degree(permile):
    """퍼밀 값을 도(degree)로 변환"""
    # 정수 또는 문자열이 들어오면 float으로 변환
    if not isinstance(permile, (int, float)):
        permile = float(permile)
    return math.degrees(math.atan(permile / 1000)) 
def isslope(cur_sta, curve_list):
    """sta가 곡선 구간에 해당하는지 구분하는 함수"""
    rounded_sta = get_block_index(cur_sta)  # 25 단위로 반올림
    
    for sta, g in curve_list:
        if rounded_sta == sta:
            if g == 0:
                return '수평', 0  # 반경이 0이면 직선
            else:
                return '기울기', f'{g * 1000:.2f}'

    return '수평', 0 # 목록에 없으면 기본적으로 직선 처리

def load_pitch_data():
    """곡선 데이터를 텍스트 파일에서 불러오는 함수"""
    txt_filepath = 'c:/temp/pitch_info.txt'
    if txt_filepath:
        return find_pitch_section(txt_filepath)
    else:
        print("지정한 파일을 찾을 수 없습니다.")
        return None
def find_pitch_section(txt_filepath='pitchinfo.txt'):
    """txt 파일을 읽고 곧바로 측점(sta)과 기울기(pitch) 정보를 반환하는 함수"""
    
    curve_list = []

    # 텍스트 파일(.txt) 읽기
    df_curve = pd.read_csv(txt_filepath, sep=",", header=None, names=['sta', 'radius'])

    # 곡선 구간 정보 저장
    for _, row in df_curve.iterrows():
        curve_list.append((row['sta'], row['radius']))
    
    return curve_list

def get_block_index(current_track_position, block_interval = 25):
    """현재 트랙 위치를 블록 인덱스로 변환"""
    return math.floor(current_track_position / block_interval + 0.001) * block_interval

def save_to_dxf(polyline_with_sta, params,  file_name='output.dxf'):
    pos = params['pos']
    next_pos = params['next_pos']
    mast_height=params['mast_height']
    contact_height=params['contact_height']
    pos_z=params['pos_z']
    next_pos_z=params['next_pos_z']
    anlge=params['anlge']

    # Create a new DXF drawing
    doc = ezdxf.new()
    msp = doc.modelspace()

    #폴리선 플롯
    sta = [point[0] for point in polyline_with_sta]
    polyline_x = [point[0] for point in polyline_with_sta]
    polyline_y = [point[3] for point in polyline_with_sta]

    selected_x =[]
    selected_y = []

    #pos 문자
    msp.add_text(pos, dxfattribs={'insert': (pos,pos_z)})
    msp.add_text(next_pos, dxfattribs={'insert': (next_pos,next_pos_z)})
    
    # Scatter plot for all polyline points
    for x, y in zip(polyline_x, polyline_y):
        if pos - 100 <= x <= next_pos + 100:
            selected_x.append(x)
            selected_y.append(y)
            msp.add_text(x, dxfattribs={'insert': (x,y), 'color': 1})
    
    # 선택된 점들로 폴리선 생성
    polyline_points = [(x, y) for x, y in zip(selected_x, selected_y)]
    msp.add_lwpolyline(polyline_points, close=False, dxfattribs={'color': 1})

    #MAST 그리기
    msp.add_line([pos, pos_z], [pos, pos_z + mast_height], dxfattribs={'color': 4})
    msp.add_line([next_pos, next_pos_z], [next_pos, next_pos_z + mast_height], dxfattribs={'color': 4})

    #전선 그리기
    msp.add_line([pos, pos_z + contact_height], [next_pos, next_pos_z + contact_height], dxfattribs={'color': 3})
    # Save the DXF file
    doc.saveas(file_name)
    print(f"DXF file saved as {file_name}")
    
# BVE 좌표 로드
polyline = load_coordinates()
polyline_with_sta = [(i * 25, *values) for i, values in enumerate(polyline)]
contact_height = 5.2
mast_height = 8

# 기울기 정보 로드
pitchlist = load_pitch_data()
if pitchlist:
    print("기울기선 정보가 성공적으로 로드되었습니다.")
    
while 1:
    while 1:
        try:
            pos = int(input('시작 측점 입력 : '))
            next_pos = int(input('끝 측점 입력 : '))
            break
        except ValueError as e:
            print('an error occurred in pos')
    current_span = next_pos - pos
    _, current_pitch = isslope(pos, pitchlist)
    pos_z= get_elevation_pos(pos, polyline_with_sta)
    next_pos_z = get_elevation_pos(next_pos, polyline_with_sta)
    permile_degree = change_permile_to_degree(current_pitch)
    anlge = calculate_slope(pos_z, next_pos_z, current_span)
    bve_angle = anlge - permile_degree
    print(f'현재 측점: {pos}, 표고 : {pos_z}')
    print(f'다음 측점: {next_pos}, 표고 : {next_pos_z}')
    print(f'현재 구배 : {current_pitch}\u2030')
    print(f'원래 각도 : {anlge:.4f}도')
    print(f'bve 각도 : {bve_angle:.4f}도')
    params = {
        'pos':pos,
        'next_pos':next_pos,
        'mast_height':mast_height,
        'contact_height':contact_height,
        'pos_z':pos_z,
        'next_pos_z':next_pos_z,
        'anlge':anlge
        }
    
    
    # DXF 파일로 저장
    while True:
        try:
            save_to_dxf(polyline_with_sta, params, 'c:/temp/test.dxf')
            print('DXF saved successfully')
            break  # Exit the loop once the save operation is successful
        except Exception as e:
            print(f'Error occurred while saving DXF: {e}')
            retry = input("Do you want to retry saving the file? (y/n): ").lower()
            if retry != 'y':
                print("Aborting DXF save.")
                break  # Exit the loop if the user does not want to retry
    plot_polyline_and_points(polyline_with_sta,params)
