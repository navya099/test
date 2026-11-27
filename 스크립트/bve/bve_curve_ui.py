"""BVE 곡선레일(5m) 설치 구문 생성기 - Tkinter GUI 모듈."""
from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from bve_curve_core import (
    ALIGNMENT_TYPES,
    CURVE,
    STRAIGHT,
    STRUCTURE_BRIDGE,
    STRUCTURE_EARTHWORK,
    STRUCTURE_TUNNEL,
    TRACK_BALLAST,
    TRACK_CONCRETE,
    generate_bve_files,
    get_default_values,
)

# ---------------------------------------------------------------------------
# 폼 라벨 및 중첩 딕셔너리 변환 (UI 표현 전용)
# ---------------------------------------------------------------------------
FORM_LABELS = [
    "freeobj 곡선-토공-자갈도상",
    "freeobj 곡선-토공-콘크리트도상",
    "freeobj 곡선-교량-자갈도상",
    "freeobj 곡선-교량-콘크리트도상",
    "freeobj 곡선-터널-자갈도상",
    "freeobj 곡선-터널-콘크리트도상",
    "freeobj 직선",
    "railtype 곡선",
    "railtype 직선-토공-자갈도상",
    "railtype 직선-토공-콘크리트도상",
    "railtype 직선-교량-자갈도상",
    "railtype 직선-교량-콘크리트도상",
    "railtype 직선-터널-자갈도상",
    "railtype 직선-터널-콘크리트도상",
]


def flatten_defaults(defaults: dict) -> dict[str, int]:
    flat: dict[str, int] = {}
    for structure_type, sub in defaults["freeobj"][CURVE].items():
        for track_type, val in sub.items():
            flat[f"freeobj 곡선-{structure_type}-{track_type}"] = val
    flat["freeobj 직선"] = defaults["freeobj"][STRAIGHT]
    flat["railtype 곡선"] = defaults["railtype"][CURVE]
    for structure_type, sub in defaults["railtype"][STRAIGHT].items():
        for track_type, val in sub.items():
            flat[f"railtype 직선-{structure_type}-{track_type}"] = val
    return flat


def unflatten_defaults(flat: dict[str, int | str]) -> dict:
    def get(key: str) -> int:
        return int(flat[key])

    return {
        "freeobj": {
            CURVE: {
                STRUCTURE_TUNNEL: {
                    TRACK_CONCRETE: get("freeobj 곡선-터널-콘크리트도상"),
                    TRACK_BALLAST: get("freeobj 곡선-터널-자갈도상"),
                },
                STRUCTURE_EARTHWORK: {
                    TRACK_CONCRETE: get("freeobj 곡선-토공-콘크리트도상"),
                    TRACK_BALLAST: get("freeobj 곡선-토공-자갈도상"),
                },
                STRUCTURE_BRIDGE: {
                    TRACK_CONCRETE: get("freeobj 곡선-교량-콘크리트도상"),
                    TRACK_BALLAST: get("freeobj 곡선-교량-자갈도상"),
                },
            },
            STRAIGHT: get("freeobj 직선"),
        },
        "railtype": {
            CURVE: get("railtype 곡선"),
            STRAIGHT: {
                STRUCTURE_TUNNEL: {
                    TRACK_CONCRETE: get("railtype 직선-터널-콘크리트도상"),
                    TRACK_BALLAST: get("railtype 직선-터널-자갈도상"),
                },
                STRUCTURE_EARTHWORK: {
                    TRACK_CONCRETE: get("railtype 직선-토공-콘크리트도상"),
                    TRACK_BALLAST: get("railtype 직선-토공-자갈도상"),
                },
                STRUCTURE_BRIDGE: {
                    TRACK_CONCRETE: get("railtype 직선-교량-콘크리트도상"),
                    TRACK_BALLAST: get("railtype 직선-교량-자갈도상"),
                },
            },
        },
    }


