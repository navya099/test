"""모달 다이얼로그."""
from __future__ import annotations
from typing import Optional

import tkinter as tk
from tkinter import ttk

from core.models import AlignResult


def ask_reference_arch(root, labels: list[str],
                       default_idx: int = 0) -> Optional[int]:
    win = tk.Toplevel(root)
    win.title("FL 통일 기준")
    win.transient(root)
    win.grab_set()
    win.resizable(False, False)

    ttk.Label(win, text="기준이 될 아치를 선택하세요.\n"
                        "(다른 아치들이 이 FL에 맞춰집니다)",
              padding=12).pack()

    var = tk.IntVar(value=default_idx)
    frame = ttk.Frame(win, padding=(16, 0, 16, 8))
    frame.pack(fill="x")
    for i, label in enumerate(labels):
        ttk.Radiobutton(frame, text=label, value=i,
                        variable=var).pack(anchor="w", pady=2)

    result = {"idx": None}

    def on_ok():
        result["idx"] = var.get()
        win.destroy()

    btns = ttk.Frame(win, padding=(16, 8, 16, 12))
    btns.pack(fill="x")
    ttk.Button(btns, text="취소",
               command=win.destroy).pack(side="right", padx=(6, 0))
    ttk.Button(btns, text="확인", style="Accent.TButton",
               command=on_ok).pack(side="right")

    _center(win, root)
    root.wait_window(win)
    return result["idx"]


def confirm_align_dialog(root, r: AlignResult, ref_label: str) -> bool:
    win = tk.Toplevel(root)
    win.title("FL 통일 미리보기")
    win.transient(root)
    win.grab_set()

    ttk.Label(win, text=f"기준 아치: {ref_label}   (FL = {r.target_FL:.4f} m)",
              style="Title.TLabel", padding=(12, 12, 12, 6)).pack(anchor="w")

    cols = ("label", "old_R1Y", "new_R1Y", "delta", "old_FL", "new_FL")
    heads = {
        "label": "아치", "old_R1Y": "이전 R1_Y", "new_R1Y": "변경 R1_Y",
        "delta": "ΔR1_Y", "old_FL": "이전 FL", "new_FL": "변경 FL",
    }
    frame = ttk.Frame(win, padding=(12, 0, 12, 8))
    frame.pack(fill="both", expand=True)
    tree = ttk.Treeview(frame, columns=cols, show="headings",
                        height=len(r.labels))
    for c in cols:
        tree.heading(c, text=heads[c])
        tree.column(c, width=100, anchor="center")
    for i, label in enumerate(r.labels):
        tree.insert("", "end", values=(
            label, f"{r.old_R1Y[i]:.4f}", f"{r.new_R1Y[i]:.4f}",
            f"{r.new_R1Y[i] - r.old_R1Y[i]:+.4f}",
            f"{r.old_FL[i]:.4f}", f"{r.new_FL[i]:.4f}"))
    tree.pack(side="left", fill="both", expand=True)

    result = {"ok": False}
    btns = ttk.Frame(win, padding=(12, 0, 12, 12))
    btns.pack(fill="x", side="bottom")
    ttk.Button(btns, text="취소",
               command=win.destroy).pack(side="right", padx=(6, 0))
    ttk.Button(btns, text="적용", style="Accent.TButton",
               command=lambda: (result.update(ok=True), win.destroy())
               ).pack(side="right")

    _center(win, root)
    root.wait_window(win)
    return result["ok"]


def _center(win, root):
    win.update_idletasks()
    x = (root.winfo_rootx() + root.winfo_width() // 2
         - win.winfo_width() // 2)
    y = (root.winfo_rooty() + root.winfo_height() // 2
         - win.winfo_height() // 2)
    win.geometry(f"+{x}+{y}")