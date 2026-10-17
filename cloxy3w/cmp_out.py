"""생성한 OUT 과 원본 OUT 을 서식(골격) + 수치 허용오차로 대조한다."""
import re, sys, math, collections
from ip2_engine import parse_dat_multi
import out_writer as W

tok = re.compile(r"\d*\.\d+|\d+")
def skeleton(l): return tok.sub(lambda m: re.sub(r"\d","9",m.group()), l)

def load(dat, out, **kw):
    inputs = parse_dat_multi(open(dat, encoding="cp949").read())
    ref_txt = open(out, "rb").read().decode("cp949").replace("\r","")
    present = {int(m) for m in re.findall(r"IP NO\. =\s+(\d+)", ref_txt)}
    inputs = [i for i in inputs if i.ip_no in present]       # 원본 OUT 에 있는 IP 만
    mine = W.render(inputs, **kw).replace("\r","").split("\n")
    return ref_txt.split("\n"), mine

def category(a):
    s = a.strip()
    if s.startswith("|"): return "좌표표"
    if re.match(r"^\d+\+", s): return "단위분포표행"
    if s.startswith(("x =","y =")): return "원중심"
    return (re.split(r"\s{2,}|\(|=", s)[0][:9] or "기타")

def compare(dat, out, **kw):
    ref, mine = load(dat, out, **kw)
    print(f"{out.split('/')[-1]}: 원본 {len(ref)}줄 / 생성 {len(mine)}줄")
    n = min(len(ref), len(mine)); exact = 0
    cat = collections.defaultdict(lambda: [0,0.0]); skel=[]; ex={}
    for i in range(n):
        a, b = ref[i], mine[i]
        if a == b: exact += 1; continue
        if skeleton(a) != skeleton(b): skel.append((i+1,a,b)); continue
        k = category(a)
        d = max(abs(float(x)-float(y)) for x,y in zip(tok.findall(a),tok.findall(b)))
        cat[k][0]+=1; cat[k][1]=max(cat[k][1],d); ex.setdefault(k,(a,b))
    print(f"  완전일치 {exact}/{n}줄 ({100*exact/n:.1f}%) · 서식 불일치 {len(skel)}줄 · 숫자만 다른 줄 {sum(v[0] for v in cat.values())}줄")
    for k,(c,d) in sorted(cat.items(), key=lambda kv:-kv[1][0]): print(f"     {k:10s} {c:4d}줄  최대차 {d:.4f}")
    for ln,a,b in skel[:3]: print(f"  [서식 {ln}] 원본|{a}|\n            생성|{b}|")
    return ex

if __name__ == "__main__":
    up="/mnt/user-data/uploads/"
    for dat,out in (("TEST.DAT","TEST_1.OUT"),("IP2.DAT","IP2.OUT"),("88.dat","88.out"),("A8C.DAT","a8c.out")):
        compare(up+dat, up+out); print()
