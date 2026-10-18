"""
cloxy_app.py - 철도 클로소이드 선형 계산기 (CLOXY 이식판) 의 tkinter UI

표(BP, IP1..IPn, EP × X, Y, R, L, B, A", D)로 입력 → 자동 계산 → 평면 미리보기 / 결과 / OUT·DXF·DAT 출력
"""
from __future__ import annotations
import math, os, re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from project_model import ProjectModel, Row, COLS, L_REFS
import out_writer
from ip2_engine import deg_to_dms

HEAD = {"name": "구분", "x": "X (북)", "y": "Y (동)", "R": "R", "L": "L", "B": "B", "A2": 'A"', "D": "D"}
WIDTH = {"name": 60, "x": 100, "y": 100, "R": 62, "L": 62, "B": 48, "A2": 52, "D": 48}
LINE_STYLE = {"outside": ("#d9480f", "바깥선"), "center": ("#212529", "중앙선"), "inside": ("#1971c2", "안쪽선")}
L_REF_LABEL = {"outside": "바깥선 (원본 프로그램 방식)", "center": "중앙선", "inside": "안쪽선"}
DXF_LABEL = {"local": "로컬: IP별 파일 (원점=IP)", "global": "전체 좌표: 한 파일"}


def _fmt(col, v):
    if v is None:
        return ""
    return f"{v:.4f}" if col in ("x", "y") else f"{v:g}"


# ====================================================================== 평면 미리보기
class PlanView(tk.Canvas):
    def __init__(self, master, **kw):
        super().__init__(master, background="white", highlightthickness=0, **kw)
        self.lines, self.ips, self.ends, self.sel = [], [], [], None
        self.scale, self.cE, self.cN = 1.0, 0.0, 0.0
        self._drag = None
        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<B1-Motion>", self._move)
        self.bind("<MouseWheel>", self._wheel)
        self.bind("<Button-4>", lambda e: self._zoom(e, 1.25))
        self.bind("<Button-5>", lambda e: self._zoom(e, 0.8))
        self.bind("<Double-Button-1>", lambda e: self.fit())

    def set_data(self, lines, ips, ends, refit=True):
        self.lines, self.ips, self.ends = lines, ips, ends
        if refit:
            self.fit()
        else:
            self.redraw()

    def highlight(self, ip_no):
        self.sel = ip_no
        self.redraw()

    def _pts(self):
        p = [q for _, _, pts in self.lines for q in pts] + [(e, n) for _, e, n in self.ips] + [(e, n) for _, e, n in self.ends]
        return p

    def fit(self):
        p = self._pts()
        w, h = max(self.winfo_width(), 50), max(self.winfo_height(), 50)
        if not p:
            self.scale, self.cE, self.cN = 1.0, 0.0, 0.0
        else:
            e0, e1 = min(q[0] for q in p), max(q[0] for q in p)
            n0, n1 = min(q[1] for q in p), max(q[1] for q in p)
            self.cE, self.cN = (e0 + e1) / 2, (n0 + n1) / 2
            self.scale = 0.9 * min(w / max(e1 - e0, 1e-6), h / max(n1 - n0, 1e-6))
        self.redraw()

    def _xy(self, e, n):
        return ((e - self.cE) * self.scale + self.winfo_width() / 2, self.winfo_height() / 2 - (n - self.cN) * self.scale)

    def redraw(self):
        self.delete("all")
        if not self.ends and not self.lines:
            self.create_text(self.winfo_width() / 2, self.winfo_height() / 2, text="TXT 좌표를 불러오거나 표에 X, Y 를 입력하세요", fill="#868e96")
            return
        poly = [self._xy(e, n) for _, e, n in self.ends[:1] + self.ips + self.ends[-1:]] if self.ends else []
        if len(poly) >= 2:
            self.create_line(*[c for q in poly for c in q], fill="#adb5bd", dash=(4, 3))
        for ip_no, name, pts in self.lines:
            col, _ = LINE_STYLE[name]
            width = 3 if ip_no == self.sel else 1.4
            if len(pts) >= 2:
                self.create_line(*[c for q in pts for c in self._xy(*q)], fill=col, width=width)
        for ip_no, e, n in self.ips:
            x, y = self._xy(e, n)
            r = 5 if ip_no == self.sel else 3
            self.create_oval(x - r, y - r, x + r, y + r, outline="#c92a2a", fill="#ffe3e3" if ip_no != self.sel else "#ff8787")
            self.create_text(x + 8, y - 8, text=f"IP{ip_no}", anchor="w", fill="#c92a2a", font=("TkDefaultFont", 9, "bold" if ip_no == self.sel else "normal"))
        for name, e, n in self.ends:
            x, y = self._xy(e, n)
            self.create_rectangle(x - 4, y - 4, x + 4, y + 4, outline="#2b8a3e", fill="#d3f9d8")
            self.create_text(x + 8, y - 8, text=name, anchor="w", fill="#2b8a3e")
        self._scalebar()

    def _scalebar(self):
        if self.scale <= 0:
            return
        target = 100 / self.scale * 1.0                         # 화면 100px 에 해당하는 m
        mag = 10 ** math.floor(math.log10(target))
        for m in (1, 2, 5, 10):
            if m * mag >= target * 0.6:
                length = m * mag
                break
        px = length * self.scale
        x0, y0 = 14, self.winfo_height() - 16
        self.create_line(x0, y0, x0 + px, y0, width=2)
        self.create_text(x0, y0 - 8, anchor="w", text=f"{length:g} m")

    def _press(self, e):
        self._drag = (e.x, e.y)

    def _move(self, e):
        if self._drag:
            dx, dy = e.x - self._drag[0], e.y - self._drag[1]
            self.cE -= dx / self.scale
            self.cN += dy / self.scale
            self._drag = (e.x, e.y)
            self.redraw()

    def _wheel(self, e):
        self._zoom(e, 1.25 if e.delta > 0 else 0.8)

    def _zoom(self, e, f):
        e0 = self.cE + (e.x - self.winfo_width() / 2) / self.scale
        n0 = self.cN - (e.y - self.winfo_height() / 2) / self.scale
        self.scale *= f
        self.cE = e0 - (e.x - self.winfo_width() / 2) / self.scale
        self.cN = n0 + (e.y - self.winfo_height() / 2) / self.scale
        self.redraw()


