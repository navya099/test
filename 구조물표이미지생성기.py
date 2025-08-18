import csv
from dataclasses import dataclass
from enum import Enum
from tkinter import filedialog, ttk, messagebox, simpledialog
import tkinter as tk
from PIL import Image, ImageDraw, ImageFont
import os
import pandas as pd
import math
import re
import textwrap
import fitz  # pymupdf
import matplotlib.pyplot as plt
import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import numpy as np
import shutil
import os

'''
xlsx 구조물 파일을 바탕으로 구조물표를 설치하는 프로그램
-made by dger -
VER 2025.08.18
'''

class StructureDATA:
    def __init__(self, name: str, start_station: float, end_station: float, length: float):
        self.name = name
        self.start_station = start_station
        self.end_station = end_station
        self.length = length

class Bridge(StructureDATA):
    pass
class Tunnel(StructureDATA):
    pass


def read_file(title):
    file_path = filedialog.askopenfilename(
        title=title,
        defaultextension=".xlsx",
        filetypes=[
            ("모든 엑셀 파일", "*.xlsx"),
            ("모든 파일", "*.*")
        ]
    )

    if not file_path:
        print("[안내] 파일 선택이 취소되었습니다.")
        return []

    print("[선택된 파일]:", file_path)
    return file_path

    
def copy_and_export_csv(open_filename='SP1700', output_filename='IP1SP',new_text='', source_directory='', work_directory=''):
    # Define the input and output file paths
    open_file = source_directory + open_filename + '.csv'
    output_file = work_directory + output_filename + '.csv'
    
    # List to store modified lines
    new_lines = []
        
    # Open the input file for reading
    with open(open_file, 'r', encoding='utf-8') as file:
        # Iterate over each line in the input file
        for line in file:
            # Replace 'LoadTexture, SP.png,' with 'LoadTexture, output_filename.png,' if found
            if f'LoadTexture, {open_filename}.png,' in line:
                line = line.replace(f'LoadTexture, {open_filename}.png,', f'LoadTexture, {output_filename}.png,')
     
            # Append the modified line to the new_lines list
            new_lines.append(line)
    
    # Open the output file for writing the modified lines
    with open(output_file, 'w', encoding='utf-8') as file:
        # Write the modified lines to the output file
        file.writelines(new_lines)

    return output_file


#클래스
def replace_text_in_dxf(file_path, modifed_path, new_text1, new_text2):
    """DXF 파일의 특정 텍스트를 새 텍스트로 교체하는 함수"""
    #구조물 연장 flaot을 str로 형변환
    length_str = str(int((new_text2)))
    try:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()

        # 🟢 특정 레이어의 MTEXT 엔티티 찾아서 교체
        for entity in msp.query("MTEXT"):
            if entity.dxf.layer == "구조물명":
                entity.text = "\P".join(list(new_text1))
            if len(new_text1) == 2:  # 이가
                entity.dxf.char_height = 200
            elif len(new_text1) == 3:  # 봉산교
                entity.dxf.char_height = 130
            elif len(new_text1) == 4:  # 지산천교
                entity.dxf.char_height = 100
            elif len(new_text1) == 5:
                entity.dxf.char_height = 77
            elif len(new_text1) == 6:
                entity.dxf.char_height = 65
            else:
                entity.dxf.char_height = 1

        # 🟢 특정 레이어의 TEXT 엔티티 찾아서 교체
        for entity in msp.query("TEXT"):
            if entity.dxf.layer == "연장":
                entity.dxf.text = length_str + 'M'


        # 변경된 DXF 저장
        doc.saveas(modifed_path)
        print("✅ 텍스트 교체 완료")
        return True

    except Exception as e:
        print(f"❌ DXF 텍스트 교체 실패: {e}")
        return False


