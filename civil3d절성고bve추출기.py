import pandas as pd
from tkinter import Tk, filedialog, Label, Button
import os
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Union

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
        df = pd.read_excel(filepaths)
        return df



# --- 명령 클래스 정의 ---
@dataclass
class BVECommand:
    trackposition: float
    def to_bve(self) -> str:
        raise NotImplementedError()

@dataclass
class Rail(BVECommand):
    rail_index: int
    x_offset: float
    y_offset: float
    obj_index: int

    def to_bve(self) -> str:
        return f"{self.trackposition},.rail {self.rail_index};{self.x_offset};{self.y_offset};{self.obj_index};"

@dataclass
class Ground(BVECommand):
    obj_index: int

    def to_bve(self) -> str:
        return f"{self.trackposition},.ground {self.obj_index};"

@dataclass
class Height(BVECommand):
    height: float

    def to_bve(self) -> str:
        return f"{self.trackposition},.height {self.height:.3f};"


# --- BVEData 클래스 정의 ---
class BVEData:
    def __init__(self):
        self.blocks = [Block()]

class Block:
    def __init__(self):
        self.track_position = 0.0
        self.rails = []
        self.ground = None
        self.height = None


def load_xls(root):
    file_path = filedialog.askopenfilename(title="엑셀 파일을 선택하세요")
    if not file_path:
        print("파일 선택이 취소되었습니다.")
        return
    return file_path

def save_txt(bve_text_dict: dict):
    # 디렉토리 선택 다이얼로그
    save_dir = filedialog.askdirectory(title="저장할 폴더 선택")
    if not save_dir:
        print("저장 취소됨.")
        return

    try:
        # 딕셔너리의 각 항목에 대해 텍스트 파일로 저장
        for filename, block_data_list in bve_text_dict.items():
            # 각 키별로 하나의 텍스트 파일 생성
            file_path = os.path.join(save_dir, f"{filename}.txt")

            with open(file_path, 'w', encoding='utf-8') as f:
                for block_data in block_data_list:
                    f.write(block_data + '\n')  # 각 블록의 데이터를 기록

            print(f"파일 저장 완료: {file_path}")
    except Exception as e:
        print(f"파일 저장 오류: {e}")

def process_dataframe(df, bvedata: BVEData):
    rows = df.iloc[16:]

    # 필요한 block 수만큼 생성
    while len(bvedata.blocks) < len(rows):
        bvedata.blocks.append(Block())

    # 인덱스 정의
    left_nori_idx = 200 # 좌측사면 인덱스
    right_nori_idx = 201 # 우측사면 인덱스
    left_nori_obj_idx = 87 # 좌측사면오브젝트 인덱스
    right_nori_obj_idx = 88 # 우측사면 오브젝트 인덱스

    for i, (_, row) in enumerate(rows.iterrows()):
        trackposition = row[1] if not pd.isna(row[1]) else 0.0
        ground_elevation = row[4] if not pd.isna(row[4]) else 0.0
        rail_elevation = row[5] if not pd.isna(row[5]) else 0.0
        elevation_diff = ground_elevation - rail_elevation

        bvedata.blocks[i].track_position = trackposition
        bvedata.blocks[i].rails.append(Rail(trackposition=trackposition,
                                            rail_index=left_nori_idx,
                                            x_offset=-elevation_diff * 1.5,
                                            y_offset=-elevation_diff,
                                            obj_index= left_nori_obj_idx
                                            )
                                       )
        bvedata.blocks[i].rails.append(Rail(trackposition=trackposition,
                                            rail_index=right_nori_idx,
                                            x_offset=elevation_diff * 1.5,
                                            y_offset=-elevation_diff,
                                            obj_index=right_nori_obj_idx
                                            )
                                       )


        # 절성고
        ground_indx = 0 if -elevation_diff > 0 else 3
        bvedata.blocks[i].ground = Ground(trackposition=trackposition,obj_index=ground_indx)
        bvedata.blocks[i].height = Height(trackposition=trackposition,height=-elevation_diff)
    return bvedata

def create_bve_systax(bvedata):
    bve_text_dict = {}
    for i, block in enumerate(bvedata.blocks):
        # 각 블록에 대한 데이터를 키별로 저장
        bve_text_dict['좌측사면'] = bve_text_dict.get('좌측사면', []) + [block.rails[0].to_bve()]
        bve_text_dict['우측사면'] = bve_text_dict.get('우측사면', []) + [block.rails[1].to_bve()]
        bve_text_dict['ground'] = bve_text_dict.get('ground', []) + [block.ground.to_bve()]
        bve_text_dict['절성고'] = bve_text_dict.get('절성고', []) + [block.height.to_bve()]
    return bve_text_dict

def convert_dataframe_to_raildata(xls_files):
    dataframe = Parser.read_xls_files(xls_files)
    df = Parser.preprocess(dataframe)
    bvedata = BVEData()
    bvedata = process_dataframe(df, bvedata)
    bve_text_list = create_bve_systax(bvedata)

    return bve_text_list


def run(file_path):
    raildata = convert_dataframe_to_raildata(file_path)
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
    root.title("BVE 절성고 파일 생성기")

    # GUI 구성
    label = Label(root, text="엑셀 파일을 선택하고 처리 버튼을 클릭하세요.", width=50, height=2)
    label.pack(pady=20)

    run_button = Button(root, text="파일 처리 시작", command=lambda: on_run_button_click(root, label), width=20)
    run_button.pack(pady=10)

    root.mainloop()

if __name__ == '__main__':
    main()
