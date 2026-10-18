"""
project_model.py - UI 와 무관한 프로젝트 모델 (표 ↔ 계산 ↔ 파일).

표(행): BP, IP1..IPn, EP   열: X, Y, R, L, B, A", D   (BP/EP 는 X, Y 만)
프로젝트 파일: .cxp (JSON, BP/EP·설정까지 전부) + 같은 이름의 .dat (원본 CLOXY 호환, 교차 검증용)
"""
from __future__ import annotations
import json, math, os
from dataclasses import dataclass, field
from alignment import (Vertex, Project, build_inputs, read_xy_txt, write_dat, azimuth, distance, deflection)
from ip2_engine import solve_curve, frame, parse_dat_multi, station_coord, deg_to_dms
import out_writer, dxf_writer
from fullalign import Full, FullInfo

COLS = ("name", "x", "y", "R", "L", "B", "A2", "D")
L_REFS = {"outside": "바깥선(OUTSIDE)", "center": "중앙선(CENTER)", "inside": "안쪽선(INSIDE)"}


@dataclass
class Row:
    name: str
    x: float | None = None
    y: float | None = None
    R: float | None = None
    L: float | None = None
    B: float | None = None
    A2: float | None = None
    D: float | None = None


@dataclass
class Result:
    inputs: list = field(default_factory=list)
    info: list = field(default_factory=list)
    curves: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    full: object = None                   # fullalign.Full (BP~EP 전체 선형)

    @property
    def ok(self):
        return not self.errors and bool(self.inputs)


