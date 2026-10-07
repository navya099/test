#!/usr/bin/env python3
"""Civil 3D -> BVE alignment conversion core (UI independent)."""
from __future__ import annotations
import csv, math, re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence
import numpy as np
from scipy.optimize import minimize

BLOCK = 25.0
EPS_TURN = math.radians(1.0 / 3600.0)

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

@dataclass
class ConversionResult:
    nodes: list[BVENode]
    blocks: list[BVEBlock]
    baseline: dict
    final: dict
    csv_path: str
    curve_path: str
    pitch_path: str

ProgressCallback = Callable[[str], None]

def wrap_rad(x: float) -> float:
    return (x + math.pi) % (2 * math.pi) - math.pi

def parse_station(v) -> float:
    s = str(v).strip().replace(',', '')
    if '+' in s:
        a, b = s.split('+', 1); return float(a) * 1000.0 + float(b)
    return float(s)

def parse_m(v) -> float:
    m = re.search(r'[-+]?\d+(?:\.\d+)?', str(v).replace(',', ''))
    if not m: raise ValueError(f'Cannot parse number: {v!r}')
    return float(m.group())

def parse_bearing(v) -> float:
    s = str(v).strip()
    m = re.search(r'N\s*(\d+)\D+(\d+)\D+(\d+(?:\.\d+)?)', s, re.I)
    if m: return float(m[1]) + float(m[2]) / 60 + float(m[3]) / 3600
    return float(s)

def _rows(path: str):
    p = Path(path)
    if p.suffix.lower() == '.csv':
        for enc in ('utf-8-sig', 'cp949', 'utf-8'):
            try:
                with p.open(encoding=enc, newline='') as f: return list(csv.reader(f))
            except UnicodeDecodeError: pass
        raise ValueError(f'Cannot decode {p}')
    if p.suffix.lower() == '.xls':
        try: import xlrd
        except ImportError as e: raise RuntimeError('Legacy .XLS input requires xlrd. Install: pip install xlrd') from e
        sh = xlrd.open_workbook(str(p)).sheet_by_index(0)
        return [sh.row_values(i) for i in range(sh.nrows)]
    raise ValueError('Input must be .csv or legacy .xls')

def load_horizontal(path: str):
    rows = _rows(path); hdr = None
    for i, r in enumerate(rows):
        names = [str(x).strip() for x in r]
        if all(x in names for x in ('측점','Northing','Easting','접선 방향')): hdr = (i, names); break
    if not hdr: raise ValueError('Horizontal header not found')
    i, n = hdr; ix = {k:n.index(k) for k in ('측점','Northing','Easting','접선 방향')}; out = []
    for r in rows[i+1:]:
        try: out.append((parse_station(r[ix['측점']]), parse_m(r[ix['Northing']]), parse_m(r[ix['Easting']]), parse_bearing(r[ix['접선 방향']])))
        except (ValueError, IndexError): continue
    return out

def load_vertical(path: str):
    rows = _rows(path); hdr = None
    for i, r in enumerate(rows):
        names = [str(x).strip() for x in r]
        if '측점' in names and '표고 설계' in names: hdr = (i, names); break
    if not hdr: raise ValueError('Vertical header not found')
    i, n = hdr; si = n.index('측점'); zi = n.index('표고 설계'); out = []
    for r in rows[i+1:]:
        try: out.append((parse_station(r[si]), parse_m(r[zi])))
        except (ValueError, IndexError): continue
    return out

def combine(horizontal, vertical) -> list[C3DPoint]:
    hs=np.array([x[0] for x in horizontal]); vs=np.array([x[0] for x in vertical]); vz=np.array([x[1] for x in vertical])
    lo=max(hs[0],vs[0]); hi=min(hs[-1],vs[-1]); out=[]
    for s,n,e,a in horizontal:
        if lo-1e-9 <= s <= hi+1e-9: out.append(C3DPoint(s,n,e,a,float(np.interp(s,vs,vz))))
    if len(out)<2: raise ValueError('No common station range')
    return out

def resample_bve(points: Sequence[C3DPoint], block=BLOCK) -> list[BVENode]:
    S=np.array([p.station for p in points]); N=np.array([p.northing for p in points]); E=np.array([p.easting for p in points]); Z=np.array([p.elevation for p in points]); A=np.unwrap(np.radians([p.bearing_deg for p in points]))
    dS=np.diff(S); dZ=np.diff(Z); D=np.r_[0.0,np.cumsum(np.hypot(dS,dZ))]
    Dj=np.arange(0.0,math.floor(D[-1]/block)*block+1e-9,block); Sj=np.interp(Dj,D,S)
    return [BVENode(float(d),float(s),float(np.interp(s,S,N)),float(np.interp(s,S,E)),float(np.interp(s,S,Z)),float(np.degrees(np.interp(s,S,A))%360)) for d,s in zip(Dj,Sj)]

