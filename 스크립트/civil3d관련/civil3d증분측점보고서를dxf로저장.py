from tkinter.filedialog import askopenfilename, askdirectory

import ezdxf
import os
import re
import csv

"""
civil3d 증분 측점 보고서로부터 dxf도면 생성
"""

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
    from pathlib import Path
    p = Path(path)
    if p.suffix.lower() == '.csv':
        for enc in ('utf-8-sig', 'cp949', 'utf-8'):
            try:
                with p.open(encoding=enc, newline='') as f:
                    return list(csv.reader(f))
            except UnicodeDecodeError: pass
        raise ValueError(f'Cannot decode {p}')
    if p.suffix.lower() == '.xls':
        try: import xlrd
        except ImportError as e: raise RuntimeError('Legacy .XLS input requires xlrd. Install: pip install xlrd') from e
        sh = xlrd.open_workbook(str(p)).sheet_by_index(0)
        return [sh.row_values(i) for i in range(sh.nrows)]
    raise ValueError('Input must be .csv or legacy .xls')

#step 파일읽기
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

def main():
    filepath = None
    while True:
        try:
            filepath = askopenfilename(title="Civil3D 보고서 또는 AcadLisp CSV 선택")
            if not filepath:
                raise FileNotFoundError("대상 파일을 찾을 수 없습니다")

            plan_result = load_horizontal(filepath)

            print(f"파일 읽기 성공: {filepath}")
            break

        except Exception as e:
            print(f"오류 발생: 파일: {filepath}는 {e}")
            print("올바른 Civil3D 보고서(.xls) 또는 AcadLisp CSV(.csv)를 선택하세요.")

    # 좌표계 변환 (Civil 좌표계 → 수학 좌표계)
    coords_tm = []
    stations = []
    for plan in plan_result:
        coords_tm.append([plan[2], plan[1]])
        stations.append(plan[0])

    #저장
    filepath_curve = askdirectory()
    if not filepath_curve:
        raise FileNotFoundError('저장 파일 경로가 선택되지 않았습니다.')

    # 곡선 결과 저장
    dxf_file = os.path.join(filepath_curve, '증분측점보고서.dxf')
    create_plan(stations, coords_tm, dxf_file)

def create_plan(chainages, coords, output_path):
    doc = ezdxf.new(dxfversion='R2010')
    msp = doc.modelspace()
    # Create a 3D polyline
    plan_2d_name = "c3d"
    layer_color = 5
    plan_2d_layer = doc.layers.new(name=plan_2d_name, dxfattribs={'color': layer_color})
    msp.add_lwpolyline(coords, dxfattribs={'layer': plan_2d_name, 'const_width': 0})
    doc.saveas(output_path)

if __name__ == '__main__':
    main()