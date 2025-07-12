import tkinter as tk
from tkinter import messagebox
import math
from scipy.optimize import fsolve

# 결과 데이터 클래스
class TrackData:
    def __init__(self, name, R, L):
        self.name = name
        self.R = R
        self.L = L

# 완화곡선 수치식
def equation(L, R, S):
    return L - math.sqrt((24 * R * S) / (1 - (L**2 / (112 * R**2)) + (L**4 / (2112 * R**4))))

def cal_clothoid(params, auto=False):
    R, B, AA, D, L = params
    RR = R + D / 2
    So = round((L ** 2) / (24 * RR), 3)
    Ro = round(RR - So, 3)

    Ri = round((Ro - (B + AA)), 3)
    Si = round((B + AA) - D + So, 3)
    Li = math.sqrt(24 * Ri * Si)

    Rc = round((Ro - AA), 3)
    Sc = round(R - Rc, 3)
    Lc = math.sqrt(24 * Rc * Sc)

    return [
        TrackData("외측궤도", Ro, L),
        TrackData("구축중심", Rc, Lc),
        TrackData("내측궤도", Ri, Li)
    ]

# 자동 계산 모드
def auto_calculate_params(R, B, D):
    V = min((R * 160 / 11.8) ** 0.5, 120)
    C = min(11.8 * V ** 2 / R, 160)
    L = 600 * C / 1000
    theta = math.atan(C / 1500)
    W = 24000 / R
    Qc = 4300 * math.sin(theta) - 1050 * (1 - math.cos(theta))
    S = 2400 / R
    alpha = round(W + Qc + S, -1)
    AA = B + alpha * 0.001
    return R, B, AA, D, L

# 계산 실행
def on_calculate():
    try:
        R = float(entry_R.get())
        B = float(entry_B.get())
        D = float(entry_D.get())

        if mode_var.get() == 0:
            AA = float(entry_AA.get())
            L = float(entry_L.get())
        else:
            R, B, AA, D, L = auto_calculate_params(R, B, D)

        results = cal_clothoid((R, B, AA, D, L))
        result_text.delete("1.0", tk.END)

        for track in results:
            result_text.insert(tk.END, f"{track.name} - R = {track.R:.3f}, L = {track.L:.3f}\n")

    except Exception as e:
        messagebox.showerror("오류", f"입력값을 확인하세요.\n{str(e)}")

# GUI 구성
root = tk.Tk()
root.title("클로소이드 계산기")
root.geometry("400x500")

mode_var = tk.IntVar(value=0)
tk.Label(root, text="계산 모드 선택").pack()
tk.Radiobutton(root, text="직접 입력", variable=mode_var, value=0).pack()
tk.Radiobutton(root, text="자동 계산", variable=mode_var, value=1).pack()

# 입력창들
def create_input(label, varname):
    tk.Label(root, text=label).pack()
    ent = tk.Entry(root)
    ent.pack()
    return ent

entry_R = create_input("곡선반경 R", "R")
entry_B = create_input("직선구간 B", "B")
entry_AA = create_input("곡선구간 A (직접입력시)", "AA")
entry_D = create_input("선로중심간격 D", "D")
entry_L = create_input("완화곡선길이 L (직접입력시)", "L")

# 계산 버튼
tk.Button(root, text="계산 실행", command=on_calculate).pack(pady=10)

# 결과창
tk.Label(root, text="결과").pack()
result_text = tk.Text(root, height=10, width=40)
result_text.pack()

root.mainloop()
