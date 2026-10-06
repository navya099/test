#!/usr/bin/env python3
"""Civil 3D sampled alignment -> fixed 25 m BVE alignment converter.

Project conventions:
- Horizontal target: down-line incremental station report (Northing/Easting/bearing).
- Vertical target: design elevation from longitudinal elevation report.
- BVE x=Northing, z=Easting.
- BVE block interval is fixed at 25 m 3-D track distance.
- Left curve radius is negative; right curve radius is positive.

The converter resamples the Civil 3D alignment on 3-D BVE chainage, derives
Pitch/Radius, optionally optimizes consecutive curve blocks while preserving
curve-end bearing, then re-integrates with ApplyRouteData.py-equivalent maths.
"""
from __future__ import annotations
import argparse, csv, math, re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence
import numpy as np
from scipy.optimize import minimize

BLOCK = 25.0
EPS_TURN = math.radians(1.0 / 3600.0)  # 1 arc-second

@dataclass
class C3DPoint:
    station: float; northing: float; easting: float; bearing_deg: float; elevation: float

@dataclass
class BVENode:
    track_position: float; c3d_station: float; northing: float; easting: float
    elevation: float; bearing_deg: float

@dataclass
class BVEBlock:
    track_position: float; c3d_station: float; radius: float; pitch: float
    target_n: float; target_e: float; target_z: float; target_bearing_deg: float


def wrap_rad(x: float) -> float:
    return (x + math.pi) % (2 * math.pi) - math.pi


def parse_station(v) -> float:
    s = str(v).strip().replace(',', '')
    if '+' in s:
        a,b=s.split('+',1); return float(a)*1000.0+float(b)
    return float(s)


def parse_m(v) -> float:
    m=re.search(r'[-+]?\d+(?:\.\d+)?',str(v).replace(',',''))
    if not m: raise ValueError(f'Cannot parse number: {v!r}')
    return float(m.group())


def parse_bearing(v) -> float:
    s=str(v).strip()
    m=re.search(r'N\s*(\d+)\D+(\d+)\D+(\d+(?:\.\d+)?)',s,re.I)
    if m: return float(m[1])+float(m[2])/60+float(m[3])/3600
    return float(s)


def _rows(path: str):
    p=Path(path)
    if p.suffix.lower()=='.csv':
        for enc in ('utf-8-sig','cp949','utf-8'):
            try:
                with p.open(encoding=enc,newline='') as f: return list(csv.reader(f))
            except UnicodeDecodeError: pass
        raise ValueError(f'Cannot decode {p}')
    if p.suffix.lower()=='.xls':
        try: import xlrd
        except ImportError as e:
            raise RuntimeError('Legacy .XLS input requires xlrd. Install: pip install xlrd') from e
        sh=xlrd.open_workbook(str(p)).sheet_by_index(0)
        return [sh.row_values(i) for i in range(sh.nrows)]
    raise ValueError('Input must be .csv or legacy .xls')


def load_horizontal(path: str):
    rows=_rows(path); hdr=None
    for i,r in enumerate(rows):
        names=[str(x).strip() for x in r]
        if '측점' in names and 'Northing' in names and 'Easting' in names and '접선 방향' in names:
            hdr=(i,names); break
    if not hdr: raise ValueError('Horizontal header not found')
    i,n=hdr; ix={k:n.index(k) for k in ('측점','Northing','Easting','접선 방향')}; out=[]
    for r in rows[i+1:]:
        try: out.append((parse_station(r[ix['측점']]),parse_m(r[ix['Northing']]),parse_m(r[ix['Easting']]),parse_bearing(r[ix['접선 방향']])))
        except (ValueError,IndexError): continue
    return out


def load_vertical(path: str):
    rows=_rows(path); hdr=None
    for i,r in enumerate(rows):
        names=[str(x).strip() for x in r]
        if '측점' in names and '표고 설계' in names: hdr=(i,names); break
    if not hdr: raise ValueError('Vertical header not found')
    i,n=hdr; si=n.index('측점'); zi=n.index('표고 설계'); out=[]
    for r in rows[i+1:]:
        try: out.append((parse_station(r[si]),parse_m(r[zi])))
        except (ValueError,IndexError): continue
    return out


