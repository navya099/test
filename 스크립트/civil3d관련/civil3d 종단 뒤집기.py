import pandas as pd
from tkinter import Tk, Label
from tkinterdnd2 import DND_FILES, TkinterDnD
import os

def parsing_excel(file):
    # Load the Excel file
    df = pd.read_excel(file)
    
     # Extract columns C and D (PVI 측점, PVI 표고)
    c_column = df.iloc[:, 2].astype(str).str.replace(r'[+m]', '', regex=True).astype(float).tolist()  # Column C (PVI 측점)
    d_column = df.iloc[:, 3].astype(str).str.replace(r'm', '', regex=True).astype(float).tolist()  # Column D (PVI 표고)

    # Check if column K exists and is not empty
    k_column = df.iloc[:, 10].astype(str).str.replace(r'm', '', regex=True).astype(float).tolist() # Column K (종단 원곡선 길이)
    
    data = {
        "PVI 측점": c_column,
        "PVI 표고": d_column,
        "종단 원곡선 길이": k_column
    }
    
    return data

def on_drop(event):
    # 드래그 앤 드롭된 파일 경로를 가져옵니다
    files = root.tk.splitlist(event.data)
    file_paths = [f for f in files if f.lower().endswith(('.xlsx'))]
    if not file_paths:
        label.config(text="xlsx 파일이 아닙니다.")
        return

    # 선택된 파일의 디렉토리 경로를 가져옵니다
    output_dir = os.path.dirname(file_paths[0])
    output_path = os.path.join(output_dir, "converted_reverse_profile.txt")

    # xls파일 파싱함수 호출
    data = parsing_excel(file_paths[0])

    # 데이터 처리
    processed_data = process_data(data)

    # Convert DataFrame to string without headers and index, replace NaN with 0
    processed_data_str = processed_data.fillna('').to_string(header=False, index=False)

    # Remove multiple spaces with a single space
    processed_data_str = '\n'.join([' '.join(line.split()) for line in processed_data_str.split('\n')])

    print(processed_data_str)

    # 결과를 파일에 저장
    try:
        with open(output_path, 'w') as f:
            f.write(processed_data_str)
        label.config(text=f"파일이 성공적으로 저장되었습니다: {output_path}")
    except Exception as e:
        label.config(text=f"파일을 저장하는데 실패했습니다: {str(e)}")

def process_data(data):
    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Reverse the DataFrame
    df_reversed = df.iloc[::-1].reset_index(drop=True)

    # Adjust the PVI 측점 column
    max_pvi_value = df_reversed["PVI 측점"].iloc[0]
    df_reversed["역방향 측점"] = max_pvi_value - df_reversed["PVI 측점"]

    # Create 역방향 fl column
    df_reversed["역방향 fl"] = df_reversed["PVI 표고"]

    # Remove "종단 원곡선 길이" for the first and last rows
    df_reversed.at[0, "종단 원곡선 길이"] = ''
    df_reversed.at[len(df_reversed) - 1, "종단 원곡선 길이"] = ''
    # Reorder columns
    df_reversed = df_reversed[["역방향 측점", "역방향 fl", "종단 원곡선 길이"]]

    return df_reversed

# TkinterDnD 창을 생성합니다
root = TkinterDnD.Tk()
root.title("종단 역변환 컨버터")

# 안내 레이블을 추가합니다
label = Label(root, text="xlsx 파일을 여기로 드래그 앤 드롭하세요")
label.pack(pady=20)

# 드래그 앤 드롭 이벤트 바인딩
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', on_drop)

# Tkinter 메인 루프 시작
root.mainloop()