# ---------------------------------------------------------------------------
# UserForm — Enter로 다음 칸 이동, 마지막 칸 Enter = 자동 제출
# ---------------------------------------------------------------------------
class UserForm(tk.Frame):
    """파라미터 입력 폼 (메인창에 임베드)."""

    def __init__(self, master, defaults: dict[str, int], on_submit=None):
        super().__init__(master)
        self.defaults = defaults
        self.on_submit = on_submit
        self.entries: dict[str, ttk.Entry] = {}
        self._create_widgets()
        self._bind_enter_navigation()

    def _create_widgets(self):
        left_labels = [l for l in FORM_LABELS if l.startswith("freeobj")]
        right_labels = [l for l in FORM_LABELS if l.startswith("railtype")]

        for col, (title, labels) in enumerate(
            [("FreeObj 인덱스", left_labels), ("RailType 인덱스", right_labels)]
        ):
            box = ttk.LabelFrame(self, text=title, padding=8)
            box.grid(row=0, column=col, sticky="nsew", padx=6, pady=6)
            for i, label in enumerate(labels):
                ttk.Label(box, text=label).grid(row=i, column=0, sticky="w", pady=2)
                entry = ttk.Entry(box, width=8, justify="right")
                entry.grid(row=i, column=1, sticky="e", pady=2)
                entry.insert(0, str(self.defaults.get(label, "")))
                self.entries[label] = entry
            self.columnconfigure(col, weight=1)

        btn_row = ttk.Frame(self)
        btn_row.grid(row=1, column=0, columnspan=2, pady=(4, 8))
        ttk.Button(
            btn_row, text="▶ 실행 (Ctrl+Enter)", command=self._submit
        ).pack(side="left", padx=4)
        ttk.Button(
            btn_row, text="기본값 복원", command=self._reset_defaults
        ).pack(side="left", padx=4)

    def _ordered_entries(self) -> list[ttk.Entry]:
        return [self.entries[l] for l in FORM_LABELS if l in self.entries]

    def _bind_enter_navigation(self):
        entries = self._ordered_entries()
        for i, entry in enumerate(entries):
            if i < len(entries) - 1:
                nxt = entries[i + 1]
                entry.bind(
                    "<Return>",
                    lambda e, n=nxt: (n.focus_set(), n.select_range(0, "end"), "break")[2],
                )
            else:
                entry.bind("<Return>", lambda e: (self._submit(), "break")[1])
            entry.bind("<KeyPress>", self._only_numeric)
            entry.bind("<Control-Return>", lambda e: (self._submit(), "break")[1])

        if entries:
            self.after(
                50, lambda: (entries[0].focus_set(), entries[0].select_range(0, "end"))
            )

    @staticmethod
    def _only_numeric(event):
        if event.char and not event.char.isdigit() and event.keysym not in (
            "BackSpace", "Delete", "Left", "Right", "Tab", "Return", "Home", "End"
        ):
            return "break"

    def _reset_defaults(self):
        for label, entry in self.entries.items():
            entry.delete(0, "end")
            entry.insert(0, str(self.defaults.get(label, "")))

    def update_defaults(self, new_defaults: dict[str, int]):
        self.defaults = new_defaults
        self._reset_defaults()

    def _submit(self):
        values: dict[str, int] = {}
        for label, entry in self.entries.items():
            raw = entry.get().strip()
            if not raw:
                messagebox.showwarning("입력 오류", f"'{label}' 값이 비어 있습니다.")
                entry.focus_set()
                return
            try:
                values[label] = int(raw)
            except ValueError:
                messagebox.showwarning("입력 오류", f"'{label}' 값이 숫자가 아닙니다.")
                entry.focus_set()
                entry.select_range(0, "end")
                return
        if self.on_submit:
            self.on_submit(values)


class FreeobjApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BVE FreeObj 자동 생성기")
        self.geometry("820x680")
        self.minsize(760, 620)

        self.alignment_type = tk.StringVar(value="도시철도")
        self.curve_path = tk.StringVar()
        self.structure_path = tk.StringVar()
        self.output_dir = tk.StringVar()

        self.user_form: UserForm | None = None
        self._build_ui()
        self._on_alignment_change()

    def _build_ui(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="노선 유형:").grid(row=0, column=0, sticky="w")
        cb = ttk.Combobox(
            top,
            textvariable=self.alignment_type,
            values=list(ALIGNMENT_TYPES),
            state="readonly",
            width=12,
        )
        cb.grid(row=0, column=1, sticky="w", padx=6)
        cb.bind("<<ComboboxSelected>>", lambda e: self._on_alignment_change())

        self._path_row(
            top, 1, "곡선 파일", self.curve_path, [("CURVE_INFO", "*.txt"), ("All files", "*.*")]
        )
        self._path_row(
            top, 2, "구조물 XLSX", self.structure_path, [("Excel", "*.xlsx")]
        )
        self._path_row(top, 3, "출력 폴더", self.output_dir, None)
        top.columnconfigure(1, weight=1)

        self.form_container = ttk.Frame(self, padding=(10, 0))
        self.form_container.pack(fill="x")

        log_frame = ttk.LabelFrame(self, text="로그", padding=6)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(4, 10))
        self.log_box = tk.Text(log_frame, height=12, wrap="word", font=("Consolas", 10))
        sb = ttk.Scrollbar(log_frame, command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=sb.set)
        self.log_box.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.bind("<Control-Return>", lambda e: self.user_form._submit() if self.user_form else None)
        self.log("노선 유형을 선택하고 파일 경로를 지정한 뒤 실행하세요.")

    def _path_row(self, parent, row, label, var, filetypes):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=2)
        entry = ttk.Entry(parent, textvariable=var)
        entry.grid(row=row, column=1, sticky="ew", padx=6)

        def browse():
            if filetypes is None:
                path = filedialog.askdirectory(title=f"{label} 선택")
            else:
                path = filedialog.askopenfilename(title=f"{label} 선택", filetypes=filetypes)
            if path:
                var.set(path)

        ttk.Button(parent, text="찾아보기", command=browse).grid(row=row, column=2)

    def _on_alignment_change(self):
        try:
            defaults = get_default_values(self.alignment_type.get())
        except ValueError:
            return
        flat = flatten_defaults(defaults)
        if self.user_form is None:
            self.user_form = UserForm(
                self.form_container, defaults=flat, on_submit=self._run_with_values
            )
            self.user_form.pack(fill="x")
        else:
            self.user_form.update_defaults(flat)

    def log(self, message: str):
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.update_idletasks()

    def _run_with_values(self, values: dict[str, int]):
        curve = self.curve_path.get().strip()
        structure = self.structure_path.get().strip()
        outdir = self.output_dir.get().strip()

        if not curve or not Path(curve).is_file():
            messagebox.showwarning("입력 오류", "곡선 파일을 선택하세요.")
            return
        if not structure or not Path(structure).is_file():
            messagebox.showwarning("입력 오류", "구조물 XLSX 파일을 선택하세요.")
            return
        if not outdir:
            outdir = str(Path(curve).parent)
            self.output_dir.set(outdir)
            self.log(f"출력 폴더 미지정 → {outdir} 사용")

        try:
            generate_bve_files(
                curve_path=curve,
                structure_path=structure,
                output_dir=outdir,
                index_dict=unflatten_defaults(values),
                alignment_type=self.alignment_type.get(),
                on_progress=self.log,
            )
            self.log("✅ 모든 작업 완료.")
        except Exception as e:
            self.log(f"[오류] {type(e).__name__}: {e}")
            messagebox.showerror("오류", f"실행 중 오류 발생:\n{e}")


if __name__ == "__main__":
    FreeobjApp().mainloop()