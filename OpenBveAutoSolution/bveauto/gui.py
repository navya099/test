# bveauto/gui.py
import tkinter as tk

from .context import BuildContext
from .pipeline import Pipeline
from .steps import (
    InfoStep, BridgeStep, CurveStep, PoleStep,
    SignalStep, PostStep, TransmissionStep,
)


def build_default_pipeline(log) -> Pipeline:
    return Pipeline([
        InfoStep(), BridgeStep(), CurveStep(), PoleStep(),
        SignalStep(), PostStep(), TransmissionStep(),
    ], log)


def launch():
    root = tk.Tk()
    root.title("SolutionRunner GUI")

    log_box = tk.Text(root, height=15, width=70)
    log_box.pack()

    def log(msg: str):
        log_box.insert(tk.END, msg + "\n")
        log_box.see(tk.END)

    ctx = BuildContext()
    pipeline = build_default_pipeline(log)

    # 입력 필드
    tk.Label(root, text="설계속도").pack()
    entry_speed = tk.Entry(root, width=20)
    entry_speed.insert(0, "150")
    entry_speed.pack()

    tk.Label(root, text="선로갯수").pack()
    entry_linecount = tk.Entry(root, width=20)
    entry_linecount.insert(0, "1")
    entry_linecount.pack()

    def sync_inputs():
        try:
            ctx.designspeed = int(entry_speed.get())
            ctx.linecount = int(entry_linecount.get())
            log(f"입력 반영: 속도={ctx.designspeed}, 선로수={ctx.linecount}")
        except ValueError:
            log("⚠️ 숫자를 입력하세요")

    def safe_run(fn):
        try:
            sync_inputs()
            fn()
        except Exception as e:
            log(f"[중단] {e}")

    # 버튼
    tk.Button(root, text="전체실행",
              command=lambda: safe_run(lambda: pipeline.run(ctx))).pack()
    tk.Button(root, text="기본정보 로드",
              command=lambda: safe_run(lambda: pipeline.run_single(ctx, "#0. 기본 정보 로드"))).pack()

    # 개별 단계 버튼 자동 생성
    for name in pipeline.names()[1:]:
        tk.Button(root, text=name,
                  command=lambda n=name: safe_run(lambda: pipeline.run_single(ctx, n))).pack()

    tk.Button(root, text="로그 클리어",
              command=lambda: log_box.delete("1.0", tk.END)).pack()
    tk.Button(root, text="종료", command=root.destroy).pack()

    root.mainloop()