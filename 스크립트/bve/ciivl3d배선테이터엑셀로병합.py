import pandas as pd
from tkinter.filedialog import askopenfilename, asksaveasfilename

# 엑셀 파일 선택
excel_file = askopenfilename(title="엑셀 파일 선택", filetypes=[("Excel files", "*.xlsx")])
if not excel_file:
    raise FileNotFoundError("엑셀 파일이 선택되지 않았습니다.")

# 결과 TXT 파일 지정
output_file = asksaveasfilename(title="저장할 TXT 파일 이름 지정", defaultextension=".txt")
if not output_file:
    raise FileNotFoundError("저장 파일이 선택되지 않았습니다.")

# 엑셀 파일 읽기 (모든 시트)
xls = pd.ExcelFile(excel_file)

output_lines = []
for sheet_name in xls.sheet_names:
    # 시트별 주석 추가
    output_lines.append(f",;{sheet_name}")

    df = pd.read_excel(excel_file, sheet_name=sheet_name)

    # 각 행을 지정된 양식으로 변환
    for _, row in df.iterrows():
        base_station = row.get("BaseStation", "")
        rail_index = row.get("Railindex", "")
        offset_x = row.get("OffsetX", "")
        offset_z = row.get("OffsetZ", "")

        # 문자열 포맷
        line = f"{base_station},.rail {rail_index};{offset_x};{offset_z}"
        output_lines.append(line)

# 결과 TXT 파일 저장
with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print(f"✅ 변환 완료! 모든 시트가 '{output_file}' 파일에 저장되었습니다.")
