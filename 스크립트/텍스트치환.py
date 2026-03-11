import os

# 원본 파일 경로 리스트 만들기
namelist = ['FPW', '급전선', '무효용조가선', '무효용전차선']

input_files = [
    rf"D:\BVE\루트\Railway\Object\철도표준라이브러리\전철전력\공통\전선\{name}_13m.csv"
    for name in namelist
]

# 치환할 숫자 정의 (예: 13 → 1~62)
old_number = "13"

# 원본 파일 줄 단위 읽기
for input_file in input_files:
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 숫자 치환 및 여러 파일 저장
    for number in range(1, 64):  # 1 ~ 63까지
        if number in [13, 35, 40, 45, 50, 55, 60]:  # 이미 존재하는 숫자는 제외
            continue

        replaced_lines = []
        for line in lines:
            if line.startswith("AddVertex"):  # 특정 줄만 치환
                replaced_lines.append(line.replace(old_number, str(number)))
            else:
                replaced_lines.append(line)

        # 원본 파일명에서 name 추출
        base_name = os.path.basename(input_file).split("_")[0]  # FPW, 급전선 등
        output_file = rf"D:\BVE\루트\Railway\Object\철도표준라이브러리\전철전력\공통\전선\{base_name}_{number}m.csv"

        with open(output_file, "w", encoding="utf-8") as f:
            f.writelines(replaced_lines)

print("치환 완료! 여러 CSV 파일이 생성되었습니다.")