class DXF2IMG:
    """DXF 파일을 이미지로 변환하는 클래스"""
    default_img_format = '.png'
    default_img_res = 96

    def convert_dxf2img(self, file_paths, img_format=default_img_format, img_res=default_img_res):
        """DXF를 이미지(PNG)로 변환하는 함수"""
        output_paths = []
        for file_path in file_paths:
            if not os.path.exists(file_path):
                print(f"❌ 파일을 찾을 수 없음: {file_path}")
                continue

            try:
                doc = ezdxf.readfile(file_path)
                msp = doc.modelspace()
                
                # DXF 파일 검증
                auditor = doc.audit()
                if auditor.has_errors:
                    print(f"⚠️ DXF 파일에 오류가 있음: {file_path}")
                    continue

                # Matplotlib 설정
                fig, ax = plt.subplots(figsize=(10, 10))
                ax.set_axis_off()  # 축 제거

                # DXF 렌더링
                ctx = RenderContext(doc)
                out = MatplotlibBackend(ax)
                Frontend(ctx, out).draw_layout(msp, finalize=True)

                # 파일 이름 설정 및 저장 경로 지정
                img_name = re.sub(r"\.dxf$", "", os.path.basename(file_path), flags=re.IGNORECASE)
                output_path = os.path.join(os.path.dirname(file_path), f"{img_name}{img_format}")

                # 이미지 저장
                fig.savefig(output_path, dpi=img_res, bbox_inches='tight', pad_inches=0)
                plt.close(fig)  # 메모리 해제

                print(f"✅ 변환 완료: {output_path}")
                output_paths.append(output_path)

            except Exception as e:
                print(f"❌ 변환 실패: {file_path} - {str(e)}")
        
        return output_paths

    def trim_and_resize_image(self, input_path, output_path, target_size=(500, 300)):
        """bbox 없이 이미지 여백을 직접 제거하고 500x300 크기로 조정"""
        try:
            img = Image.open(input_path).convert("RGB")
            np_img = np.array(img)

            # 흰색 배경 탐색 (흰색 또는 거의 흰색인 부분 제외)
            mask = np.any(np_img < [250, 250, 250], axis=-1)

            # 유효한 영역 찾기
            coords = np.argwhere(mask)
            if coords.size == 0:
                print("❌ 유효한 이미지 내용을 찾을 수 없음")
                return

            y_min, x_min = coords.min(axis=0)
            y_max, x_max = coords.max(axis=0)

            # 이미지 자르기 (bbox 사용하지 않음)
            cropped_img = img.crop((x_min, y_min, x_max, y_max))

            # 크기 조정 (500x300)
            resized_img = cropped_img.resize(target_size, Image.LANCZOS)
            resized_img.save(output_path)
            print(f"✅ 여백 제거 및 크기 조정 완료: {output_path}")

        except Exception as e:
            print(f"❌ 이미지 처리 실패: {e}")    
#######이미지 생성 로직 끝

def process_dxf_image(source_directory, work_directory, new_text1, new_text2):
    """DXF 파일 수정 및 이미지 변환"""
    file_path = source_directory  + '구조물표.dxf'
    modifed_path = work_directory + '구조물표-수정됨.dxf'
    final_output_image = os.path.join(work_directory, new_text1 + '.png')
    converter = DXF2IMG()

    replace_text_in_dxf(file_path, modifed_path, new_text1, new_text2)

    output_paths = converter.convert_dxf2img([modifed_path], img_format='.png')

    if output_paths:
        converter.trim_and_resize_image(output_paths[0], final_output_image, target_size=(400, 900))

