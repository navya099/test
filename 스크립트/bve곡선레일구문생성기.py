import tkinter as tk
from tkinter import filedialog, ttk, messagebox, simpledialog
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
            station = float(line[0])
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

# 좌표 Y축 거리 차이 계산
def cal_ordinate1(R, TL):
    A = TL / 5
    B = A * 3
    return math.sqrt((R**2) - (B)**2) - math.sqrt((R**2) - (TL**2))

def cal_ordinate2(R, TL):
    C = TL / 5
    return math.sqrt((R**2) - (C)**2) - math.sqrt((R**2) - (TL**2))

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

def create_freeobj(freeobj, structure_list,curve_info, index_dict: dict):
    content = []
    for sta, x, y, z in freeobj:
        current_structure = isbridge_tunnel(sta, structure_list)
        iscurve = check_sta_is_curve(sta, curve_info)

        if iscurve == '곡선':  
            if current_structure == '터널':
                freeobj_index = index_dict['freeobj']['곡선']['터널']['콘크리트도상']
            elif current_structure == '토공' or current_structure == '교량':
                freeobj_index = index_dict['freeobj']['곡선']['토공']['자갈도상']
            else:
                raise KeyError(f'올바르지 않은 구조물 {current_structure}')
        else:
            freeobj_index = index_dict['freeobj']['직선']#Null.csv
        content.append(f'{sta},.freeobj 0;{freeobj_index};{x};0;{y};0;{z}\n')
        
    return content

def isbridge_tunnel(sta, structure_list):
    """sta가 교량/터널/토공 구간에 해당하는지 구분하는 함수"""
    for name, start, end in structure_list['bridge']:
        if start <= sta <= end:
            return '교량'
    
    for name, start, end in structure_list['tunnel']:
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


def save_files(content, save_path):

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

def create_railtype(curveinfo, structure_list, index_dict: dict):
    railtype_list =[]
    for info in curveinfo:
        sta = info[0]
        R = info[1]
        c = info[2]
        currnet_structure = isbridge_tunnel(sta, structure_list)
        if R == 0:  # 직선
            if currnet_structure == '터널':
                railtype = index_dict['railtype']['직선']['터널']['콘크리트도상']#콘크리트도상전차선x
            else:
                railtype = index_dict['railtype']['직선']['토공']['자갈도상']  # 자갈도상 신선 전차선x
        else:
            railtype = index_dict['railtype']['곡선']
        railtype_list.append(f'{sta},.railtype 0;{railtype};\n')
        
    return railtype_list

def save_railtype(content, save_path):
    try:
        with open(save_path, 'w', encoding='utf-8') as f:
            for line in content:
                f.write(line)  # Ensure each line ends with a newline character
        print(f'{save_path}파일이 성공적으로 저장되었습니다.')
    except Exception as e:
        print(f'파일 저장에 실패하였습니다: {e}')

def get_default_values(alignment_type):
    # alignmenttype별 기본값 딕셔너리
    default_values = {
        '도시철도': {
            'freeobj': {
                '곡선': {
                    '터널': {
                        '콘크리트도상': 473,
                        '자갈도상': 228,
                    },
                    '토공': {
                        '콘크리트도상': 465,
                        '자갈도상': 228,
                    },
                    '교량': {
                        '콘크리트도상': 465,
                        '자갈도상': 228,
                    }
                },
                '직선': 499,
            },
            'railtype': {
                '곡선': 4,
                '직선': {
                    '터널': {
                        '콘크리트도상': 25,
                        '자갈도상': 17,
                    },
                    '토공': {
                        '콘크리트도상': 23,
                        '자갈도상': 9,
                    },
                    '교량': {
                        '콘크리트도상': 23,
                        '자갈도상': 9,
                    }
                }
            }
        },
        '일반철도': {
            'freeobj': {
                '곡선': {
                    '터널': {
                        '콘크리트도상': 473,
                        '자갈도상': 228,
                    },
                    '토공': {
                        '콘크리트도상': 465,
                        '자갈도상': 449,
                    },
                    '교량': {
                        '콘크리트도상': 465,
                        '자갈도상': 449,
                    }
                },
                '직선': 499,
            },
            'railtype': {
                '곡선': 4,
                '직선': {
                    '터널': {
                        '콘크리트도상': 25,
                        '자갈도상': 17,
                    },
                    '토공': {
                        '콘크리트도상': 23,
                        '자갈도상': 9,
                    },
                    '교량': {
                        '콘크리트도상': 23,
                        '자갈도상': 9,
                    }
                }
            }
        },
        '준고속철도': {
            'freeobj': {
                '곡선': {
                    '터널': {
                        '콘크리트도상': 473,
                        '자갈도상': 228,
                    },
                    '토공': {
                        '콘크리트도상': 465,
                        '자갈도상': 449,
                    },
                    '교량': {
                        '콘크리트도상': 465,
                        '자갈도상': 449,
                    }
                },
                '직선': 499,
            },
            'railtype': {
                '곡선': 4,
                '직선': {
                    '터널': {
                        '콘크리트도상': 25,
                        '자갈도상': 17,
                    },
                    '토공': {
                        '콘크리트도상': 23,
                        '자갈도상': 9,
                    },
                    '교량': {
                        '콘크리트도상': 23,
                        '자갈도상': 9,
                    }
                }
            }
        },
        '고속철도': {
            'freeobj': {
                '곡선': {
                    '터널': {
                        '콘크리트도상': 658,
                        '자갈도상': 659,
                    },
                    '교량': {
                        '콘크리트도상': 657,
                        '자갈도상': 656,
                    },
                    '토공': {
                        '콘크리트도상': 657,
                        '자갈도상': 656,
                    },
                },
                '직선': 499,
            },
            'railtype': {
                '곡선': 4,
                '직선': {
                    '터널': {
                        '콘크리트도상': 114,
                        '자갈도상': 115,
                    },
                    '토공':{
                        '콘크리트도상': 12,
                        '자갈도상': 7,
                    },
                    '교량': {
                        '콘크리트도상': 12,
                        '자갈도상': 7,
                    }
                }
            }
        }
    }

    # 전달받은 alignmenttype에 맞는 기본값 선택
    defaults = default_values.get(alignment_type)
    if defaults is None:
        raise ValueError(f"알 수 없는 노선 유형: {alignment_type}")
    return defaults


