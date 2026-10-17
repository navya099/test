"""생성 DXF 를 원본 TEST.DXF 와 대조 (전반부/라벨/눈금/격자 서식) + 기하 폐합 검증"""
import math, copy, collections
from ip2_engine import parse_dat_multi
from dxfparse import read_dxf
import dxf_writer as DW

ips=parse_dat_multi(open("c:/temp/S97.DAT",encoding="cp949").read())
inp=copy.copy(next(i for i in ips if i.ip_no==15))
inp.sta_step=20.0
text=DW.render_dxf(ips,mode="global")
open("c:/temp/gen.dxf","w",encoding="cp949",newline="").write(text)
ref=read_dxf("c:/temp/S97.dxf"); gen=read_dxf("c:/temp/gen.dxf")

def stats(es):
    return collections.Counter((x["type"],x["layer"]) for x in es if x["type"] not in("SECTION","ENDSEC","EOF"))
a,b=stats(ref),stats(gen)
print("== 엔티티 구성 (원본 vs 생성) ==")
for k in sorted(set(a)|set(b)):
    mark="" if a[k]==b[k] else "   ← 차이"
    print(f"  {k[0]:9s}{str(k[1]):9s} {a[k]:4d} / {b[k]:4d}{mark}")

# 라벨 문구
tr=[x["xyz"][1].strip() if 1 in x["xyz"] else "" for x in ref if x["type"]=="TEXT"]
tg=[x["xyz"][1].strip() if 1 in x["xyz"] else "" for x in gen if x["type"]=="TEXT"]
print("\n== 라벨 문구 ==  원본 %d개 / 생성 %d개, 집합 일치: %s"%(len(tr),len(tg),sorted(tr)==sorted(tg)))
print("   차이:",sorted(set(tr)^set(tg)) or "없음")
