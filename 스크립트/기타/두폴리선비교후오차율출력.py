import numpy as np
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def calculate_average_error(main_poly, compare_poly):
    if len(main_poly) != len(compare_poly):
        raise ValueError("두 폴리선의 점 개수가 같아야 합니다.")

    errors = []
    for (m_sta, mx, my), (c_sta, cx, cy) in zip(main_poly, compare_poly):
        dist = np.sqrt((mx - cx)**2 + (my - cy)**2)
        errors.append(dist)

    avg_error = np.mean(errors)
    return avg_error, errors

def read_coordinates(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    coordinates = []
    for i, line in enumerate(lines):
        parts = line.strip().split(',')
        # 헤더 라인 건너뛰기
        if i == 0 and not parts[0].replace('.', '', 1).isdigit():
            continue

        if len(parts) == 5:
            display_sta = float(parts[0].strip())
            real_sta = float(parts[1].strip())
            northing = float(parts[2].strip())
            easting = float(parts[3].strip())
            bearing = float(parts[4].strip())
            coordinates.append((display_sta, easting, northing))
        elif len(parts) == 4:
            sta = float(parts[0].strip())
            x = float(parts[1].strip())
            y = float(parts[2].strip())
            z = float(parts[3].strip())
            coordinates.append((sta, x, y))
        elif len(parts) == 3:
            sta = i * 25
            x = float(parts[0].strip())
            y = float(parts[1].strip())
            z = float(parts[2].strip())
            coordinates.append((sta, x, y))
    return coordinates


def list_length_adjustor(mainlist, sublist):
    new_list = []
    sub_dict = {sta: (x, y) for sta, x, y in sublist}  # STA를 키로 딕셔너리화
    for m_sta, mx, my in mainlist:
        if m_sta in sub_dict:  # STA 값이 일치하는 경우만 매칭
            sx, sy = sub_dict[m_sta]
            new_list.append((m_sta, sx, sy))
    return new_list



class Main(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("폴리선 오차 비교")

        # 메인 파일
        tk.Label(self, text="메인 파일:").grid(row=0, column=0, sticky="w")
        self.entry_input1 = tk.Entry(self, width=50)
        self.entry_input1.grid(row=0, column=1, padx=5, pady=2)
        tk.Button(self, text="찾기", command=lambda: self.browse_input(self.entry_input1)).grid(row=0, column=2, padx=5)

        # 비교 파일
        tk.Label(self, text="비교할 파일:").grid(row=1, column=0, sticky="w")
        self.entry_input2 = tk.Entry(self, width=50)
        self.entry_input2.grid(row=1, column=1, padx=5, pady=2)
        tk.Button(self, text="찾기", command=lambda: self.browse_input(self.entry_input2)).grid(row=1, column=2, padx=5)

        # 실행 버튼
        tk.Button(self, text="비교", command=self.compare, width=5, bg="lightblue").grid(row=3, column=0, columnspan=50, pady=10)
        # 실행 버튼
        tk.Button(self, text="종료", command=self.destroy, width=5, bg="lightblue").grid(row=3, column=1,  columnspan=50, pady=10)
    def browse_input(self, entry):
        filename = filedialog.askopenfilename(title="파일 선택",
                                              filetypes=[("Text files", "*.txt *.csv"), ("All files", "*.*")])
        if filename:
            entry.delete(0, tk.END)
            entry.insert(0, filename)

    def compare(self):
        main_file = self.entry_input1.get()
        sub_file = self.entry_input2.get()

        main_poly = read_coordinates(main_file)
        sub_poly = read_coordinates(sub_file)

        if len(main_poly) != len(sub_poly):
            sub_poly = list_length_adjustor(main_poly, sub_poly)

        if not sub_poly:
            print("⚠️ 비교할 수 있는 점이 없습니다. STA 값이 맞는지 확인하세요.")
            return

        avg_error, errors = calculate_average_error(main_poly, sub_poly)

        print("각 점별 오차:", errors)
        print("평균 오차율:", avg_error)

        # --- 폴리선 시각화 ---
        main_sta = [sta for sta, x, y in main_poly]
        main_x = [x for sta, x, y in main_poly]
        main_y = [y for sta, x, y in main_poly]

        sub_sta = [sta for sta, x, y in sub_poly]
        sub_x = [x for sta, x, y in sub_poly]
        sub_y = [y for sta, x, y in sub_poly]

        plt.figure(figsize=(8, 6))
        ax = plt.gca()  # 현재 Axes 객체 가져오기
        plt.plot(main_x, main_y, 'b-', label="Main Poly (기준)")
        plt.plot(sub_x, sub_y, 'r--', label="Compare Poly (비교)")
        plt.scatter(main_x, main_y, c='blue', s=10)
        plt.scatter(sub_x, sub_y, c='red', s=10)

        plt.title(f"두 폴리선 비교\n평균 오차율: {avg_error:.3f}")
        plt.xlabel("X 좌표 (Easting)")
        plt.ylabel("Y 좌표 (Northing)")
        plt.legend()
        ax.set_aspect('equal')
        # X, Y축 범위 지정 (예시: 데이터 범위에 맞춰 확대)
        plt.xlim(min(main_x + sub_x) - 5000, max(main_x + sub_x) + 5000)
        plt.ylim(min(main_y + sub_y) - 1000, max(main_y + sub_y) + 1000)
        plt.grid(True)
        plt.show()


if __name__ == "__main__":
    app = Main()
    app.mainloop()