class ProjectModel:
    def __init__(self):
        self.rows = [Row("BP"), Row("EP")]
        self.start_station = 0.0
        self.chain = 20.0
        self.l_ref = "outside"
        self.dxf_mode = "local"          # local | global | full
        self.full_out = True              # OUT 끝에 BP~EP 전체 측점 좌표표를 붙임
        self.def_B = 2.2
        self.def_D = 4.4
        self.result = Result()
        self.path = None

    # ------------------------------------------------------------ 행 조작
    @property
    def n_ip(self):
        return len(self.rows) - 2

    def renumber(self):
        self.rows[0].name = "BP"
        self.rows[-1].name = "EP"
        for k, r in enumerate(self.rows[1:-1], 1):
            r.name = f"IP{k}"

    def new_ip(self) -> Row:
        return Row("IP?", None, None, None, None, self.def_B, None, self.def_D)

    def insert_ip(self, before_index: int | None = None) -> int:
        """before_index: rows 의 인덱스 (None 이면 EP 앞). 새 행의 인덱스를 반환"""
        i = len(self.rows) - 1 if before_index is None else max(1, min(before_index, len(self.rows) - 1))
        self.rows.insert(i, self.new_ip())
        self.renumber()
        return i

    def delete_row(self, index: int) -> bool:
        if index <= 0 or index >= len(self.rows) - 1:
            return False                       # BP/EP 는 삭제 불가
        del self.rows[index]
        self.renumber()
        return True

    def move_row(self, index: int, delta: int) -> int:
        j = index + delta
        if not (1 <= index <= len(self.rows) - 2 and 1 <= j <= len(self.rows) - 2):
            return index
        self.rows[index], self.rows[j] = self.rows[j], self.rows[index]
        self.renumber()
        return j

    def set_cell(self, index: int, col: str, text: str):
        r = self.rows[index]
        t = text.strip()
        val = None if t == "" else float(t.replace(",", ""))
        if col in ("R", "L", "B", "A2", "D") and index in (0, len(self.rows) - 1):
            return                              # BP/EP 에는 곡선 값 없음
        setattr(r, col, val)

    # ------------------------------------------------------------ 가져오기
    def load_points(self, path: str):
        """헤더 없는 X,Y TXT: 첫 점 BP, 마지막 점 EP, 가운데는 IP. 기존 IP 의 R/L/B/A"/D 는 순서대로 유지"""
        pts = read_xy_txt(path)
        if len(pts) < 3:
            raise ValueError("점이 3개 이상 필요합니다 (BP, IP 1개 이상, EP)")
        old = [r for r in self.rows[1:-1]]
        rows = [Row("BP", *pts[0])]
        for k, p in enumerate(pts[1:-1]):
            base = old[k] if k < len(old) else self.new_ip()
            rows.append(Row("IP?", p[0], p[1], base.R, base.L, base.B, base.A2, base.D))
        rows.append(Row("EP", *pts[-1]))
        self.rows = rows
        self.renumber()

    def load_legacy_dat(self, path: str, pad: float = 500.0):
        """원본 DAT 가져오기. BP/EP 는 DAT 에 없으므로 첫 IP 진입/마지막 IP 진출 방향으로 pad m 떨어진 임의 점"""
        ips = parse_dat_multi(open(path, encoding="cp949", errors="replace").read())
        if any(i.ip_n is None for i in ips):
            raise ValueError("좌표가 없는 DAT 는 가져올 수 없습니다 (좌표계산 플래그 y 필요)")
        f, l = ips[0], ips[-1]
        a = math.radians(f.az_in_deg + 180); b = math.radians(l.az_out_deg)
        rows = [Row("BP", f.ip_n + pad * math.cos(a), f.ip_e + pad * math.sin(a))]
        for i in ips:
            rows.append(Row("IP?", i.ip_n, i.ip_e, i.R, i.L, i.B, i.A2, i.D))
        rows.append(Row("EP", l.ip_n + pad * math.cos(b), l.ip_e + pad * math.sin(b)))
        self.rows = rows
        self.renumber()
        self.start_station = f.ip_sta - pad
        self.chain = f.sta_step
        self.l_ref = "outside"

    # ------------------------------------------------------------ 계산
    def compute(self) -> Result:
        res = Result()
        rows = self.rows
        for r in rows:
            if r.x is None or r.y is None:
                res.errors.append(f"{r.name}: X, Y 좌표가 비어 있습니다")
        for r in rows[1:-1]:
            for col, label in (("R", "R"), ("L", "L"), ("A2", 'A"'), ("B", "B"), ("D", "D")):
                v = getattr(r, col)
                if v is None or v <= 0:
                    res.errors.append(f"{r.name}: {label} 값이 필요합니다 (0보다 커야 함)")
        if len(rows) < 3:
            res.errors.append("IP 가 최소 1개 필요합니다")
        if res.errors:
            self.result = res
            return res
        verts = [Vertex("BP", rows[0].x, rows[0].y)]
        for r in rows[1:-1]:
            verts.append(Vertex(r.name, r.x, r.y, r.R, r.B, r.A2, r.D, r.L))
        verts.append(Vertex("EP", rows[-1].x, rows[-1].y))
        for a, b in zip(verts, verts[1:]):
            if distance(a, b) < 1e-6:
                res.errors.append(f"{a.name}-{b.name}: 두 점이 같은 위치입니다")
        if res.errors:
            self.result = res
            return res
        prj = Project(verts, self.start_station, self.chain)
        try:
            inputs, info = build_inputs(prj, l_ref=self.l_ref)
        except ValueError as e:
            res.errors.append(str(e)); self.result = res; return res
        res.warnings += prj.warnings
        for inp in inputs:
            try:
                cv = solve_curve(inp)
            except Exception:
                res.errors.append(f"IP{inp.ip_no}: " + self._unsolvable_hint(inp))
                continue
            res.curves.append(cv)
        if res.errors:
            self.result = res
            return res
        # 곡선 간 간섭: 앞 IP 의 ETC 가 다음 IP 의 BTC 를 넘는지
        for k in range(len(res.curves) - 1):
            e = max(l.ETC for l in res.curves[k].lines.values())
            b = min(l.BTC for l in res.curves[k + 1].lines.values())
            if e > b:
                res.warnings.append(f"IP{k + 1}-IP{k + 2}: 곡선이 {e - b:.3f} m 겹칩니다 (앞 곡선 ETC > 다음 곡선 BTC)")
        res.inputs, res.info = inputs, info
        res.full = Full(res.curves, FullInfo((rows[0].x, rows[0].y), (rows[-1].x, rows[-1].y),
                                             self.start_station, prj.ep_station, self.chain))
        self.result = res
        return res

    def _unsolvable_hint(self, inp) -> str:
        msg = "이 R·L·A\"·B·D 조합으로 완화곡선을 풀 수 없습니다 (L 이 너무 크거나 R 이 너무 작음)"
        w = inp.A2 - inp.D / 2
        if getattr(inp, "l_ref", "outside") != "outside" and w > 0:
            msg += (f" — 중앙/안쪽선 기준 L 은 바깥선 L 이 존재하도록 약 {math.sqrt(24 * inp.R * w):.0f} m 이상이어야 합니다"
                    f" (곡선부 확폭 A\"-D/2 = {w:.3f} m)")
        return msg

    # ------------------------------------------------------------ 미리보기 점
    def preview_lines(self, step: float = 3.0):
        """[(ip_no, name, [(E,N)...])] — 전체 좌표계(동, 북)"""
        out = []
        for inp, cv in zip(self.result.inputs, self.result.curves):
            fr = frame(cv)
            for name, ln in cv.lines.items():
                stas = sorted({ln.BTC, ln.BCC, ln.ECC, ln.ETC} | {ln.BTC + k * step for k in range(1, int((ln.ETC - ln.BTC) / step))})
                pts = []
                for s in stas:
                    n, e, _ = station_coord(cv, ln, s, fr)
                    pts.append((e, n))
                out.append((inp.ip_no, name, pts))
        return out

    def preview_straights(self):
        """BP~EP 직선구간 [((E,N),(E,N))] (좌/중/우 궤도)"""
        res = self.result
        if not res.ok or res.full is None:
            return []
        out = []
        for side in ("left", "center", "right"):
            for p, q in res.full.straights(side):
                out.append(((p[1], p[0]), (q[1], q[0])))
        return out

    # ------------------------------------------------------------ 출력/저장
    def write_out(self, path: str, distribution: bool = True):
        self._need_ok()
        out_writer.write_out(path, self.result.inputs, distribution=distribution,
                             full=self.result.full if self.full_out else None)

    def write_dxf(self, path: str) -> list:
        """local: IP 마다 파일(<이름>_IPn.dxf), global: 한 파일.  만든 파일 경로 목록 반환"""
        self._need_ok()
        made = []
        if self.dxf_mode == "full":
            dxf_writer.write_dxf(path, self.result.inputs, mode="full", full=self.result.full); made.append(path)
        elif self.dxf_mode == "global":
            dxf_writer.write_dxf(path, self.result.inputs, mode="global"); made.append(path)
        else:
            base, ext = os.path.splitext(path)
            for inp in self.result.inputs:
                p = f"{base}_IP{inp.ip_no}{ext or '.dxf'}"
                dxf_writer.write_dxf(p, self.result.inputs, mode="local", ip_no=inp.ip_no); made.append(p)
        return made

    def export_dat(self, path: str):
        self._need_ok()
        write_dat(path, self.result.inputs)

    def _need_ok(self):
        if not self.result.ok:
            raise ValueError("계산 결과가 없습니다 — 입력 오류를 먼저 해결하세요")

    def save_project(self, path: str):
        base, _ = os.path.splitext(path)
        data = dict(version=1, start_station=self.start_station, chain=self.chain, l_ref=self.l_ref,
                    dxf_mode=self.dxf_mode, full_out=self.full_out, def_B=self.def_B, def_D=self.def_D,
                    rows=[{k: getattr(r, k) for k in COLS} for r in self.rows])
        with open(base + ".cxp", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        res = self.compute()
        if res.ok:
            write_dat(base + ".dat", res.inputs)          # 프로젝트의 DAT (원본 호환)
        self.path = base + ".cxp"
        return res

    def open_project(self, path: str):
        base, ext = os.path.splitext(path)
        if ext.lower() == ".dat":
            self.load_legacy_dat(path); return "dat"
        data = json.load(open(path, encoding="utf-8"))
        self.rows = [Row(**{k: r.get(k) for k in COLS}) for r in data["rows"]]
        self.start_station = data.get("start_station", 0.0); self.chain = data.get("chain", 20.0)
        self.l_ref = data.get("l_ref", "outside"); self.dxf_mode = data.get("dxf_mode", "local")
        self.full_out = data.get("full_out", True)
        self.def_B = data.get("def_B", 2.2); self.def_D = data.get("def_D", 4.4)
        self.renumber(); self.path = path
        return "cxp"