# 2. UI 핸들러 (관심사 분리)
def ask_user(prompt, default_value):
    value = simpledialog.askstring("입력", f"{prompt} (기본값: {default_value})")
    if value is None:  # 취소
        return None
    return int(value) if value.strip() else default_value

def ask_user_cui(prompt, default_value):
    """콘솔에서 사용자 입력을 받는 핸들러"""
    value = input(f"{prompt} (기본값: {default_value}) 입력: ")
    if not value.strip():  # 입력이 없으면 기본값 사용
        return default_value
    try:
        return int(value)
    except ValueError:
        print("[경고] 숫자가 아닙니다. 기본값을 사용합니다.")
        return default_value

# 3. 사용자 입력 적용
def apply_user_input(defaults, ui_handler=ask_user):
    v1 = ui_handler("freeobj 곡선-터널-콘크리트도상", defaults['freeobj']['곡선']['터널']['콘크리트도상'])
    if v1 is None: return None
    v2 = ui_handler("freeobj 곡선-터널-자갈도상", defaults['freeobj']['곡선']['터널']['자갈도상'])
    if v2 is None: return None
    v3 = ui_handler("freeobj 직선", defaults['freeobj']['직선'])
    if v3 is None: return None

    v4 = ui_handler("railtype 곡선", defaults['railtype']['곡선'])
    if v4 is None: return None
    v5 = ui_handler("railtype 직선-터널-콘크리트도상", defaults['railtype']['직선']['터널']['콘크리트도상'])
    if v5 is None: return None
    v6 = ui_handler("railtype 직선-터널-자갈도상", defaults['railtype']['직선']['터널']['자갈도상'])
    if v6 is None: return None

    return {
        'freeobj': {
            '곡선': {'터널': {'콘크리트도상': v1, '자갈도상': v2}},
            '직선': v3,
        },
        'railtype': {
            '곡선': v4,
            '직선': {'터널': {'콘크리트도상': v5, '자갈도상': v6}},
        }
    }

# 4. 최종 사용
def preprocess_input_index(alignment_type, mode="gui"):
    defaults = get_default_values(alignment_type)
    if mode == "gui":
        return apply_user_input(defaults, ui_handler=ask_user)      # GUI 모드
    elif mode == "cui":
        return apply_user_input(defaults, ui_handler=ask_user_cui)  # CUI 모드
    elif mode == 'default':
        return defaults
    else:
        raise ValueError("지원하지 않는 모드입니다.")


class FreeobjApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FreeObj 자동 생성기")
        self.geometry("600x400")
        self.alignment_type = ''
        self.create_widgets()

    def create_widgets(self):
        label = ttk.Label(self, text="BVE FreeObj 자동 생성 프로그램", font=("Arial", 14, "bold"))
        label.pack(pady=20)

        self.log_box = tk.Text(self, height=15, wrap=tk.WORD, font=("Consolas", 10))
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        run_button = ttk.Button(self, text="FreeObj 생성 실행", command=self.run_main)
        run_button.pack(pady=10)

    def log(self, message):
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)



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
            self.process_interval()
            index_dict  = preprocess_input_index(self.alignment_type)
            self.log("파일을 읽는 중...")
            lines = read_file()
            if not lines:
                self.log("파일 없음 또는 불러오기 실패.")
                return

            self.log("구조물 정보 로드 중...")
            structure_list = load_structure_data()
            if structure_list:
                self.log("구조물 정보가 성공적으로 로드되었습니다.")

            self.log("곡선 정보 파싱 중...")
            curveinfo = parsing_curveinfo(lines)

            self.log("캔트 정보 추출 중...")
            C_list = extract_cant(curveinfo)

            self.log("FreeObj 계산 중...")
            freeobj = cal_mainlogic(curveinfo, C_list)

            self.log("FreeObj 생성 중...")
            content = create_freeobj(freeobj, structure_list, curveinfo, index_dict)
            save_files(content)
            self.log("FreeObj 저장 완료!")

            self.log("Railtype 생성 중...")
            railtype = create_railtype(curveinfo, structure_list, index_dict)
            save_railtype(railtype)
            self.log("Railtype 저장 완료!")

            messagebox.showinfo("완료", "FreeObj 및 RailType 생성이 완료되었습니다.")
        except Exception as e:
            self.log(f"[오류] {str(e)}")
            messagebox.showerror("오류", f"실행 중 오류 발생:\n{e}")


if __name__ == "__main__":
    app = FreeobjApp()
    app.mainloop()

