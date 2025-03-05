import tkinter as tk
from tkinter import filedialog, ttk
import math
import csv
import pandas as pd

'''
BVE곡선파일을 바탕으로 곡선레일(5m)를 설치하는 프로그램
-made by dger -
VER 20250303 2343
#수정
직선구간에 프리오브젯ㄱ트 생성 방지

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

준비파일: 구조물 측점 csv 등
구조물 측점 샘플파일
B1	18840	19120	280
B2	19240	19380	140

출력파일: FREEOBJ구문파일, railtype구문파일

'''

# Global Variables
increment = 5  #계산간격
block_length =25 #bve블록단위
# File Reading Function
def read_file():
    # Open file dialog
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

# Parsing Curve Info
def parsing_curveinfo(lines):
    curveinfo = []
    
    for line in lines:
        try:
            station = int(line[0])
        except Exception as e:
            print("station 읽는 중 오류가 발생했습니다:", e)
            station = 0.0
        try:
            radius = float(line[1])
        except Exception as e:
            print("radius 읽는 중 오류가 발생했습니다:", e)
            radius = 0.0
        try:
            cant = float(line[2])
        except Exception as e:
            cant = 0.0

        curveinfo.append([station, radius, cant])
    
    return curveinfo

def extract_cant(curveinfo):
    c_list =[]
    for info in curveinfo:
        STA = info[0]
        R = info[1]
        C = info[2]
        c_list.append([STA,R,C])
    return c_list

def cal_direction(R):
    return -1 if R < 0 else 1

def cal_ordinate1(R, TL):
    return math.sqrt((R**2) - (7.5)**2) - math.sqrt((R**2) - (TL**2))

def cal_ordinate2(R, TL):
    return math.sqrt((R**2) - (2.5)**2) - math.sqrt((R**2) - (TL**2))

def cal_M1(ordinate1):
    return math.degrees(ordinate1 / increment)

def cal_M2(ordinate1, ordinate2):
    return math.degrees((ordinate2 - ordinate1) / increment)

def cal_X(direction, ordinate1, ordinate2):
    X = []
    for i in range(increment):
        if i == 0:
            x = 0
        elif i == 1 or i == 4:
            x = ordinate1 if direction == -1 else -ordinate1
        elif i == 2 or i == 3:
            x = ordinate2 if direction == -1 else -ordinate2
        X.append(x)
    return X

def cal_Y(direction, M1, M2):
    Y = []
    for i in range(increment):
        if i == 0:
            y = M1 if direction == -1 else -M1
        elif i == 1:
            y = M2 if direction == -1 else -M2
        elif i == 2:
            y = 0
        elif i == 3:
            y = -M2 if direction == -1 else M2
        elif i == 4:
            y = -M1 if direction == -1 else M1
        Y.append(y)
    return Y

def cal_cant_5m(C_list, sta, sign):#5m캔트반환기
    current_curvetype = None
    for i in range(len(C_list) - 1):
        current_STA, current_R, current_cant = C_list[i]
        next_STA, next_R, next_cant = C_list[i + 1]
        
        # sta가 현재 구간 사이에 있는 경우 보간(interpolation)
        if current_STA == sta: 
            cant_difference = abs(next_cant - current_cant)
            cant_increment = cant_difference / increment
            if sign == -1:#좌향곡선

                if current_R < next_R and next_R != 0:
                    current_curvetype = 'SP-PC' #SP PC인경우
                elif current_R > next_R:
                    current_curvetype = 'CP-PS'  # CP-PS인경우
                elif current_R > next_R and next_R ==0:
                    current_curvetype = 'CP-PS'  #PS-직선인경우
            else:#우향곡선
                if current_R > next_R and next_R != 0:
                    current_curvetype = 'SP-PC' #SP PC인경우
                elif current_R > next_R:
                    current_curvetype = 'CP-PS'  # CP-PS인경우
                elif current_R > next_R and next_R ==0:
                    current_curvetype = 'CP-PS'  #PS-직선인경우
            if current_curvetype == 'SP-PC':
                return cant_increment * 1000 * sign
            else:
                return cant_increment * 1000 * -sign
        
    return 0

def cal_Z(first_cant, cant_increment, sign):
    Z = []
    first_cant *= 1000
    for i in range(increment):

        dest_cant = (first_cant +  i  * cant_increment)#mm단위 변환
        z = math.degrees(dest_cant /1500) #각도로 변환
        Z.append(z)
        
    return Z