def copy_all_files(source_directory, target_directory, include_extensions=None, exclude_extensions=None):
    """
    원본 폴더의 모든 파일을 대상 폴더로 복사 (대상 폴더의 모든 데이터 제거)
    
    :param source_directory: 원본 폴더 경로
    :param target_directory: 대상 폴더 경로
    :param include_extensions: 복사할 확장자의 리스트 (예: ['.txt', '.csv'] → 이 확장자만 복사)
    :param exclude_extensions: 제외할 확장자의 리스트 (예: ['.log', '.tmp'] → 이 확장자는 복사 안 함)
    """
    
    # 대상 폴더가 존재하면 삭제 후 다시 생성
    if os.path.exists(target_directory):
        shutil.rmtree(target_directory)  # 대상 폴더 삭제
    os.makedirs(target_directory, exist_ok=True)  # 대상 폴더 재생성

    # 원본 폴더의 모든 파일을 가져와 복사
    for filename in os.listdir(source_directory):
        source_path = os.path.join(source_directory, filename)
        target_path = os.path.join(target_directory, filename)

        # 파일만 처리 (폴더는 복사하지 않음)
        if os.path.isfile(source_path):
            file_ext = os.path.splitext(filename)[1].lower()  # 확장자 추출 후 소문자로 변환
            
            # 포함할 확장자가 설정된 경우, 해당 확장자가 아니면 건너뛴다
            if include_extensions and file_ext not in include_extensions:
                continue
            
            # 제외할 확장자가 설정된 경우, 해당 확장자는 복사하지 않는다
            if exclude_extensions and file_ext in exclude_extensions:
                continue
            
            # 파일 복사 (메타데이터 유지)
            shutil.copy2(source_path, target_path)

    #모든작업 종료후 원본폴더째로 삭제
    shutil.rmtree(source_directory)

    print(f"📂 모든 파일이 {source_directory} → {target_directory} 로 복사되었습니다.")

def select_target_directory():
    """폴더 선택 다이얼로그를 띄워 target_directory를 설정"""
    global target_directory
    root = tk.Tk()
    root.withdraw()  # GUI 창 숨기기

    target_directory = filedialog.askdirectory(title="대상 폴더 선택")

    if target_directory:
        print(f"📁 선택된 대상 폴더: {target_directory}")
    else:
        print("❌ 대상 폴더가 선택되지 않았습니다.")

    return target_directory


def load_structure_data(filepath):
    """xlsx 파일을 읽고 교량과 터널 정보를 반환하는 함수"""
    bridge_list = []
    tunnel_list = []

    # xlsx 파일 읽기
    df_bridge = pd.read_excel(filepath, sheet_name='교량', header=None)
    df_tunnel = pd.read_excel(filepath, sheet_name='터널', header=None)

    # 첫 번째 행을 열 제목으로 설정
    df_bridge.columns = ['br_NAME', 'br_START_STA', 'br_END_STA', 'br_LENGTH']
    df_tunnel.columns = ['tn_NAME', 'tn_START_STA', 'tn_END_STA', 'tn_LENGTH']

    # 교량 구간과 터널 구간 정보
    for _, row in df_bridge.iterrows():
        bridge_list.append(
            Bridge(
            name=row['br_NAME'],
            start_station = row['br_START_STA'],
            end_station=row['br_END_STA'],
            length=row['br_LENGTH']
            )
        )

    for _, row in df_tunnel.iterrows():
        tunnel_list.append(
            Tunnel(
                name=row['tn_NAME'],
                start_station=row['tn_START_STA'],
                end_station=row['tn_END_STA'],
                length=row['tn_LENGTH']
            )
        )

    return bridge_list, tunnel_list


def create_structure_post_txt(dic: dict, work_directory: str):
    """
    결과 데이터를 받아 파일로 저장하는 함수.
    """
    output_file = work_directory + "structure_post.txt"  # 저장할 파일 이름

    with open(output_file, "w", encoding="utf-8") as file:
        for key, value in dic.items():  # dic.items() 사용
            file.write(f"{value[1]},.freeobj 0;{key};,;\n")  # 원하는 형식으로 저장



