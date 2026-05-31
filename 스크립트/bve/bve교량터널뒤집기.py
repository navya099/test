import tkinter as tk
from tkinter import filedialog

import tkinter as tk
from tkinter import filedialog

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

    for block_index, block in enumerate(blocks):
        modified_block = [line for line in block if not line.startswith(",;")]  # ",;"로 시작하는 행은 걸러내고 나머지 행만 남김
        modified_block.reverse()  # 걸러낸 행을 제외한 나머지 행을 뒤집음

        

        # 줄의 마지막과 그 전 줄을 바꾸기
        for i in range(len(modified_block) - 1):  # 마지막 줄은 건너뜁니다.
            if not line.startswith(",;"):
                current_line_parts = modified_block[i].split(',', 1)  # 현재 줄을 쉼표(,)로 분할합니다.
                next_line_parts = modified_block[i + 1].split(',', 1)  # 다음 줄을 쉼표(,)로 분할합니다.

                # 현재 줄과 다음 줄의 마지막 부분을 서로 바꿉니다.
                if len(current_line_parts) > 1 and len(next_line_parts) > 1:
                    temp = current_line_parts[1]
                    current_line_parts[1] = next_line_parts[1]
                    next_line_parts[1] = temp

                    # 바꾼 내용을 다시 합쳐줍니다.
                    modified_block[i] = ','.join(current_line_parts)
                    modified_block[i + 1] = ','.join(next_line_parts)
                    
        # 기존 블록에서 ",;"로 시작하는 행의 위치를 찾아 그 자리에 걸러낸 행을 다시 넣음
        for i, line in enumerate(block):
            if line.startswith(",;"):
                modified_block.insert(i, line)
                
        block[:] = modified_block  # 블록을 수정된 블록으로 업데이트

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
    with open("reverse.txt", 'r', encoding='utf8') as f:
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
    with open("reverse.txt", 'w', encoding='utf8') as f:
        f.writelines(new_lines)
        
if __name__ == '__main__':
    input_station = int(input("원하는 시작 측점을 입력하세요: "))
    main()