def cal_mainlogic(curveinfo, C_list):
    freeobj = []
    for info in curveinfo:
        STA = info[0]
        R = info[1]
        C = info[2]
        sign = 1 if R >=0 else -1
        direction = cal_direction(R)
        IA = block_length / R if R != 0 else 0
        TL = R * math.tan(IA) / 2
        O1 = cal_ordinate1(R, TL) if R != 0 else 0
        O2 = cal_ordinate2(R, TL) if R != 0 else 0
        M1 = cal_M1(O1) if R != 0 else 0
        M2 = cal_M2(O1, O2) if R != 0 else 0
        x = cal_X(direction, O1, O2) if R != 0 else [0,0,0,0,0]
        y = cal_Y(direction, M1, M2) if R != 0 else [0,0,0,0,0]

        cant_increment = cal_cant_5m(C_list, STA, sign)
        z = cal_Z(C, cant_increment ,sign)
        stations = [STA + i * increment for i in range(increment)]

        for i in range(increment):
            
            freeobj.append([stations[i], x[i], y[i], z[i]])
        
    return freeobj

def create_freeobj(freeobj, structure_list,curve_info):
    content = []
    for sta, x, y, z in freeobj:
        current_structure = isbridge_tunnel(sta, structure_list)
        iscurve = check_sta_is_curve(sta, curve_info)

        if iscurve == '곡선':  
            if current_structure == '터널':
                freeobj_index = 473#콘크리트도상터널전차선x
            else:
                freeobj_index = 449#자갈도상신선전차선x
        else:
            freeobj_index = 499#Null.csv
        content.append(f'{sta},.freeobj 0;{freeobj_index};{x};0;{y};0;{z}\n')
        
    return content

def isbridge_tunnel(sta, structure_list):
    """sta가 교량/터널/토공 구간에 해당하는지 구분하는 함수"""
    for start, end in structure_list['bridge']:
        if start <= sta <= end:
            return '교량'
    
    for start, end in structure_list['tunnel']:
        if start <= sta <= end:
            return '터널'
    
    return '토공'

def check_sta_is_curve(current_sta, curveinfo):
    for i in range(len(curveinfo)-1):
        sta, R, c = curveinfo[i]
        NEXT_sta, NEXT_R, NEXT_c = curveinfo[i +1]
        if sta <=current_sta < NEXT_sta:
            if R != 0:
                return '곡선'
            else:
                return '직선'
        
# 실행
def load_structure_data():
    """구조물 데이터를 엑셀 파일에서 불러오는 함수"""
    openexcelfile = open_excel_file()
    if openexcelfile:
        return find_structure_section(openexcelfile)
    else:
        print("엑셀 파일을 선택하지 않았습니다.")
        return None

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


def save_files(content):
    save_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "freeobj.txt"), ("All files", "*.*")]
    )
    
    if not save_path:
        print("파일 저장이 취소되었습니다.")
        return

    # Modify content
    modified_content = modify_content(content)
    
    try:
        with open(save_path, 'w', encoding='utf-8') as f:
            for line in modified_content:
                f.write(line)  # Ensure each line ends with a newline character
        print(f'{save_path}파일이 성공적으로 저장되었습니다.')
    except Exception as e:
        print(f'파일 저장에 실패하였습니다: {e}')
        
def modify_content(contents):
    modified_contents = []
    for content in contents:
        parts = content.split(';')
        
        # Ensure there are enough parts to avoid IndexError
        if len(parts) > 4:
            # Extract the three values after 478;
            value1 = parts[2].strip()
            value2 = parts[4].strip()
            value3 = parts[6].strip()
            # Check if all three values are '0'
            if not (value1 == '0' and value2 == '0' and value3 == '0'):
                modified_contents.append(content)
                
    return modified_contents

def create_railtype(curveinfo, structure_list):
    railtype_list =[]
    for info in curveinfo:
        sta = info[0]
        R = info[1]
        c = info[2]
        currnet_structure = isbridge_tunnel(sta, structure_list)
        if R == 0:#직선
            if currnet_structure == '터널':
                railtype = 16#콘크리트도상 신선 전차선x
            else:
                railtype = 9#자갈도상 신선 전차선x
        else:
            railtype = 4
        railtype_list.append(f'{sta},.railtype 0;{railtype};\n')
        
    return railtype_list

def save_railtype(content):
    save_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "railtype.txt"), ("All files", "*.*")]
    )
    try:
        with open(save_path, 'w', encoding='utf-8') as f:
            for line in content:
                f.write(line)  # Ensure each line ends with a newline character
        print(f'{save_path}파일이 성공적으로 저장되었습니다.')
    except Exception as e:
        print(f'파일 저장에 실패하였습니다: {e}')

def main():
    lines = read_file()
    if not lines:
        return
    # 구조물 정보 로드
    structure_list = load_structure_data()
    if structure_list:
        print("구조물 정보가 성공적으로 로드되었습니다.")
    
    curveinfo = parsing_curveinfo(lines)
    C_list = extract_cant(curveinfo)
    freeobj = cal_mainlogic(curveinfo, C_list)
    content = create_freeobj(freeobj, structure_list, curveinfo)
    save_files(content)
    railtype = create_railtype(curveinfo, structure_list)
    save_railtype(railtype)
# Running the main function
if __name__ == "__main__":
    main()
