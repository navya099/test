import tkinter as tk
from tkinter import filedialog

def file_reverse():
    root = tk.Tk()
    file_path = filedialog.askopenfilename()  # 파일 다이얼로그로 파일 선택

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 뒤집힌 데이터를 담을 리스트
    reversed_lines = list(reversed(lines))

    updated_lines = []
    for line in reversed_lines:
        parts = line.split('.pitch ')
        if len(parts) > 1:
            numbers = parts[1].split()
            if numbers:
                num = numbers[0]
                # 부호와 숫자 확인
                num = num.split()[0]
                if num.startswith('-') and num[1:].replace('.', '', 1).isdigit():  
                    num = float(num)  # 문자열을 부동 소수점으로 변환
                    updated_num = -num  # 부호 변경
                    updated_line = f"{parts[0]}.pitch {updated_num}\n"
                    updated_lines.append(updated_line)
                elif num.replace('.', '', 1).isdigit():
                    num = float(num)
                    updated_num = -num  # 부호 변경
                    updated_line = f"{parts[0]}.pitch {updated_num}\n"
                    updated_lines.append(updated_line)
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)
    
    # 결과를 파일에 씁니다. (reversed_lines를 사용해야 함)
    with open("reversed_pitch.txt", "w", encoding='utf8') as f:
        f.writelines(updated_lines)

# 측점 찾기
def find_station():
    with open("reversed_pitch.txt",  'r', encoding='utf8') as f:
        lines = f.readlines()
    current_station = []
    
    for line in lines:
        if line.split(",")[0].replace('.', '', 1).isdigit():
            current_station.append(float(line.split(",")[0]))
        elif line.strip() == "":
            continue

    last_station = max(current_station)
    
    return current_station, last_station

#측점 변환
def change_station():
    current_station, last_station = find_station()
    change_station = []
    unit = []
    
    for i in range(len(current_station)):
        unit.append((last_station - current_station[i]) // 25)
        change_station.append(input_station+unit[i]*25)
    return change_station

def main():
    file_reverse()
    
    # reverse.txt 파일 읽기
    with open("reversed_pitch.txt", 'r', encoding='utf8') as f:
        lines = f.readlines()
    
    # 측점 변환 및 새로운 라인 생성
    a = change_station()
    new_lines = []
    i = 0

    for line in lines:
        parts = line.split(",")
        if parts[0].replace('.', '', 1).isdigit():
            try:
                float(parts[0])
                number = a[i]  # 현재 인덱스에 해당하는 측점 변환값을 더합니다.
                new_line = f"{number},{','.join(parts[1:])}"
                new_lines.append(new_line)
                i += 1
            except ValueError:
                new_lines.append(line)
        else:
            new_lines.append(line)

    
    # 변경된 내용 reverse.txt 파일에 쓰기
    with open("reversed_pitch.txt", 'w', encoding='utf8') as f:
        f.writelines(new_lines)

        # reverse.txt 파일 읽기
    with open("reversed_pitch.txt", 'r', encoding='utf8') as f:
        lines = f.readlines()

        # 각 줄의 뒷 부분을 전부 제거하고 이전 줄의 뒷부분에 삽입하기
    for i in range(len(lines)-1):
        if lines[i][0].isdigit():  # 숫자로 시작하는 경우에만 처리
            previous_value = lines[i + 1].split(' ')[1]
            lines[i] = f"{lines[i].split(' ')[0]} {previous_value}"
            
    # 변경된 내용 reverse.txt 파일에 쓰기
    with open("reversed_pitch.txt", 'w', encoding='utf8') as f:
        f.writelines(lines)
        
if __name__ == '__main__':
    input_station = 0
    main()
