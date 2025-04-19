import pandas as pd
from tkinter import Tk, filedialog, Label, Button
import os
from collections import defaultdict

class Parser:
    @staticmethod
    def preprocess(df):
        def clean_cell(x):
            if isinstance(x, str):
                x = x.replace('+', '')
                x = x.replace('미터', '')
                try:
                    return float(x)
                except ValueError:
                    return x  # 변환 불가능한 경우 원래 문자열 유지
            return x
        return df.applymap(clean_cell)

    @staticmethod
    def read_xls_files(filepaths) -> list[tuple[str, pd.DataFrame]]:
        dataframes = []
        for path in filepaths:
            try:
                df = pd.read_excel(path)
                dataframes.append((os.path.basename(path), df))  # 파일명과 df를 함께 저장
            except Exception as e:
                print(f"Error reading {path}: {e}")
        return dataframes

class BVEWriter:
    def __init__(self):
        self.rail_format = "{trackposition},.rail {rail_index};{x_offset};{y_offset};{rail_obj_index};"
        self.railend_format = "{trackposition},.railend {rail_index};"

    def create_rail(self, trackposition, rail_index, x_offset, y_offset, rail_obj_index):
        return self.rail_format.format(
            trackposition=trackposition,
            rail_index=rail_index,
            x_offset=x_offset,
            y_offset=y_offset,
            rail_obj_index=rail_obj_index
        )

    def create_railend(self, trackposition, rail_index):
        return self.railend_format.format(
            trackposition=trackposition,
            rail_index=rail_index
        )


def load_xls(root):
    folder_path = filedialog.askdirectory(title="엑셀 파일이 있는 폴더를 선택하세요")
    if not folder_path:
        print("폴더 선택이 취소되었습니다.")
        return
    return folder_path

def collect_xls_files(folder_path):
    xls_files = [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.lower().endswith(('.xls')) and not f.startswith('~$')
    ]
    print('폴더 내 엑셀파일 목록')
    for i, file in enumerate(xls_files):
        print(f'{i} = {file}')
    return xls_files

def save_txt(data: dict):
    save_file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    if not save_file_path:
        print("저장 취소됨.")
        return

    try:
        with open(save_file_path, 'w', encoding='utf-8') as f:
            for filename, lines in data.items():
                f.write(f",;##### {filename} #####\n")
                for line in lines:
                    f.write(line + '\n')
                f.write("\n")
        print(f"파일 저장 완료: {save_file_path}")
    except Exception as e:
        print(f"파일 저장 오류: {e}")

def create_rail_or_railend(df, bvewriter, row, railindex, is_first_line, is_last_line):
    trackposition = row[0] if not pd.isna(row[0]) else 0.0
    mode = 0 if df.shape[1] == 6 else 1
    if mode == 0:
        x_offset = row[4] if not pd.isna(row[4]) else 0.0
        y_offset = row[5] if not pd.isna(row[5]) else 0.0
    else:
        x_offset = row[2] if not pd.isna(row[2]) else 0.0
        y_offset = 0
    if is_last_line:
        return bvewriter.create_railend(trackposition, railindex)
    else:
        rail_obj_index = '' if not is_first_line else 0
        return bvewriter.create_rail(trackposition, railindex, x_offset, y_offset, rail_obj_index)

def process_dataframe(df, bvewriter, railindex):
    rail_data = []
    rows = df.iloc[9:]
    mode = 0 if df.shape[1] == 6 else 1
    is_first_line = True
    for idx, (i, row) in enumerate(rows.iterrows()):
        is_last_line = idx == len(rows) - 1
        rail_text = create_rail_or_railend(df, bvewriter, row, railindex, is_first_line, is_last_line)
        rail_data.append(rail_text)
        is_first_line = False
    return rail_data

def convert_dataframe_to_raildata(xls_files):
    dataframes = Parser.read_xls_files(xls_files)
    bvewriter = BVEWriter()

    railindex = 2
    raildata = defaultdict(list)

    for filename, df in dataframes:
        #df 전처리
        df = Parser.preprocess(df)
        rail_data = process_dataframe(df, bvewriter, railindex)
        raildata[filename].extend(rail_data)
        railindex += 1

    return raildata


def run(folder_path):
    xls_files = collect_xls_files(folder_path)
    raildata = convert_dataframe_to_raildata(xls_files)
    return raildata

def on_run_button_click(root, label):
    folder_path = load_xls(root)
    if folder_path:
        label.config(text="파일 처리 중...")
        raildata = run(folder_path)
        save_txt(raildata)
        label.config(text="파일 저장 완료!")

def main():
    root = Tk()
    root.title("BVE 배선파일 생성기")

    # GUI 구성
    label = Label(root, text="엑셀 파일을 선택하고 처리 버튼을 클릭하세요.", width=50, height=2)
    label.pack(pady=20)

    run_button = Button(root, text="파일 처리 시작", command=lambda: on_run_button_click(root, label), width=20)
    run_button.pack(pady=10)

    root.mainloop()

if __name__ == '__main__':
    main()