def interp_angle_deg(x, xs, degs):
    u=np.unwrap(np.radians(degs)); return float(np.degrees(np.interp(x,xs,u))%360.0)


def combine(horizontal, vertical) -> list[C3DPoint]:
    hs=np.array([x[0] for x in horizontal]); vs=np.array([x[0] for x in vertical]); vz=np.array([x[1] for x in vertical])
    lo=max(hs[0],vs[0]); hi=min(hs[-1],vs[-1]); out=[]
    for s,n,e,a in horizontal:
        if lo-1e-9<=s<=hi+1e-9: out.append(C3DPoint(s,n,e,a,float(np.interp(s,vs,vz))))
    if len(out)<2: raise ValueError('No common station range')
    return out


def resample_bve(points: Sequence[C3DPoint], block=BLOCK) -> list[BVENode]:
    S=np.array([p.station for p in points]); N=np.array([p.northing for p in points]); E=np.array([p.easting for p in points]); Z=np.array([p.elevation for p in points]); A=np.unwrap(np.radians([p.bearing_deg for p in points]))
    dS=np.diff(S); dZ=np.diff(Z); D=np.r_[0.0,np.cumsum(np.hypot(dS,dZ))]
    Dj=np.arange(0.0,math.floor(D[-1]/block)*block+1e-9,block); Sj=np.interp(Dj,D,S)
    return [BVENode(float(d),float(s),float(np.interp(s,S,N)),float(np.interp(s,S,E)),float(np.interp(s,S,Z)),float(np.degrees(np.interp(s,S,A))%360)) for d,s in zip(Dj,Sj)]


def derive_blocks(nodes: Sequence[BVENode], left_negative=True) -> list[BVEBlock]:
    out=[]
    for a,b in zip(nodes[:-1],nodes[1:]):
        ds=b.c3d_station-a.c3d_station; dz=b.elevation-a.elevation; pitch=dz/ds
        turn=wrap_rad(math.radians(b.bearing_deg-a.bearing_deg))
        # Mathematical positive turn in (North,East) is clockwise/right. BVE convention requested: left negative, right positive.
        radius=0.0 if abs(turn)<EPS_TURN else ds/turn
        out.append(BVEBlock(a.track_position,a.c3d_station,radius,pitch,a.northing,a.easting,a.elevation,a.bearing_deg))
    return out


def integrate(nodes: Sequence[BVENode], blocks: Sequence[BVEBlock], block=BLOCK):
    n,e,z=nodes[0].northing,nodes[0].easting,nodes[0].elevation; th=math.radians(nodes[0].bearing_deg); rec=[(0.0,n,e,z,math.degrees(th)%360)]
    for b in blocks:
        s=block/math.sqrt(1+b.pitch*b.pitch); h=s*b.pitch
        if b.radius:
            turn=s/b.radius; chord=2*abs(b.radius)*math.sin(abs(turn)/2); th_mid=th+turn/2; n+=math.cos(th_mid)*chord; e+=math.sin(th_mid)*chord; th+=turn
        else: n+=math.cos(th)*s; e+=math.sin(th)*s
        z+=h; rec.append((b.track_position+block,n,e,z,math.degrees(th)%360))
    return rec


def curve_groups(blocks: Sequence[BVEBlock]):
    groups=[]; start=None; sign=0
    for i,b in enumerate(blocks):
        s=0 if b.radius==0 else (1 if b.radius>0 else -1)
        if s and start is None: start=i; sign=s
        elif start is not None and s!=sign:
            groups.append((start,i-1)); start=i if s else None; sign=s
    if start is not None: groups.append((start,len(blocks)-1))
    return groups


