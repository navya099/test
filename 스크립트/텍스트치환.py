import os

def read_lines(input_file):
    # 원본 파일 줄 단위 읽기
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return lines

def replace_csv_file_length_text(old_text:str, new_text: str, lines: list[str]):
    # 숫자 치환 및 여러 파일 저장

        replaced_lines = []
        for line in lines:
            if line.startswith("AddVertex"):  # 특정 줄만 치환
                replaced_lines.append(line.replace(old_text, new_text))
            else:
                replaced_lines.append(line)
        return replaced_lines

def save_file(output_file, lines):
    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(lines)

def main():
    # 원본 파일 경로 리스트 만들기
    namelist = ['FPW', '급전선', '무효용조가선', '무효용전차선']
    #소스 파일
    input_files = [
        rf"D:\BVE\루트\Railway\Object\철도표준라이브러리\전철전력\공통\전선\{name}_base.csv"
        for name in namelist
    ]
    #실행
    for input_file in input_files:
        lines = read_lines(input_file)
        base_name = os.path.basename(input_file).split("_")[0]  # FPW, 급전선 등
        for number in range(1, 64):  # 1 ~ 63까지
            replaced_lines = replace_csv_file_length_text(
                old_text='13',
                new_text=str(number),
                lines=lines
            )
            output_file = rf"D:\BVE\루트\Railway\Object\철도표준라이브러리\전철전력\공통\전선\{base_name}_{number}m.csv"
            save_file(output_file, replaced_lines)

if __name__ == "__main__":
    main()