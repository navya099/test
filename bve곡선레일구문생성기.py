import tkinter as tk
from tkinter import filedialog, ttk
import math
import csv

# Global Variables
increment = 5  # Calculation interval, default 5

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

def cal_direction(R):
    return -1 if R < 0 else 1

def cal_ordinate1(R, TL):
    return math.sqrt((R**2) - (7.5)**2) - math.sqrt((R**2) - (TL**2))

def cal_ordinate2(R, TL):
    return math.sqrt((R**2) - (2.5)**2) - math.sqrt((R**2) - (TL**2))

def cal_M1(ordinate1):
    return math.degrees(ordinate1 / 5)

def cal_M2(ordinate1, ordinate2):
    return math.degrees((ordinate2 - ordinate1) / 5)

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

def cal_mainlogic(curveinfo):
    freeobj = []
    for info in curveinfo:
        STA = info[0]
        R = info[1]
        direction = cal_direction(R)
        IA = 25 / R if R != 0 else 0
        TL = R * math.tan(IA) / 2
        O1 = cal_ordinate1(R, TL) if R != 0 else 0
        O2 = cal_ordinate2(R, TL) if R != 0 else 0
        M1 = cal_M1(O1) if R != 0 else 0
        M2 = cal_M2(O1, O2) if R != 0 else 0
        x = cal_X(direction, O1, O2) if R != 0 else [0,0,0,0,0]
        y = cal_Y(direction, M1, M2) if R != 0 else [0,0,0,0,0]

        stations = [STA + i * 5 for i in range(increment)]
        
        for i in range(increment):
            
            freeobj.append([stations[i], x[i], y[i]])
        
    return freeobj

def create_freeobj(freeobj):
    content = []
    for sta, x, y in freeobj:
        freeobj_index = 478
        content.append(f'{sta},.freeobj 0;{freeobj_index};{x};;{y};;0\n')
        
    return content
    
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

def create_railtype(curveinfo):
    railtype_list =[]
    for info in curveinfo:
        sta = info[0]
        R = info[1]
        c = info[2]

        if R == 0:
            railtype = 0
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
    curveinfo = parsing_curveinfo(lines)
    freeobj = cal_mainlogic(curveinfo)
    content = create_freeobj(freeobj)
    save_files(content)
    railtype = create_railtype(curveinfo)
    save_railtype(railtype)
# Running the main function
if __name__ == "__main__":
    main()