def derive_blocks(nodes: Sequence[BVENode]) -> list[BVEBlock]:
    out=[]
    for a,b in zip(nodes[:-1],nodes[1:]):
        ds=b.c3d_station-a.c3d_station; dz=b.elevation-a.elevation; pitch=dz/ds
        turn=wrap_rad(math.radians(b.bearing_deg-a.bearing_deg))
        radius=0.0 if abs(turn)<EPS_TURN else ds/turn
        out.append(BVEBlock(a.track_position,a.c3d_station,radius,pitch,a.northing,a.easting,a.elevation,a.bearing_deg))
    return out

def integrate(nodes: Sequence[BVENode], blocks: Sequence[BVEBlock], block=BLOCK):
    n,e,z=nodes[0].northing,nodes[0].easting,nodes[0].elevation; th=math.radians(nodes[0].bearing_deg); rec=[(0.0,n,e,z,math.degrees(th)%360)]
    for b in blocks:
        s=block/math.sqrt(1+b.pitch*b.pitch); h=s*b.pitch
        if b.radius:
            turn=s/b.radius; chord=2*abs(b.radius)*math.sin(abs(turn)/2); th_mid=th+turn/2
            n+=math.cos(th_mid)*chord; e+=math.sin(th_mid)*chord; th+=turn
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

def optimize_radii(nodes: Sequence[BVENode], blocks: list[BVEBlock], end_weight=200.0, regularization=1e-4, progress: ProgressCallback|None=None):
    groups=curve_groups(blocks)
    for gi,(a,b) in enumerate(groups,1):
        if progress: progress(f'곡선 최적화 {gi}/{len(groups)}  Track {blocks[a].track_position:g}~{blocks[b].track_position+BLOCK:g} m')
        pre=integrate(nodes[:a+1],blocks[:a])[-1] if a else (0,nodes[0].northing,nodes[0].easting,nodes[0].elevation,nodes[0].bearing_deg)
        _,n0,e0,_,deg0=pre; idx=list(range(a,b+1)); svals=np.array([BLOCK/math.sqrt(1+blocks[i].pitch**2) for i in idx])
        k0=np.array([svals[j]/blocks[i].radius for j,i in enumerate(idx)]); total=float(k0.sum())
        def f(k):
            n,e,th=n0,e0,math.radians(deg0); val=0.0
            for j,i in enumerate(idx):
                turn=k[j]; chord=svals[j] if abs(turn)<1e-12 else 2*(svals[j]/abs(turn))*math.sin(abs(turn)/2)
                tm=th+turn/2; n+=math.cos(tm)*chord; e+=math.sin(tm)*chord; th+=turn
                q=nodes[i+1]; err=(n-q.northing)**2+(e-q.easting)**2; val+=err*(end_weight if i==b else 1.0)
            return val+regularization*float(np.sum((k-k0)**2))
        cons={'type':'eq','fun':lambda k: float(np.sum(k)-total)}
        sol=minimize(f,k0,method='SLSQP',constraints=[cons],options={'maxiter':300,'ftol':1e-12})
        if sol.success:
            for j,i in enumerate(idx): blocks[i].radius=0.0 if abs(sol.x[j])<EPS_TURN else svals[j]/sol.x[j]
        elif progress: progress(f'경고: 곡선 {gi} 최적화 실패 - {sol.message}')
    return blocks

def validation(nodes, blocks):
    rec=integrate(nodes,blocks); errs=[]; aerrs=[]
    for r,q in zip(rec,nodes):
        errs.append(math.hypot(r[1]-q.northing,r[2]-q.easting)); aerrs.append(abs(math.degrees(wrap_rad(math.radians(r[4]-q.bearing_deg)))))
    im=int(np.argmax(errs))
    return {'max_xy_m':max(errs),'max_xy_track_position':nodes[im].track_position,'rms_xy_m':float(np.sqrt(np.mean(np.square(errs)))),'max_bearing_deg':max(aerrs),'end_xy_m':errs[-1]}

