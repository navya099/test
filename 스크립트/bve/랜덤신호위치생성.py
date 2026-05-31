from tkinter.filedialog import askdirectory
import random
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
import os

class SignalPlanner:
    def __init__(self):
        self.structure_list = None
        self.pole_positions = []
        self.block_length = []

    def distribute_pole_spacing_flexible(self, start_km, end_km, spans):
        start_m = int(start_km * 1000)
        end_m = int(end_km * 1000)

        positions = [start_m]
        selected_spans = []
        current_pos = start_m

        while current_pos < end_m:
            possible_spans = list(spans)
            random.shuffle(possible_spans)

            for span in possible_spans:
                if current_pos + span > end_m:
                    continue
                positions.append(current_pos + span)
                selected_spans.append(span)
                current_pos += span
                break

            if current_pos + min(spans) > end_m:
                break

        self.pole_positions = positions
        self.block_length = selected_spans
        return selected_spans, positions

    def find_structure_section(self, filepath):
        df_bridge = pd.read_excel(filepath, sheet_name='교량', header=None)
        df_tunnel = pd.read_excel(filepath, sheet_name='터널', header=None)

        df_bridge.columns = ['br_NAME', 'br_START_STA', 'br_END_STA', 'br_LENGTH']
        df_tunnel.columns = ['tn_NAME', 'tn_START_STA', 'tn_END_STA', 'tn_LENGTH']

        structure_list = {'bridge': [], 'tunnel': []}
        for _, row in df_bridge.iterrows():
            structure_list['bridge'].append((row['br_NAME'], row['br_START_STA'], row['br_END_STA']))
        for _, row in df_tunnel.iterrows():
            structure_list['tunnel'].append((row['tn_NAME'], row['tn_START_STA'], row['tn_END_STA']))

        self.structure_list = structure_list
        return structure_list

    def isbridge_tunnel(self, sta):
        for name, start, end in self.structure_list['bridge']:
            if start <= sta <= end:
                return '교량'
        for name, start, end in self.structure_list['tunnel']:
            if start <= sta <= end:
                return '터널'
        return '토공'

    def save_to_txt(self, filename="pole_positions.txt"):
        pole_data = {
            '교량': {'signal_type': '5현시_교량용', 'index': 44, 'x-offset': -2.675},
            '터널': {'signal_type': '5현시_터널용', 'index': 62, 'x-offset': -2.54},
            '토공': {'signal_type': '5현시_토공용', 'index': 44, 'x-offset': -2.675}
        }
        device_data = {
            'LEU': (46,),
            '자동폐색유니트': (47,),
            '발리스': (45,)
        }

        with open(filename, "w", encoding="utf-8") as f:
            for i, pos in enumerate(self.pole_positions):
                structure_type = self.isbridge_tunnel(pos)
                signal_data = pole_data[structure_type]
                signal_type = signal_data['signal_type']
                signal_index = signal_data['index']
                x_offset = signal_data['x-offset']

                if i != 0:
                    f.write('\n,;폐색신호기\n')
                    f.write(',;하선\n')
                    f.write(f'{pos},.freeobj 0;{signal_index};{x_offset};;,;{signal_type}\n')

                    f.write(',;상선\n')
                    if structure_type == '터널':
                        f.write(f'{pos},.freeobj 0;{signal_index};3;0;180;,;{signal_type}\n')
                    else:
                        f.write(f'{pos + 10},.freeobj 0;{signal_index};{x_offset};0;180;,;{signal_type}\n')

                    if structure_type != '터널':
                        f.write(',;발리스\n')
                        f.write(f'{pos - 20},.freeobj 0;{device_data["발리스"][0]};0;;,;\n')
                        f.write(f'{pos - 17},.freeobj 0;{device_data["발리스"][0]};0;;,;\n')

                        f.write(',;LEU\n')
                        f.write(f'{pos - 14},.freeobj 0;{device_data["LEU"][0]};0;0.3;,;\n')

                        f.write(',;자동폐색유니트\n')
                        f.write(f'{pos - 13},.freeobj 0;{device_data["자동폐색유니트"][0]};0;;,;\n')

    def run(self, start_km, end_km, excel_file, save_file):
        block_length = [random.randint(1200, 1800) for _ in range(4)]
        self.distribute_pole_spacing_flexible(start_km, end_km, block_length)
        self.find_structure_section(excel_file)
        self.save_to_txt(save_file)
        print(f"✅ 신호 데이터가 {save_file} 파일로 저장되었습니다!")
        print(f"신호기 개수: {len(self.pole_positions)}")
        print(f"폐색간격 최소:{min(self.block_length)}, 최대:{max(self.block_length)}")

class SignalPlannerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("400x400")
        self.title("신호 배치 자동화 툴")
        self.start_sta_var = tk.DoubleVar()
        tk.Label(self, text='시작 측점').pack(pady=5)
        tk.Entry(self, textvariable=self.start_sta_var).pack(pady=5)
        tk.Label(self, text='끝 측점').pack(pady=5)
        self.end_sta_var = tk.DoubleVar()
        tk.Entry(self, textvariable=self.end_sta_var).pack(pady=5)

        # 버튼 UI
        tk.Button(self, text="엑셀 구조물 파일 선택", command=self.load_excel).pack(pady=5)
        tk.Button(self, text="곡선 txt 파일 선택", command=self.load_curve).pack(pady=5)
        tk.Button(self, text="신호 배치 실행", command=self.run_planner).pack(pady=10)
        tk.Button(self, text="종료", command=self.destroy).pack(pady=10)

        self.excel_file = None
        self.curve_file = None

    def load_excel(self):
        self.excel_file = filedialog.askopenfilename(
            title="엑셀 파일 선택",
            filetypes=[("Excel Files", "*.xlsx")]
        )
        if self.excel_file:
            messagebox.showinfo("확인", f"엑셀 파일 선택됨:\n{self.excel_file}")

    def load_curve(self):
        self.curve_file = filedialog.askopenfilename(
            title="곡선 txt 파일 선택",
            filetypes=[("Text Files", "*.txt")]
        )
        if self.curve_file:
            messagebox.showinfo("확인", f"곡선 파일 선택됨:\n{self.curve_file}")

    def run_planner(self):
        if not self.excel_file or not self.curve_file:
            messagebox.showerror("오류", "엑셀 파일과 곡선 파일을 모두 선택하세요.")
            return

        save_dir = filedialog.askdirectory(title="결과 저장 폴더 선택")
        if not save_dir:
            return

        save_path = os.path.join(save_dir, "신호.txt")

        # 실행
        start_km = self.start_sta_var.get() // 1000
        end_km = self.end_sta_var.get() // 1000
        planner = SignalPlanner()
        planner.run(
            start_km=start_km,
            end_km=end_km,
            excel_file=self.excel_file,
            save_file=save_path
        )

        messagebox.showinfo("완료", f"✅ 신호 데이터가 저장되었습니다:\n{save_path}")

if __name__ == "__main__":
    app = SignalPlannerGUI()
    app.mainloop()