import os
import tkinter as tk
from tkinter import filedialog, messagebox


# ========================
# 핵심 처리 함수
# ========================

def process_layout_file(input_file, output_file, start_station):
    # 파일 읽기
    with open(input_file, 'r', encoding='utf8') as f:
        lines = f.readlines()

    # 블록 단위 분리 및 뒤집기
    blocks = []
    block = []
    for line in lines:
        if line.startswith(";") or line.strip() == "":
            if block:
                blocks.append(block)
                block = []
        else:
            block.append(line)
    if block:
        blocks.append(block)

    # 블록 처리: 순서 뒤집기 + Rail/Railend 변경
    for block in blocks:
        block.reverse()
        if block:
            block[0] = block[0].replace("Railend", "rail")
            if len(block) > 1:
                block[-2] = block[-2].replace("Rail", "Railend")

    # 측점 계산
    stations = [int(line.split(",")[0]) for line in lines if line.split(",")[0].isdigit()]
    if not stations:
        messagebox.showerror("오류", "측점을 찾을 수 없습니다.")
        return
    last_station = max(stations)
    new_stations = [start_station + (last_station - sta) // 25 * 25 for sta in stations]

    # X 좌표 변환 및 파일 재작성
    new_lines = []
    j = 0
    for line in lines:
        parts = line.split(",")
        if parts[0].isdigit():
            line = str(new_stations[j]) + "," + ",".join(parts[1:])
            j += 1

        # X 좌표 처리
        try:
            parts2 = line.split(";")
            num_x = float(parts2[1])
            parts2[1] = str(round((num_x - 4.3) * -1, 3))
            line = ";".join(parts2)
        except:
            pass

        new_lines.append(line)

    # 결과 쓰기
    with open(output_file, 'w', encoding='utf8') as f:
        f.writelines(new_lines)


# ========================
# Tkinter GUI
# ========================

class LayoutGUI:
    def __init__(self, master):
        self.master = master
        master.title("Layout Reverse Tool")
        master.geometry("400x200")

        # 파일 선택
        tk.Label(master, text="원본 파일").grid(row=0, column=0, sticky='w')
        self.entry_file = tk.Entry(master, width=40)
        self.entry_file.grid(row=0, column=1)
        tk.Button(master, text="찾기", command=self.browse_file).grid(row=0, column=2)

        # 시작 측점
        tk.Label(master, text="시작 측점").grid(row=1, column=0, sticky='w')
        self.entry_sta = tk.Entry(master, width=20)
        self.entry_sta.grid(row=1, column=1)

        # 변환 버튼
        tk.Button(master, text="변환 실행", command=self.run_process).grid(row=2, column=0, columnspan=3, pady=20)

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if filename:
            self.entry_file.delete(0, tk.END)
            self.entry_file.insert(0, filename)

    def run_process(self):
        input_file = self.entry_file.get()
        if not input_file or not os.path.exists(input_file):
            messagebox.showerror("오류", "파일을 선택하세요.")
            return

        try:
            start_station = int(self.entry_sta.get())
        except ValueError:
            messagebox.showerror("오류", "시작 측점을 숫자로 입력하세요.")
            return

        output_file = os.path.join(os.path.dirname(input_file), "reverse.txt")
        process_layout_file(input_file, output_file, start_station)
        messagebox.showinfo("완료", f"변환 완료! 저장 파일: {output_file}")


# ========================
# 실행
# ========================

if __name__ == "__main__":
    root = tk.Tk()
    app = LayoutGUI(root)
    root.mainloop()
