import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 기본 데이터
insulator_l = 0.625
insulator_in = 0.086
insulator_effective = insulator_l - insulator_in

pipe_length_table = {
    'mark101':0.67,'mark102':1.07,'mark103':1.47,'mark104':1.87,
    'mark105':2.17,'mark106':2.47,'mark107':2.77,'mark108':3.07,
    'mark109':3.37,'mark110':3.67,'mark111':3.97,'mark112':4.27,
}

adjustable_step = 0.03
min_out = 0.06
adjustable_step_max = 21

# 파이프 끝 구멍 오프셋 (15mm 간격, 4칸)
pipe_hole_offsets = [0.015, 0.030, 0.045, 0.060]

# GUI 윈도우 생성
root = tk.Tk()
root.title("상부 파이프 조립 시뮬레이터")

# 콤보박스 (파이프 선택)
pipe_var = tk.StringVar(value='mark104')
pipe_combo = ttk.Combobox(root, textvariable=pipe_var, values=list(pipe_length_table.keys()), state="readonly")
pipe_combo.pack(pady=5)

# 슬라이더 (조정봉 칸수 선택)
rod_var = tk.IntVar(value=10)
rod_slider = tk.Scale(root, from_=0, to=adjustable_step_max, orient='horizontal', variable=rod_var, label="조정봉 칸수")
rod_slider.pack(pady=5)

# 콤보박스 (파이프 구멍 위치 선택)
hole_var = tk.IntVar(value=1)
hole_combo = ttk.Combobox(root, textvariable=hole_var, values=[1,2,3,4], state="readonly")
hole_combo.pack(pady=5)

# 목표 길이 입력
target_entry = tk.Entry(root)
target_entry.pack(pady=5)

def auto_select():
    try:
        target_length = float(target_entry.get())
    except ValueError:
        messagebox.showerror("입력 오류", "목표 길이를 숫자로 입력하세요.")
        return

    results = []
    for mark, pipe_length in pipe_length_table.items():
        for i in range(adjustable_step_max+1):
            rod_out = min_out + i*adjustable_step
            for idx, offset in enumerate(pipe_hole_offsets, start=1):
                total_length = pipe_length + insulator_effective + rod_out + offset
                results.append((mark, i, idx, total_length))

    # 허용 오차 범위 ±0.01m
    tolerance = 0.01
    candidates = [r for r in results if abs(r[3]-target_length) <= tolerance]

    if not candidates:
        messagebox.showerror("조건 불일치", f"목표 길이 {target_length:.3f}m에 맞는 조합이 없습니다.")
        return

    best = min(candidates, key=lambda x: abs(x[3]-target_length))

    # 자동 선택 반영
    pipe_var.set(best[0])
    rod_var.set(best[1])
    hole_var.set(best[2])
    update_plot()

# 버튼
auto_button = tk.Button(root, text="목표 길이에 맞추기", command=auto_select)
auto_button.pack(pady=5)

# matplotlib Figure
fig, ax = plt.subplots(figsize=(10,4))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack()

def update_plot(*args):
    ax.clear()
    mark = pipe_var.get()
    pipe_length = pipe_length_table[mark]
    rod_out = min_out + rod_var.get()*adjustable_step
    pipe_offset = pipe_hole_offsets[hole_var.get()-1]

    total_length = pipe_length + insulator_effective + rod_out + pipe_offset

    # 애자
    ax.plot([0, insulator_effective], [0,0], color='y', linewidth=25)
    ax.text(insulator_effective/2, 0.02, f"애자 {insulator_effective:.3f}m", ha='center')

    # 파이프
    pipe_start = insulator_effective
    pipe_end = insulator_effective + pipe_length
    ax.plot([pipe_start, pipe_end], [0,0], color='b', linewidth=5)
    ax.text((pipe_start+pipe_end)/2, 0.02, f"{mark} {pipe_length:.3f}m", ha='center')

    # 파이프 끝 구멍 표시
    for idx, offset in enumerate(pipe_hole_offsets, start=1):
        hole_pos = pipe_end + offset
        if idx == hole_var.get():
            ax.plot(hole_pos, 0, 'ro', markersize=8)
            ax.text(hole_pos, -0.03, f"구멍 {idx}", ha='center', color='red')
        else:
            ax.plot(hole_pos, 0, 'ko', markersize=5)

    # 조정봉
    rod_start = pipe_end
    rod_end = pipe_end + rod_out
    ax.plot([rod_start, rod_end], [0,0], color='r', linewidth=3)
    ax.text((rod_start+rod_end)/2, 0.02, f"조정봉 {rod_out:.3f}m", ha='center')

    # 전체 길이
    ax.text(total_length, 0.05, f"총 {total_length:.3f}m", ha='right', color='g')

    ax.set_title("상부 파이프 조립 시뮬레이션 (구멍 오프셋 반영)")
    ax.set_ylim(-0.1, 0.2)
    ax.axis('off')
    canvas.draw()

# 이벤트 연결
pipe_combo.bind("<<ComboboxSelected>>", update_plot)
rod_slider.config(command=lambda val: update_plot())
hole_combo.bind("<<ComboboxSelected>>", update_plot)

# 초기 실행
update_plot()

root.mainloop()