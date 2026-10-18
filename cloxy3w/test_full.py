"""전체(BP~EP) 옵션 검증: OUT 전체 좌표표 + DXF 연속성(끊어진 곳이 BP/EP 뿐인지)"""
import math, os, re, tempfile, collections
import ezdxf
from project_model import ProjectModel

tmp = tempfile.mkdtemp()
for name, path in (("A8C", "/mnt/user-data/uploads/A8C.DAT"), ("S97", "/mnt/user-data/uploads/S97.DAT"), ("88", "/mnt/user-data/uploads/88.dat")):
    m = ProjectModel(); m.load_legacy_dat(path); res = m.compute(); F = res.full
    # ---- OUT
    op = os.path.join(tmp, name + ".OUT"); m.write_out(op)
    txt = open(op, "rb").read().decode("cp949").replace("\r", "")
    sec = txt.split("\f")[-1]
    tabs = re.split(r"\n\s+(left|center|right) x, y", sec)
    rows = {}
    for side, body in zip(tabs[1::2], tabs[2::2]):
        rows[side] = re.findall(r"\|\s*(\d+)K\s*(\d*\.\d+)\s*\|\s*(\d+\.\d+)\s*\|\s*(\d+\.\d+)\s*\|(\S*)\s*\|", body)
    worst = 0
    for side, rs in rows.items():
        for km, mm, x, y, tag in rs[::7]:
            s = int(km) * 1000 + float(mm); n, e = F.point(side, s)
            worst = max(worst, math.hypot(n - float(x), e - float(y)))
    first = {s: (rows[s][0][4], rows[s][-1][4]) for s in rows}
    nrow = {s: len(r) for s, r in rows.items()}
    print(f"[{name}] OUT: 전체 좌표표 3개({nrow}) 첫/끝 비고 {first['center']}  | 표 값과 엔진 값 차이(샘플) {worst:.1e} m  | 파일 {os.path.getsize(op)//1024} KB")
    # ---- DXF full
    m.dxf_mode = "full"; dp = os.path.join(tmp, name + ".dxf"); m.write_dxf(dp)
    doc = ezdxf.readfile(dp); msp = doc.modelspace(); aud = doc.audit()
    cnt = collections.Counter((e.dxftype(), e.dxf.layer) for e in msp)
    ends = collections.defaultdict(list)
    for e in msp:
        L = e.dxf.layer
        if L not in ("LEFT", "CENTER", "RIGHT"): continue
        if e.dxftype() == "LINE":
            ends[L] += [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
        elif e.dxftype() == "POLYLINE":
            v = [(p.dxf.location.x, p.dxf.location.y) for p in e.vertices]; ends[L] += [v[0], v[-1]]
        elif e.dxftype() == "ARC":
            c = e.dxf.center; r = e.dxf.radius
            for a in (e.dxf.start_angle, e.dxf.end_angle):
                ends[L].append((c.x + r * math.cos(math.radians(a)), c.y + r * math.sin(math.radians(a))))
    unmatched = {}
    for L, pts in ends.items():
        un = []
        for i, p in enumerate(pts):
            if not any(j != i and math.dist(p, q) < 1e-5 for j, q in enumerate(pts)): un.append(p)
        unmatched[L] = un
    bp = (m.rows[0].y, m.rows[0].x); ep = (m.rows[-1].y, m.rows[-1].x)
    ok = all(len(v) == 2 for v in unmatched.values())
    cen = unmatched["CENTER"]; okc = ok and sorted([math.dist(cen[0], bp) < 1e-5 or math.dist(cen[0], ep) < 1e-5, math.dist(cen[1], bp) < 1e-5 or math.dist(cen[1], ep) < 1e-5]) == [True, True]
    print(f"      DXF: audit 오류 {len(aud.errors)} | 레이어별 연결 안 된 끝점 수 { {k: len(v) for k, v in unmatched.items()} } → 끊김은 BP/EP 뿐: {okc}")
    print(f"           LINE(직선구간) {sum(v for (t,l),v in cnt.items() if t=='LINE' and l in ('LEFT','CENTER','RIGHT'))}개, CHAIN 눈금 {cnt[('LINE','CHAIN')]}개, 100m 원 {cnt[('CIRCLE','CHAIN')]}개, IP 라벨 {cnt[('TEXT','IPTXT')]}개")
