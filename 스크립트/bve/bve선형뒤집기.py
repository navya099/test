import os
import tkinter as tk
from tkinter import filedialog

# 측점 뒤집기 함수
# 측점 뒤집기 함수
def file_reverse():
    root = tk.Tk()
    
    file_path = filedialog.askopenfilename()  # 파일 다이얼로그로 파일 선택
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 빈 줄을 기준으로 각 블록을 분리합니다.
    blocks = []
    block = []
    for line in lines:
        if line.startswith("\n"):
            if block:
                blocks.append(block)
                block = []
        else:
            block.append(line)
    if block:
        blocks.append(block)

    for block in blocks:
        modified_block = [line for line in block if not line.startswith(",;")]  # ",;"로 시작하는 행은 걸러내고 나머지 행만 남김
        modified_block.reverse()  # 걸러낸 행을 제외한 나머지 행을 뒤집음

        # 기존 블록에서 ",;"로 시작하는 행의 위치를 찾아 그 자리에 걸러낸 행을 다시 넣음
        for i, line in enumerate(block):
            if line.startswith(",;"):
                modified_block.insert(i, line)

        block[:] = modified_block  # 블록을 수정된 블록으로 업데이트

        # ,;로 시작하지 않는 행의 뒷부분을 뒤집기
        for i, line in enumerate(block):
            if not line.startswith(",;"):
                parts = line.split(",", 1)
                if len(parts) > 1:
                    parts[1] = parts[1][::-1]  # 뒷부분을 뒤집기
                    block[i] = ",".join(parts)

    # 결과를 파일에 씁니다.
    with open("reverse.txt", "w", encoding='utf8') as f:
        for block in blocks:
            f.write("".join(block))

# 측점 찾기
def find_station():
    with open("reverse.txt",  'r', encoding='utf8') as f:
        lines = f.readlines()
    current_station = []
    
    for line in lines:
        if line.split(",")[0].isdigit():
            current_station.append(int(line.split(",")[0]))
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

def change_radius():
    with open("reverse.txt", 'r', encoding='utf8') as f:
        lines = f.readlines()

    updated_data = []  # 변경된 내용을 저장할 리스트

    for line in lines:
        parts = line.split('.CURVE ')
        if len(parts) > 1:  # '.CURVE'가 있는 라인인지 확인
            numbers = parts[1].split(';')
            if len(numbers) == 2:  # ';'로 분리된 부분이 두 개인지 확인
                num = numbers[0].strip()
                if num.replace('.', '', 1).replace('-', '', 1).isdigit():  # 숫자 확인
                    try:
                        value = float(num)
                        if value != 0:  # 0이 아닌 경우에만 부호 변경
                            new_value = -value
                            updated_line = parts[0] + '.CURVE ' + str(new_value) + ';' + numbers[1]
                            updated_data.append(updated_line)
                        else:
                            updated_data.append(line)  # 0인 경우에는 그대로 유지
                    except ValueError:
                        updated_data.append(line)
                else:
                    updated_data.append(line)
            else:
                updated_data.append(line)
        else:
            updated_data.append(line)
        
    # 변경된 내용을 파일에 쓰기
    with open("reverse.txt", 'w', encoding='utf8') as f:
        f.writelines(updated_data)

def main():
    file_reverse()
    
    # reverse.txt 파일 읽기
    with open("reverse.txt", 'r', encoding='utf8') as f:
        lines = f.readlines()
    
    # 측점 변환 및 새로운 라인 생성
    a = change_station()
    new_lines = []
    i = 0

    for line in lines:
        parts = line.split(",")
        if parts[0].isdigit():
            number = a[i]  # 현재 인덱스에 해당하는 측점 변환값을 더합니다.
            new_line = f"{number},{','.join(parts[1:])}"
            new_lines.append(new_line)
            i += 1
        else:
            new_line = line
            new_lines.append(new_line)

    

    

    # 변경된 내용 reverse.txt 파일에 쓰기
    with open("reverse.txt", 'w', encoding='utf8') as f:
        f.writelines(new_lines)

        # reverse.txt 파일 읽기
    with open("reverse.txt", 'r', encoding='utf8') as f:
        lines = f.readlines()

        # 각 줄의 뒷 부분을 전부 제거하고 이전 줄의 뒷부분에 삽입하기
    for i in range(len(lines)-1):
        if lines[i][0].isdigit():  # 숫자로 시작하는 경우에만 처리
            previous_value = lines[i + 1].split(',')[1].strip()  # strip()으로 공백 제거
            lines[i] = f"{lines[i].split(',')[0]},{previous_value}\n"
            # 마지막 줄 처리
        #숫자가 아닌 경우
        if not lines[i][0].isdigit():
            lines[i-1] = f"{lines[i-1].split(',')[0]},.CURVE 0;0\n"
            
    # 변경된 내용 reverse.txt 파일에 쓰기
    with open("reverse.txt", 'w', encoding='utf8') as f:
        f.writelines(lines)


    change_radius()
        
if __name__ == '__main__':
    input_station = int(input("원하는 시작 측점을 입력하세요: "))
    main()