def optimize_radii(nodes: Sequence[BVENode], blocks: list[BVEBlock], end_weight=200.0, regularization=1e-4):
    """Optimize each consecutive curve group. Sum of turns is constrained, so end bearing is preserved."""
    # Process sequentially; start pose for each group comes from current complete alignment.
    for a,b in curve_groups(blocks):
        pre=integrate(nodes[:a+1],blocks[:a])[-1] if a else (0,nodes[0].northing,nodes[0].easting,nodes[0].elevation,nodes[0].bearing_deg)
        _,n0,e0,z0,deg0=pre; idx=list(range(a,b+1)); svals=np.array([BLOCK/math.sqrt(1+blocks[i].pitch**2) for i in idx])
        k0=np.array([svals[j]/blocks[i].radius for j,i in enumerate(idx)])
        total=float(k0.sum())
        def f(k):
            n,e,th=n0,e0,math.radians(deg0); val=0.0
            for j,i in enumerate(idx):
                turn=k[j]; chord=svals[j] if abs(turn)<1e-12 else 2*(svals[j]/abs(turn))*math.sin(abs(turn)/2)
                tm=th+turn/2; n+=math.cos(tm)*chord; e+=math.sin(tm)*chord; th+=turn
                q=nodes[i+1]; err=(n-q.northing)**2+(e-q.easting)**2; val+=err*(end_weight if i==b else 1.0)
            val+=regularization*float(np.sum((k-k0)**2)); return val
        cons={'type':'eq','fun':lambda k: float(np.sum(k)-total)}
        sol=minimize(f,k0,method='SLSQP',constraints=[cons],options={'maxiter':300,'ftol':1e-12})
        if sol.success:
            for j,i in enumerate(idx): blocks[i].radius=0.0 if abs(sol.x[j])<EPS_TURN else svals[j]/sol.x[j]
    return blocks


def validation(nodes,blocks):
    rec=integrate(nodes,blocks); errs=[]; aerrs=[]
    for r,q in zip(rec,nodes):
        errs.append(math.hypot(r[1]-q.northing,r[2]-q.easting)); aerrs.append(abs(math.degrees(wrap_rad(math.radians(r[4]-q.bearing_deg)))))
    im=int(np.argmax(errs)); return {'max_xy_m':max(errs),'max_xy_track_position':nodes[im].track_position,'rms_xy_m':float(np.sqrt(np.mean(np.square(errs)))),'max_bearing_deg':max(aerrs),'end_xy_m':errs[-1]}


def write_csv(path,nodes,blocks):
    with open(path,'w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f); w.writerow(['TrackPosition','C3DStation','Radius','Pitch','TargetNorthing','TargetEasting','TargetElevation','TargetBearing'])
        for b in blocks: w.writerow([f'{b.track_position:.3f}',f'{b.c3d_station:.6f}',f'{b.radius:.6f}',f'{b.pitch:.9f}',f'{b.target_n:.4f}',f'{b.target_e:.4f}',f'{b.target_z:.4f}',f'{b.target_bearing_deg:.9f}'])


def write_curve(path,blocks,cant=0.0,curve_type=0):
    with open(path,'w',encoding='utf-8') as f:
        for b in blocks:
            # Radius 0 explicitly restores straight track; commands remain on 25 m BVE positions only.
            r=0.0 if abs(b.radius)>1e12 else b.radius
            f.write(f'{b.track_position:g},.curve {r:.6f};{cant:g};\n')

def write_pitch(blocks):
    path = r'c:/temp/종단선형.txt'
    with open(path,'w',encoding='utf-8') as f:
        for b in blocks:
            p= b.pitch * 1000
            f.write(f'{b.track_position:g},.pitch {p:.6f};\n')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('horizontal'); ap.add_argument('vertical'); ap.add_argument('-o','--output-prefix',default='c:/temp/평면선형'); ap.add_argument('--no-optimize',action='store_true'); ap.add_argument('--cant',type=float,default=0.0); ap.add_argument('--curve-type',type=int,default=0); args=ap.parse_args()
    pts=combine(load_horizontal(args.horizontal),load_vertical(args.vertical)); nodes=resample_bve(pts); blocks=derive_blocks(nodes)
    before=validation(nodes,blocks)
    if not args.no_optimize: blocks=optimize_radii(nodes,blocks)
    after=validation(nodes,blocks)
    write_csv(args.output_prefix+'.csv',nodes,blocks);
    write_curve(args.output_prefix+'.txt',blocks,args.cant,args.curve_type)
    write_pitch(blocks)
    print('nodes:',len(nodes),'blocks:',len(blocks)); print('baseline:',before); print('final:',after); print('written:',args.output_prefix+'.csv',args.output_prefix+'.txt')

if __name__=='__main__': main()
