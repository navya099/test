from tkinter.filedialog import askopenfilename, asksaveasfilename

# 원본 파일 선택
file_path = askopenfilename(title="원본 텍스트 파일 선택")
if not file_path:
    raise FileNotFoundError('파일이 선택되지 않았습니다.')

# 기준 STATION 값 입력
station_limit = int(input("기준 STATION 값을 입력하세요: ").strip())

# 결과 저장할 파일 선택
output_file = asksaveasfilename(title="결과 저장할 파일 이름 지정", defaultextension=".txt")
if not output_file:
    raise FileNotFoundError('저장 파일이 선택되지 않았습니다.')

# 파일에서 텍스트 읽기
with open(file_path, "r", encoding="utf-8") as f:
    input_text = f.read()

output_lines = []
for line in input_text.splitlines():
    # 빈 줄이나 주석 라인은 그대로 유지
    if not line.strip() or line.strip().startswith(",;"):
        output_lines.append(line)
        continue

    # 첫 번째 필드(Station 값) 추출
    first_field = line.split(",")[0]
    try:
        station_value = int(first_field)
    except ValueError:
        station_value = None

    # 기준 이하만 남기기
    if station_value is not None and station_value <= station_limit:
        output_lines.append(line)

result = "\n".join(output_lines)

# 결과를 새 파일로 저장
with open(output_file, "w", encoding="utf-8") as f:
    f.write(result)

print(f"✅ 변환 완료! 결과가 '{output_file}' 파일에 저장되었습니다.")
