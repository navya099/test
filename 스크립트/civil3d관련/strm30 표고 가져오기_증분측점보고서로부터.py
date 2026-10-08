import datetime
import os
import time
from tkinter.filedialog import askopenfilename
import pyproj
import rasterio
import glob
import re
import csv

"""
civil3d 증분 측점 보고서로부터 지표면 종단 생성용 파일 추출(sta, elev)
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

def tm2wgs(coords_array):
    transformed = []
    p1 = pyproj.CRS.from_epsg(5186)
    p2 = pyproj.CRS.from_epsg(4326)
    transformer = pyproj.Transformer.from_crs(p1, p2, always_xy=True)
    for x, y in coords_array:
        lon, lat = transformer.transform(x, y)
        transformed.append((lon, lat))
    return transformed

def get_elevations(coords, dem_files):
    elevations = []
    datasets = [rasterio.open(f) for f in dem_files]
    for lon, lat in coords:
        ele = 0
        for ds in datasets:
            if ds.bounds.left <= lon <= ds.bounds.right and ds.bounds.bottom <= lat <= ds.bounds.top:
                row, col = ds.index(lon, lat)
                from rasterio.windows import Window
                ele = float(ds.read(1, window=Window(col, row, 1, 1))[0, 0])
                break
        elevations.append(ele)
    for ds in datasets:
        ds.close()
    return elevations

def write_file(stations, elevations, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        for sta, ele in zip(stations, elevations):
            f.write(f"{sta} {ele + 100}\n")

# ===== CONFIG =====
input_report = askopenfilename(title="증분 측점 보고서 파일 선택")
input_folder = os.path.dirname(input_report)
output_txt = os.path.join(input_folder, 'elevation.txt')
dem_folder = r"D:\도면\DEM\stm30m"  # DEM 폴더

# DEM 파일명 패턴으로 타일만 선택
dem_files = glob.glob(os.path.join(dem_folder, "n*_e*_1arc_v3*.tif"))
if not dem_files:
    raise ValueError("DEM 파일을 찾을 수 없습니다.")

if not os.path.exists(input_report):
    time.sleep(1)

start_time = datetime.datetime.now()
print(f"작업 시작 시간: {start_time}")

plan_result = load_horizontal(input_report)
print(len(plan_result))
coords_tm = []
stations =[]
for plan in plan_result:
    coords_tm.append([plan[2], plan[1]])
    stations.append(plan[0])
coords = tm2wgs(coords_tm)

# 최소 범위 계산
min_lon = min(lon for lon, lat in coords)
max_lon = max(lon for lon, lat in coords)
min_lat = min(lat for lon, lat in coords)
max_lat = max(lat for lon, lat in coords)

selected_files = []
for f in dem_files:
    name = os.path.basename(f)
    try:
        lat_tile = int(name[1:3])
        lon_tile = int(name[5:8])
    except ValueError:
        continue
    if min_lat-1 <= lat_tile <= max_lat+1 and min_lon-1 <= lon_tile <= max_lon+1:
        selected_files.append(f)

if not selected_files:
    raise ValueError("좌표 범위에 맞는 DEM 파일이 없습니다.")

elevations = get_elevations(coords, selected_files)
write_file(stations, elevations, output_txt)

end_time = datetime.datetime.now()
print(f"표고파일 저장 완료: {output_txt}")
print(f"작업 완료 시간: {end_time}")
print(f"총 소요 시간: {end_time - start_time}")