def write_csv(path,nodes,blocks):
    with open(path,'w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f); w.writerow(['TrackPosition','C3DStation','Radius','Pitch','TargetNorthing','TargetEasting','TargetElevation','TargetBearing'])
        for b in blocks: w.writerow([f'{b.track_position:.3f}',f'{b.c3d_station:.6f}',f'{b.radius:.6f}',f'{b.pitch:.9f}',f'{b.target_n:.4f}',f'{b.target_e:.4f}',f'{b.target_z:.4f}',f'{b.target_bearing_deg:.9f}'])

def write_curve(path,blocks,cant=0.0):
    with open(path,'w',encoding='utf-8') as f:
        for b in blocks:
            r=0.0 if abs(b.radius)>1e12 else b.radius
            f.write(f'{b.track_position:g},.curve {r:.6f};{cant:g};\n')

def write_pitch(path,blocks):
    with open(path,'w',encoding='utf-8') as f:
        for b in blocks: f.write(f'{b.track_position:g},.pitch {b.pitch*1000:.6f};\n')

def convert(horizontal_path: str, vertical_path: str, output_prefix: str, optimize: bool=True, cant: float=0.0, progress: ProgressCallback|None=None) -> ConversionResult:
    def msg(s):
        if progress: progress(s)
    msg('수평 보고서 읽는 중...'); horizontal=load_horizontal(horizontal_path)
    msg('종단 보고서 읽는 중...'); vertical=load_vertical(vertical_path)
    msg('C3D 데이터 결합 및 25 m BVE 체인리지 재샘플링...'); pts=combine(horizontal,vertical); nodes=resample_bve(pts); blocks=derive_blocks(nodes)
    msg('Baseline 검증...'); before=validation(nodes,blocks)
    if optimize:
        msg('Radius 최적화 시작...'); blocks=optimize_radii(nodes,blocks,progress=progress)
    msg('최종 검증...'); after=validation(nodes,blocks)
    prefix=Path(output_prefix); prefix.parent.mkdir(parents=True,exist_ok=True)
    csv_path=str(prefix.with_suffix('.csv')); curve_path=str(prefix.with_suffix('.txt')); pitch_path=str(prefix.parent/'종단선형.txt')
    msg('결과 파일 저장...'); write_csv(csv_path,nodes,blocks); write_curve(curve_path,blocks,cant); write_pitch(pitch_path,blocks)
    msg('완료')
    return ConversionResult(nodes,blocks,before,after,csv_path,curve_path,pitch_path)

#!/usr/bin/env python3
import queue, threading, traceback
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Civil 3D → BVE 선형 변환기')
        self.geometry('820x620'); self.minsize(760,560)
        self.q=queue.Queue(); self.worker=None
        self.horizontal=tk.StringVar(); self.vertical=tk.StringVar(); self.output=tk.StringVar(value=r'c:\temp\평면선형')
        self.optimize=tk.BooleanVar(value=True); self.cant=tk.DoubleVar(value=0.0); self.status=tk.StringVar(value='대기 중')
        self._build(); self.after(100,self._poll)

    def _build(self):
        root=ttk.Frame(self,padding=14); root.pack(fill='both',expand=True); root.columnconfigure(1,weight=1); root.rowconfigure(7,weight=1)
        ttk.Label(root,text='Civil 3D → BVE 실제선형 변환',font=('',16,'bold')).grid(row=0,column=0,columnspan=3,sticky='w',pady=(0,14))
        self._file_row(root,1,'수평 증분측점 보고서',self.horizontal,self._pick_horizontal)
        self._file_row(root,2,'종단 표고차 보고서',self.vertical,self._pick_vertical)
        ttk.Label(root,text='출력 Prefix').grid(row=3,column=0,sticky='w',pady=6); ttk.Entry(root,textvariable=self.output).grid(row=3,column=1,sticky='ew',padx=8); ttk.Button(root,text='선택...',command=self._pick_output).grid(row=3,column=2)
        opt=ttk.LabelFrame(root,text='변환 옵션',padding=10); opt.grid(row=4,column=0,columnspan=3,sticky='ew',pady=10)
        ttk.Checkbutton(opt,text='Radius 최적화 사용',variable=self.optimize).pack(side='left',padx=(0,20)); ttk.Label(opt,text='Cant').pack(side='left'); ttk.Entry(opt,textvariable=self.cant,width=10).pack(side='left',padx=6); ttk.Label(opt,text='BVE Block = 25 m (고정)').pack(side='right')
        bar=ttk.Frame(root); bar.grid(row=5,column=0,columnspan=3,sticky='ew',pady=(0,8)); bar.columnconfigure(1,weight=1)
        self.run_btn=ttk.Button(bar,text='변환 실행',command=self._run); self.run_btn.grid(row=0,column=0,padx=(0,10)); self.pb=ttk.Progressbar(bar,mode='indeterminate'); self.pb.grid(row=0,column=1,sticky='ew'); ttk.Label(bar,textvariable=self.status).grid(row=0,column=2,padx=(10,0))
        ttk.Label(root,text='실행 결과').grid(row=6,column=0,columnspan=3,sticky='w')
        self.log=tk.Text(root,height=20,wrap='word',font=('Consolas',10)); self.log.grid(row=7,column=0,columnspan=3,sticky='nsew',pady=(5,0)); sy=ttk.Scrollbar(root,orient='vertical',command=self.log.yview); sy.grid(row=7,column=3,sticky='ns'); self.log.configure(yscrollcommand=sy.set)

    def _file_row(self,parent,row,label,var,cmd):
        ttk.Label(parent,text=label).grid(row=row,column=0,sticky='w',pady=6); ttk.Entry(parent,textvariable=var).grid(row=row,column=1,sticky='ew',padx=8); ttk.Button(parent,text='찾기...',command=cmd).grid(row=row,column=2)
    def _pick_horizontal(self):
        p=filedialog.askopenfilename(title='수평 증분측점 보고서',filetypes=[('Civil report','*.xls *.csv'),('All files','*.*')]);
        if p:self.horizontal.set(p)
    def _pick_vertical(self):
        p=filedialog.askopenfilename(title='종단 표고차 보고서',filetypes=[('Civil report','*.xls *.csv'),('All files','*.*')]);
        if p:self.vertical.set(p)
    def _pick_output(self):
        p=filedialog.asksaveasfilename(title='출력 Prefix 선택',initialfile='평면선형',defaultextension='',filetypes=[('Output prefix','*.*')]);
        if p:self.output.set(str(Path(p).with_suffix('')))
    def _append(self,s): self.log.insert('end',s+'\n'); self.log.see('end')
    def _run(self):
        if self.worker and self.worker.is_alive(): return
        h,v,o=self.horizontal.get().strip(),self.vertical.get().strip(),self.output.get().strip()
        if not h or not v or not o: messagebox.showwarning('입력 확인','수평 보고서, 종단 보고서, 출력 Prefix를 모두 지정하세요.'); return
        self.log.delete('1.0','end'); self.run_btn.state(['disabled']); self.pb.start(12); self.status.set('계산 중...')
        self.worker=threading.Thread(target=self._work,args=(h,v,o),daemon=True); self.worker.start()
    def _work(self,h,v,o):
        try:
            r=convert(h,v,o,optimize=self.optimize.get(),cant=self.cant.get(),progress=lambda s:self.q.put(('log',s)))
            self.q.put(('done',r))
        except Exception:
            self.q.put(('error',traceback.format_exc()))
    def _fmt_metrics(self,title,m):
        return (f'{title}\n  Max XY : {m["max_xy_m"]*1000:.3f} mm @ Track {m["max_xy_track_position"]:.3f} m\n'
                f'  RMS XY : {m["rms_xy_m"]*1000:.3f} mm\n  Max Bearing : {m["max_bearing_deg"]:.9f}°\n  End XY : {m["end_xy_m"]*1000:.3f} mm')
    def _poll(self):
        try:
            while True:
                typ,data=self.q.get_nowait()
                if typ=='log': self._append(data)
                elif typ=='done':
                    self.pb.stop(); self.run_btn.state(['!disabled']); self.status.set('완료')
                    self._append(''); self._append(f'nodes: {len(data.nodes)}  blocks: {len(data.blocks)}'); self._append(self._fmt_metrics('Baseline',data.baseline)); self._append(self._fmt_metrics('Final',data.final)); self._append(''); self._append('출력 파일:'); self._append('  '+data.csv_path); self._append('  '+data.curve_path); self._append('  '+data.pitch_path)
                    messagebox.showinfo('완료','BVE 선형 변환이 완료되었습니다.')
                elif typ=='error':
                    self.pb.stop(); self.run_btn.state(['!disabled']); self.status.set('오류'); self._append(data); messagebox.showerror('변환 오류','변환 중 오류가 발생했습니다. 실행 결과 창을 확인하세요.')
        except queue.Empty: pass
        self.after(100,self._poll)

if __name__=='__main__': App().mainloop()
