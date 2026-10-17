import math, collections
def read_dxf(path):
    raw=open(path,encoding="cp949",errors="replace").read().replace("\r","").split("\n")
    pairs=[(int(raw[i].strip()),raw[i+1].strip()) for i in range(0,len(raw)-1,2) if raw[i].strip().lstrip("-").isdigit()]
    ents=[];cur=None
    for code,val in pairs:
        if code==0:
            if cur: ents.append(cur)
            cur={"type":val,"layer":None,"pts":[]} if val in("POLYLINE","VERTEX","LINE","TEXT","CIRCLE","ARC","SEQEND","POINT") else None
            if cur is not None: cur["xyz"]={}
            continue
        if cur is None: continue
        if code==8: cur["layer"]=val
        if code in(10,20,30,11,21,31,40,50,51,1,72,73): cur["xyz"][code]=val
    if cur: ents.append(cur)
    return ents
if __name__=="__main__":
    e=read_dxf("/mnt/user-data/uploads/TEST.DXF")
    print(collections.Counter((x["type"],x["layer"]) for x in e))
    polys=collections.defaultdict(list); layer=None
    for x in e:
        if x["type"]=="POLYLINE": layer=x["layer"]; polys[layer].append([])
        elif x["type"]=="VERTEX": polys[layer][-1].append((float(x["xyz"][10]),float(x["xyz"][20])))
    for l,pl in polys.items():
        for p in pl:
            d=[math.dist(p[i],p[i+1]) for i in range(len(p)-1)]
            print(l,len(p),"first",p[0],"last",p[-1],"seg first5",[round(v,4) for v in d[:5]],"seglast3",[round(v,4) for v in d[-3:]],"len",round(sum(d),3))
    for x in e:
        if x["type"] in("TEXT","LINE","CIRCLE","ARC","POINT"): print(x)