def create_structure_index_txt(dic: dict, work_directory: str, object_folder: str):
    """
    결과 데이터를 받아 파일로 저장하는 함수.
    """
    output_file = work_directory + "structure_post_index.txt"  # 저장할 파일 이름
    object_folder = object_folder.split("Object/")[-1]
    with open(output_file, "w", encoding="utf-8") as file:
        for key, value in dic.items():  # dic.items() 사용
            file.write(f".freeobj({key}) {object_folder}/{value[0]}.csv\n")  # 원하는 형식으로 저장

#메인 gui클래스
class MainProcessingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.base_source_directory = 'c:/temp/structure/소스/'
        self.log_box = None
        self.title("구조물표 생성기")
        self.geometry("650x450")

        self.source_directory = self.base_source_directory #원본 소스 위치
        self.work_directory = '' #작업물이 저장될 위치
        self.target_directory = ''
        self.create_widgets()

    def create_widgets(self):
        label = ttk.Label(self, text="구조물표 생성 프로그램", font=("Arial", 16, "bold"))
        label.pack(pady=10)

        self.log_box = tk.Text(self, height=20, wrap=tk.WORD, font=("Consolas", 10))
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        run_button = ttk.Button(self, text="생성", command=self.run_main)
        run_button.pack(pady=10)

    def log(self, message):
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)

    def run_main(self):
        try:
            # 디렉토리 설정
            self.log("작업 디렉토리 확인 중...")
            self.work_directory = 'c:/temp/structure/result/'
            if not os.path.exists(self.work_directory):
                os.makedirs(self.work_directory)
                self.log(f"디렉토리 생성: {self.work_directory}")
            else:
                self.log(f"디렉토리 존재: {self.work_directory}")

            # 대상 디렉토리 선택
            self.log("대상 디렉토리 선택 중...")
            self.target_directory = select_target_directory()
            self.log(f"대상 디렉토리: {self.target_directory}")

            # ✅ 항상 base_source_directory에서 새로 경로 만들기
            self.source_directory = os.path.join(self.base_source_directory) + '/'
            self.log(f"소스 경로: {self.source_directory}")

            # 구조물 데이터 로드
            self.log("구조물 데이터 로드 중...")
            filepath = read_file('엑셀 파일 선택')
            bridges, tunnels = load_structure_data(filepath)

            index = 5025
            #이미지 생성 프로세스
            index_dic = {}
            for br in bridges:
                process_dxf_image(self.source_directory, self.work_directory, br.name, br.length)
                copy_and_export_csv(
                    open_filename='교량표',
                    output_filename=br.name,
                    new_text=br.name,
                    source_directory=self.source_directory,
                    work_directory=self.work_directory
                )
                index_dic[index] = (br.name, br.start_station)
                index += 1
            for tunnel in tunnels:
                process_dxf_image(self.source_directory, self.work_directory, tunnel.name, tunnel.length)
                copy_and_export_csv(
                    open_filename='터널표',
                    output_filename=tunnel.name,
                    new_text=tunnel.name,
                    source_directory=self.source_directory,
                    work_directory=self.work_directory
                )

                index_dic[index] = (tunnel.name , tunnel.start_station)
                index += 1
            # 최종 텍스트 생성
            if bridges and tunnels:
                self.log("최종 결과 생성 중...")
                create_structure_post_txt(index_dic, self.work_directory)
                create_structure_index_txt(index_dic, self.work_directory, self.target_directory)
                self.log("결과 파일 생성 완료!")

            # 파일 복사
            self.log("결과 파일 복사 중...")
            copy_all_files(self.work_directory, self.target_directory, ['.csv', '.png', '.txt'], ['.dxf', '.ai'])

            self.log("✅ 모든 작업이 성공적으로 완료되었습니다.")
            messagebox.showinfo("완료", "곡선 데이터 처리 완료!")

        except Exception as e:
            self.log(f"[오류] {str(e)}")
            messagebox.showerror("오류", f"실행 중 오류 발생:\n{e}")

if __name__ == "__main__":
    app = MainProcessingApp()
    app.mainloop()

