"""TXT(X,Y) -> Project -> 엔진 -> OUT 전체 파이프라인 스모크 테스트 (A8C 의 IP 좌표 사용)"""
import math, re, os, tempfile
from ip2_engine import parse_dat_multi, solve_curve
from alignment import *
import out_writer as W

dat = parse_dat_multi(open("c:/temp/s97.DAT", encoding="cp949").read())
f, l = dat[0], dat[-1]
def pt(ip, az, d): a = math.radians(az); return (ip.ip_n + d*math.cos(a), ip.ip_e + d*math.sin(a))
pts = [pt(f, f.az_in_deg + 180, 700)] + [(i.ip_n, i.ip_e) for i in dat] + [pt(l, l.az_out_deg, 700)]
tmp = tempfile.mkdtemp(); txt = os.path.join(tmp, "points.txt")
open(txt, "w").write("\n".join(f"{x:.4f},{y:.4f}" for x, y in pts) + "\n")      # 헤더 없는 X,Y
params = [dict(R=i.R, B=i.B, A2=i.A2, D=i.D, L=i.L) for i in dat]

pts2 = read_xy_txt(txt)
prj = project_from_points(pts2, params, start_station=f.ip_sta - 700, chain=20)
inputs, info = build_inputs(prj)
print("읽은 점", len(pts2), "개 → IP", len(inputs), "개, 경고:", prj.warnings or "없음")
text = W.render(inputs)
print("생성 OUT:", text.count("\r\n"), "줄,", text.count("\f"), "개 블록")
# 원본과 IP 단위로 대조 (IP1~8 은 측점까지 같음)
ref = open("c:/temp/a8c.out", "rb").read().decode("cp949").replace("\r", "")
ref_blocks = ref.split("\f")[1:]; my_blocks = text.replace("\r", "").split("\f")[1:]
tok = re.compile(r"\d*\.\d+|\d+")
sk = lambda s: tok.sub(lambda m: re.sub(r"\d", "9", m.group()), s)
print("\nIP   줄수(원본/생성)  서식불일치  숫자최대차")
for k, (a, b) in enumerate(zip(ref_blocks, my_blocks), 1):
    la, lb = a.split("\n"), b.split("\n"); bad = 0; mx = 0
    for x, y in zip(la, lb):
        if x == y: continue
        if sk(x) != sk(y): bad += 1; continue
        mx = max(mx, max(abs(float(p)-float(q)) for p, q in zip(tok.findall(x), tok.findall(y))))
    print(f"{k:>3}   {len(la)}/{len(lb)}        {bad:>3}       {mx:.4f}")
# DAT 내보내기 왕복
p2 = os.path.join(tmp, "x.dat"); write_dat(p2, inputs)
back = parse_dat_multi(open(p2, encoding="cp949").read())
print("\nDAT 왕복:", all(abs(a.R-b.R)<1e-6 and abs(a.ip_sta-b.ip_sta)<1e-5 and abs(a.ia_deg-b.ia_deg)<3e-6 for a, b in zip(inputs, back)), "(IA 는 0.01″ 단위로 저장)")
open("c:/temp/A8C_from_xy.OUT", "wb").write(text.encode("cp949"))