# ====================================================================== 메인 앱
class App:
    def __init__(self, root: tk.Tk | None = None, model: ProjectModel | None = None):
        self.root = root or tk.Tk()
        self.m = model or ProjectModel()
        self.root.title("CLOXY 선형 계산기 — 클로소이드 완화곡선 (표 입력)")
        self.root.geometry("1280x760")
        self._edit = None
        self._after = None
        self._build_menu()
        self._build_toolbar()
        self._build_settings()
        self._build_body()
        self.status = ttk.Label(self.root, anchor="w", relief="sunken")
        self.status.pack(side="bottom", fill="x")
        self.refresh_table()
        self.compute()

    # ------------------------------------------------------------ 위젯
    def _build_menu(self):
        mb = tk.Menu(self.root)
        f = tk.Menu(mb, tearoff=0)
        f.add_command(label="새 프로젝트", command=self.cmd_new)
        f.add_command(label="TXT 좌표 불러오기 (X,Y)...", command=self.cmd_load_points)
        f.add_command(label="원본 DAT 가져오기...", command=self.cmd_import_dat)
        f.add_separator()
        f.add_command(label="프로젝트 열기...", command=self.cmd_open)
        f.add_command(label="프로젝트 저장", command=self.cmd_save)
        f.add_command(label="다른 이름으로 저장...", command=lambda: self.cmd_save(True))
        f.add_separator()
        f.add_command(label="종료", command=self.root.destroy)
        mb.add_cascade(label="파일", menu=f)
        o = tk.Menu(mb, tearoff=0)
        o.add_command(label="OUT 저장...", command=self.cmd_out)
        o.add_command(label="DXF 저장...", command=self.cmd_dxf)
        o.add_command(label="DAT 내보내기 (원본 호환)...", command=self.cmd_dat)
        mb.add_cascade(label="출력", menu=o)
        h = tk.Menu(mb, tearoff=0)
        h.add_command(label="입력 항목 설명", command=self.cmd_help)
        mb.add_cascade(label="도움말", menu=h)
        self.root.config(menu=mb)

    def _build_toolbar(self):
        tb = ttk.Frame(self.root, padding=(6, 4))
        tb.pack(side="top", fill="x")
        for text, cmd in (("TXT 불러오기", self.cmd_load_points), ("프로젝트 열기", self.cmd_open), ("저장", self.cmd_save)):
            ttk.Button(tb, text=text, command=cmd).pack(side="left", padx=2)
        ttk.Separator(tb, orient="vertical").pack(side="left", fill="y", padx=6)
        for text, cmd in (("OUT 저장", self.cmd_out), ("DXF 저장", self.cmd_dxf), ("DAT 내보내기", self.cmd_dat)):
            ttk.Button(tb, text=text, command=cmd).pack(side="left", padx=2)
        ttk.Separator(tb, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Button(tb, text="전체 보기", command=lambda: self.plan.fit()).pack(side="left", padx=2)

    def _build_settings(self):
        sf = ttk.LabelFrame(self.root, text="프로젝트 설정", padding=(8, 4))
        sf.pack(side="top", fill="x", padx=6)
        self.v_start = tk.StringVar(value=f"{self.m.start_station:g}")
        self.v_chain = tk.StringVar(value=f"{self.m.chain:g}")
        self.v_defB = tk.StringVar(value=f"{self.m.def_B:g}")
        self.v_defD = tk.StringVar(value=f"{self.m.def_D:g}")
        self.v_lref = tk.StringVar(value=L_REF_LABEL[self.m.l_ref])
        self.v_dxf = tk.StringVar(value=DXF_LABEL[self.m.dxf_mode])
        def ent(label, var, w=9):
            ttk.Label(sf, text=label).pack(side="left", padx=(8, 2))
            e = ttk.Entry(sf, textvariable=var, width=w)
            e.pack(side="left")
            e.bind("<Return>", lambda ev: self.on_settings()); e.bind("<FocusOut>", lambda ev: self.on_settings())
            return e
        ent("BP 측점", self.v_start, 11); ent("chain(m)", self.v_chain, 6)
        ent("새 IP 기본 B", self.v_defB, 5); ent("D", self.v_defD, 5)
        ttk.Label(sf, text="L 기준").pack(side="left", padx=(14, 2))
        cb = ttk.Combobox(sf, textvariable=self.v_lref, values=list(L_REF_LABEL.values()), state="readonly", width=24)
        cb.pack(side="left"); cb.bind("<<ComboboxSelected>>", lambda ev: self.on_settings())
        ttk.Label(sf, text="DXF").pack(side="left", padx=(14, 2))
        cd = ttk.Combobox(sf, textvariable=self.v_dxf, values=list(DXF_LABEL.values()), state="readonly", width=24)
        cd.pack(side="left"); cd.bind("<<ComboboxSelected>>", lambda ev: self.on_settings())

    def _build_body(self):
        pw = ttk.PanedWindow(self.root, orient="horizontal")
        pw.pack(fill="both", expand=True, padx=6, pady=4)
        left = ttk.Frame(pw)
        pw.add(left, weight=0)
        bar = ttk.Frame(left)
        bar.pack(fill="x", pady=(0, 3))
        for text, cmd in (("IP 추가", self.cmd_add), ("위에 삽입", self.cmd_insert), ("삭제", self.cmd_delete), ("▲", lambda: self.cmd_move(-1)), ("▼", lambda: self.cmd_move(1))):
            ttk.Button(bar, text=text, width=8 if len(text) > 1 else 3, command=cmd).pack(side="left", padx=1)
        self.tree = ttk.Treeview(left, columns=COLS, show="headings", selectmode="browse", height=24)
        for c in COLS:
            self.tree.heading(c, text=HEAD[c])
            self.tree.column(c, width=WIDTH[c], anchor="e" if c != "name" else "center", stretch=False)
        sb = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        self.tree.tag_configure("end", background="#f1f3f5")
        self.tree.tag_configure("bad", background="#ffe3e3")
        self.tree.bind("<Double-1>", self._dbl)
        self.tree.bind("<Return>", lambda e: self._edit_selected(1))
        self.tree.bind("<F2>", lambda e: self._edit_selected(1))
        self.tree.bind("<Delete>", lambda e: self.cmd_delete())
        self.tree.bind("<Insert>", lambda e: self.cmd_insert())
        self.tree.bind("<Control-v>", self._paste)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        right = ttk.Notebook(pw)
        pw.add(right, weight=1)
        self.plan = PlanView(right)
        right.add(self.plan, text="평면 미리보기")
        rf = ttk.Frame(right)
        right.add(rf, text="결과 요약")
        cols = ("ip", "sta", "ia", "turn", "tl", "cl", "lo", "lc", "li", "btc", "etc")
        names = ("IP", "IP 측점", "교각 IA", "회전", "TL", "CL", "L 바깥", "L 중앙", "L 안쪽", "BTC(최소)", "ETC(최대)")
        wd = (46, 88, 96, 38, 64, 64, 64, 64, 64, 82, 82)
        self.res = ttk.Treeview(rf, columns=cols, show="headings", height=12)
        for c, n, w in zip(cols, names, wd):
            self.res.heading(c, text=n); self.res.column(c, width=w, anchor="e", stretch=False)
        xs = ttk.Scrollbar(rf, orient="horizontal", command=self.res.xview)
        self.res.configure(xscrollcommand=xs.set)
        xs.pack(side="bottom", fill="x")
        self.res.pack(fill="both", expand=True)
        self.res.bind("<<TreeviewSelect>>", self._on_res_select)
        of = ttk.Frame(right)
        right.add(of, text="OUT 요약(선택 IP)")
        self.out_text = tk.Text(of, font="TkFixedFont", wrap="none", height=30)
        self.out_text.pack(fill="both", expand=True)
        mf = ttk.Frame(right)
        right.add(mf, text="경고/오류")
        self.msg = tk.Text(mf, wrap="word", height=10)
        self.msg.pack(fill="both", expand=True)
        self.msg.tag_configure("err", foreground="#c92a2a"); self.msg.tag_configure("warn", foreground="#e67700"); self.msg.tag_configure("ok", foreground="#2b8a3e")
        self.nb = right

    # ------------------------------------------------------------ 표 갱신/편집
    def refresh_table(self, select: int | None = None):
        sel = select if select is not None else self._sel_index()
        self.tree.delete(*self.tree.get_children())
        n = len(self.m.rows)
        for i, r in enumerate(self.m.rows):
            vals = [r.name] + [_fmt(c, getattr(r, c)) for c in COLS[1:]]
            if i in (0, n - 1):
                for k in (3, 4, 5, 6, 7):
                    vals[k] = "—"
            self.tree.insert("", "end", iid=str(i), values=vals, tags=("end",) if i in (0, n - 1) else ())
        self.tree.heading("L", text=f"L({ {'outside':'바깥','center':'중앙','inside':'안쪽'}[self.m.l_ref] })")
        if sel is not None and 0 <= sel < n:
            self.tree.selection_set(str(sel)); self.tree.focus(str(sel))

    def _sel_index(self):
        s = self.tree.selection()
        return int(s[0]) if s else None

    def _dbl(self, ev):
        item = self.tree.identify_row(ev.y)
        col = self.tree.identify_column(ev.x)
        if item and col:
            self._begin_edit(int(item), int(col[1:]) - 1)

    def _edit_selected(self, col_idx):
        i = self._sel_index()
        if i is not None:
            self._begin_edit(i, col_idx)

    def _begin_edit(self, row_idx: int, col_idx: int):
        self._end_edit(commit=True)
        col = COLS[col_idx]
        n = len(self.m.rows)
        if col == "name" or (col in ("R", "L", "B", "A2", "D") and row_idx in (0, n - 1)):
            return
        bbox = self.tree.bbox(str(row_idx), f"#{col_idx + 1}")
        if not bbox:
            return
        x, y, w, h = bbox
        e = ttk.Entry(self.tree)
        e.place(x=x, y=y, width=w, height=h)
        e.insert(0, _fmt(col, getattr(self.m.rows[row_idx], col)))
        e.select_range(0, "end"); e.focus_set()
        e.bind("<Return>", lambda ev: self._finish(row_idx, col_idx, 0, 1))
        e.bind("<Tab>", lambda ev: (self._finish(row_idx, col_idx, 1, 0), "break")[1])
        e.bind("<Escape>", lambda ev: self._end_edit(commit=False))
        e.bind("<FocusOut>", lambda ev: self._end_edit(commit=True))
        self._edit = (e, row_idx, col_idx)

    def _finish(self, row_idx, col_idx, dc, dr):
        self._end_edit(commit=True)
        nc, nr = col_idx + dc, row_idx + dr
        if nc >= len(COLS):
            nc, nr = 1, row_idx + 1
        if 0 <= nr < len(self.m.rows):
            self.tree.selection_set(str(nr)); self.tree.focus(str(nr))
            self._begin_edit(nr, nc)

    def _end_edit(self, commit: bool):
        if not self._edit:
            return
        e, ri, ci = self._edit
        self._edit = None
        text = e.get()
        e.destroy()
        if commit:
            self.commit_cell(ri, COLS[ci], text)

    def commit_cell(self, row_idx: int, col: str, text: str):
        try:
            self.m.set_cell(row_idx, col, text)
        except ValueError:
            self.set_status(f"숫자가 아닌 값입니다: {text!r}")
            return
        self.refresh_table(select=row_idx)
        self.schedule_compute()

    def _paste(self, ev):
        try:
            txt = self.root.clipboard_get()
        except tk.TclError:
            return
        self.paste_points(txt, self._sel_index() or 0)

    def paste_points(self, text: str, start: int = 0):
        pts = []
        for ln in text.splitlines():
            parts = [t for t in re.split(r"[,\t ;]+", ln.strip()) if t]
            if len(parts) >= 2:
                try:
                    pts.append((float(parts[0]), float(parts[1])))
                except ValueError:
                    pass
        if not pts:
            return 0
        while len(self.m.rows) < start + len(pts):
            self.m.insert_ip(None)
        for k, (x, y) in enumerate(pts):
            self.m.rows[start + k].x, self.m.rows[start + k].y = x, y
        self.refresh_table(select=start)
        self.schedule_compute()
        return len(pts)

    # ------------------------------------------------------------ 행 명령
    def cmd_add(self):
        i = self.m.insert_ip(None); self.refresh_table(select=i); self.schedule_compute()

    def cmd_insert(self):
        s = self._sel_index()
        i = self.m.insert_ip(s if s else None); self.refresh_table(select=i); self.schedule_compute()

    def cmd_delete(self):
        s = self._sel_index()
        if s is not None and self.m.delete_row(s):
            self.refresh_table(select=min(s, len(self.m.rows) - 2)); self.schedule_compute()

    def cmd_move(self, d):
        s = self._sel_index()
        if s is not None:
            j = self.m.move_row(s, d); self.refresh_table(select=j); self.schedule_compute()

    # ------------------------------------------------------------ 설정
    def on_settings(self):
        try:
            self.m.start_station = float(self.v_start.get().replace(",", ""))
            ch = float(self.v_chain.get())
            if ch <= 0:
                raise ValueError
            self.m.chain = ch
            self.m.def_B = float(self.v_defB.get()); self.m.def_D = float(self.v_defD.get())
        except ValueError:
            self.set_status("설정 값에 숫자가 아닌 항목이 있습니다 (chain 은 0보다 커야 함)")
            return
        inv = {v: k for k, v in L_REF_LABEL.items()}
        self.m.l_ref = inv.get(self.v_lref.get(), "outside")
        self.m.dxf_mode = {v: k for k, v in DXF_LABEL.items()}.get(self.v_dxf.get(), "local")
        self.refresh_table()
        self.schedule_compute()

    # ------------------------------------------------------------ 계산/표시
    def schedule_compute(self):
        if self._after:
            self.root.after_cancel(self._after)
        self._after = self.root.after(150, self.compute)

    def compute(self):
        self._after = None
        res = self.m.compute()
        self.msg.delete("1.0", "end")
        for e in res.errors:
            self.msg.insert("end", "오류  " + e + "\n", "err")
        for w in res.warnings:
            self.msg.insert("end", "경고  " + w + "\n", "warn")
        if res.ok and not res.warnings:
            self.msg.insert("end", "문제 없음\n", "ok")
        self.res.delete(*self.res.get_children())
        if res.ok:
            for inp, inf, cv in zip(res.inputs, res.info, res.curves):
                d, m_, s = deg_to_dms(inf["ia"])
                lo, lc, li = (cv.lines[k].L for k in ("outside", "center", "inside"))
                btc = min(l.BTC for l in cv.lines.values()); etc = max(l.ETC for l in cv.lines.values())
                self.res.insert("", "end", iid=str(inp.ip_no), values=(
                    f"IP{inp.ip_no}", f"{inf['sta']:.4f}", f"{d}°{m_:02d}′{s:05.2f}″", "좌" if inf["left"] else "우",
                    f"{inf['TL']:.3f}", f"{inf['CL']:.3f}", f"{lo:.3f}", f"{lc:.3f}", f"{li:.3f}", f"{btc:.3f}", f"{etc:.3f}"))
            lines = self.m.preview_lines()
            ips = [(i.ip_no, i.ip_e, i.ip_n) for i in res.inputs]
        else:
            lines, ips = [], []
        rows = self.m.rows
        ends = [(r.name, r.y, r.x) for r in (rows[0], rows[-1]) if r.x is not None and r.y is not None]
        if not res.ok:
            ips = [(k, r.y, r.x) for k, r in enumerate(rows[1:-1], 1) if r.x is not None and r.y is not None]
        self.plan.set_data(lines, ips, ends, refit=True)
        bad = {r.split(":")[0] for r in res.errors}
        for i, r in enumerate(rows):
            if self.tree.exists(str(i)):
                tags = ("end",) if i in (0, len(rows) - 1) else ()
                self.tree.item(str(i), tags=tags + (("bad",) if r.name in bad else ()))
        n = len(res.errors)
        self.set_status(f"오류 {n}건 — '경고/오류' 탭 확인" if n else
                        f"IP {len(res.inputs)}개 계산 완료" + (f" · 경고 {len(res.warnings)}건" if res.warnings else ""))
        self._show_out_summary(self._sel_ip())

    def set_status(self, t):
        self.status.config(text=t)

    def _sel_ip(self):
        i = self._sel_index()
        return i if (i is not None and 1 <= i <= len(self.m.rows) - 2) else None

    def _on_select(self, ev=None):
        ip = self._sel_ip()
        self.plan.highlight(ip)
        self._show_out_summary(ip)
        if ip and self.res.exists(str(ip)) and self.res.selection() != (str(ip),):   # 같을 때는 다시 설정하지 않음(이벤트 되먹임 방지)
            self.res.selection_set(str(ip))

    def _on_res_select(self, ev=None):
        s = self.res.selection()
        if s and self.tree.selection() != (s[0],):
            self.tree.selection_set(s[0]); self.tree.focus(s[0])

    def _show_out_summary(self, ip):
        self.out_text.delete("1.0", "end")
        res = self.m.result
        if not res.ok:
            return
        k = (ip or 1) - 1
        if 0 <= k < len(res.curves):
            txt = "\n".join(out_writer.summary_block(res.curves[k], res.inputs[k].ip_no)).replace("\f", "")
            self.out_text.insert("end", txt.strip("\n"))

    # ------------------------------------------------------------ 파일 명령 (경로를 받는 *_to/from 은 테스트용)
    def cmd_new(self):
        if messagebox.askyesno("새 프로젝트", "현재 표를 지우고 새로 시작할까요?"):
            self.m = ProjectModel(); self.refresh_table(); self.compute()

    def load_points_file(self, path):
        self.m.load_points(path); self.refresh_table(); self.compute()
        self.set_status(f"{os.path.basename(path)}: 점 {len(self.m.rows)}개 읽음 — R, L, A\" 등을 입력하세요")

    def cmd_load_points(self):
        p = filedialog.askopenfilename(title="IP 좌표 TXT (X,Y)", filetypes=[("텍스트", "*.txt *.csv *.xy"), ("모든 파일", "*.*")])
        if p:
            try:
                self.load_points_file(p)
            except Exception as e:
                messagebox.showerror("불러오기 오류", str(e))

    def import_dat_file(self, path):
        self.m.load_legacy_dat(path); self.sync_settings_vars(); self.refresh_table(); self.compute()
        self.set_status("원본 DAT 를 가져왔습니다 — BP/EP 는 DAT 에 없어 임의 위치로 설정되었습니다")

    def cmd_import_dat(self):
        p = filedialog.askopenfilename(title="원본 DAT", filetypes=[("DAT", "*.dat *.DAT"), ("모든 파일", "*.*")])
        if p:
            try:
                self.import_dat_file(p)
            except Exception as e:
                messagebox.showerror("가져오기 오류", str(e))

    def sync_settings_vars(self):
        self.v_start.set(f"{self.m.start_station:g}"); self.v_chain.set(f"{self.m.chain:g}")
        self.v_defB.set(f"{self.m.def_B:g}"); self.v_defD.set(f"{self.m.def_D:g}")
        self.v_lref.set(L_REF_LABEL[self.m.l_ref]); self.v_dxf.set(DXF_LABEL[self.m.dxf_mode])

    def open_project_file(self, path):
        kind = self.m.open_project(path); self.sync_settings_vars(); self.refresh_table(); self.compute()
        self.set_status(f"{os.path.basename(path)} 열기 완료" + (" (DAT: BP/EP 임의 설정)" if kind == "dat" else ""))

    def cmd_open(self):
        p = filedialog.askopenfilename(title="프로젝트 열기", filetypes=[("프로젝트", "*.cxp *.dat *.DAT"), ("모든 파일", "*.*")])
        if p:
            try:
                self.open_project_file(p)
            except Exception as e:
                messagebox.showerror("열기 오류", str(e))

    def save_project_file(self, path):
        res = self.m.save_project(path)
        base = os.path.splitext(path)[0]
        self.set_status(f"저장: {os.path.basename(base)}.cxp" + (f" + {os.path.basename(base)}.dat" if res.ok else " (오류가 있어 DAT 는 만들지 않음)"))

    def cmd_save(self, as_new=False):
        p = self.m.path
        if as_new or not p:
            p = filedialog.asksaveasfilename(title="프로젝트 저장", defaultextension=".cxp", filetypes=[("프로젝트", "*.cxp")])
        if p:
            self.save_project_file(p)

    def _need(self):
        self.compute()
        if not self.m.result.ok:
            messagebox.showwarning("출력", "입력 오류를 먼저 해결하세요 ('경고/오류' 탭 참고)")
            return False
        return True

    def cmd_out(self):
        if self._need():
            p = filedialog.asksaveasfilename(title="OUT 저장", defaultextension=".OUT", filetypes=[("OUT", "*.OUT *.out")])
            if p:
                self.m.write_out(p); self.set_status(f"OUT 저장: {p}")

    def cmd_dxf(self):
        if self._need():
            p = filedialog.asksaveasfilename(title="DXF 저장", defaultextension=".dxf", filetypes=[("DXF", "*.dxf")])
            if p:
                made = self.m.write_dxf(p); self.set_status(f"DXF {len(made)}개 파일 저장")

    def cmd_dat(self):
        if self._need():
            p = filedialog.asksaveasfilename(title="DAT 내보내기", defaultextension=".DAT", filetypes=[("DAT", "*.DAT *.dat")])
            if p:
                self.m.export_dat(p); self.set_status(f"DAT 저장: {p}")

    def cmd_help(self):
        messagebox.showinfo("입력 항목", (
            "R  기준(구조물 중심선) 곡선반경\n"
            "L  완화곡선장 — 어느 선의 L 인지는 '프로젝트 설정 > L 기준'에서 선택\n"
            "    (원본 프로그램의 입력 L 은 바깥선 기준으로 확인됨)\n"
            "B  구조물 중심에서 내측궤도까지의 거리 (곡선부, 확폭 반영 고정값)\n"
            'A" 구조물 중심에서 외측궤도까지의 거리 (곡선부, 확폭 반영 고정값)\n'
            "D  직선부 궤간 (직선에서는 B, A\" 가 모두 D/2)\n\n"
            "BP 측점: BP 의 측점값. IP 측점, 방위각, 교각은 좌표에서 자동 계산됩니다.\n"
            "표 편집: 셀 더블클릭 / Enter, Tab 이동, Delete 삭제, Ctrl+V 로 X,Y 붙여넣기"))

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
