import pandas as pd
import os
from tkinter.filedialog import askopenfilenames, asksaveasfilename

# 여러 CSV 파일 선택
file_paths = askopenfilenames(title="CSV 파일들을 선택하세요", filetypes=[("CSV files", "*.csv")])
if not file_paths:
    raise FileNotFoundError("CSV 파일이 선택되지 않았습니다.")

# 결과 저장할 엑셀 파일 지정
output_file = asksaveasfilename(title="저장할 엑셀 파일 이름 지정", defaultextension=".xlsx")
if not output_file:
    raise FileNotFoundError("저장 파일이 선택되지 않았습니다.")

# 새 ExcelWriter 생성
with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    for file_path in file_paths:
        # 파일 이름에서 시트 이름 추출
        sheet_name = os.path.splitext(os.path.basename(file_path))[0]

        # CSV 읽기
        df = pd.read_csv(file_path)

        # 필요한 열만 추출 (BaseStation, OffsetX, OffsetZ)
        new_df = df[["BaseStation", "OffsetX", "OffsetZ"]]

        # 중간에 빈 열 2개 추가 (열 이름은 임시로 지정)
        new_df.insert(1, "Railindex", "")

        # 시트에 쓰기
        new_df.to_excel(writer, sheet_name=sheet_name, index=False)

print(f"✅ 변환 완료! 결과가 '{output_file}' 파일에 저장되었습니다.")
