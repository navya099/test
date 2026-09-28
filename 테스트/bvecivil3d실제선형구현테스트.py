"""Civil 3D -> OpenBVE 25m fixed-block, straight-locked converter.

GUI: choose Civil 3D report (.TXT/.xls/.xlsx) or AcadLisp .csv,
then an existing BVE alignment export (측점,X,Y,Z,Bearing,Radius,Cant,Pitch,height).
The reference BVE export identifies the 13 curve runs and supplies initial radii.
Requires: numpy, scipy, pandas; xlrd for .xls; chardet optional.

The pitch choice affects ONLY the optimizer/simulation. This script does not
edit the BVE vertical alignment. For a pitch-free experiment, remove pitch
from the actual route too before comparing its exported coordinates.
"""
import csv
import math
import os
import re
import sys
from pathlib import Path
from tkinter import Tk, messagebox
from tkinter.filedialog import askopenfilename, askdirectory

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

STATION_RE = re.compile(r'^\s*(\d+)\+(\d+(?:\.\d+)?)\s*$')
DMS_RE = re.compile(r'(\d+(?:\.\d+)?)\s*°\s*(\d+(?:\.\d+)?)\s*[\'′]\s*(\d+(?:\.\d+)?)')


def station_value(value):
    if isinstance(value, str):
        match = STATION_RE.match(value)
        if match:
            return float(match.group(1)) * 1000 + float(match.group(2))
        return float(value.strip().replace(',', ''))
    return float(value)


def parse_bearing(value, mode):
    if mode == 'acadlisp':
        return float(value)
    match = DMS_RE.search(str(value))
    if not match:
        raise ValueError(f'접선 방향을 해석할 수 없습니다: {value!r}')
    deg, minute, second = map(float, match.groups())
    # Civil north-clockwise bearing -> East-CCW math angle.
    return math.radians(90 - deg - minute / 60 - second / 3600)


def load_civil(path):
    """Return [station, Easting(X), Northing(Y), math tangent radians]."""
    ext = Path(path).suffix.lower()
    if ext == '.txt':
        # Civil3D incremental station report: UTF-16 tab-separated.
        rows = []
        for enc in ('utf-16', 'utf-8-sig', 'cp949'):
            try:
                with open(path, encoding=enc, newline='') as f:
                    raw = list(csv.reader(f, delimiter='\t'))
                break
            except (UnicodeError, UnicodeDecodeError):
                continue
        else:
            raise ValueError('TXT 인코딩을 해석할 수 없습니다.')
        for r in raw:
            if len(r) < 4 or not STATION_RE.match(r[0]):
                continue
            try:
                sta = station_value(r[0])
                north = float(r[1].replace(',', '').replace('미터', ''))
                east = float(r[2].replace(',', '').replace('미터', ''))
                heading = parse_bearing(r[3], 'civil3dreport')
                rows.append((sta, east, north, heading))
            except (ValueError, IndexError):
                continue
    elif ext in ('.xls', '.xlsx'):
        # Civil report is often a formatted worksheet with a title and 14 header rows.
        engine = 'xlrd' if ext == '.xls' else 'openpyxl'
        df = pd.read_excel(path, skiprows=14, engine=engine)
        df.columns = [str(c).strip() for c in df.columns]
        if not {'측점', '접선 방향'}.issubset(df.columns):
            raise ValueError('엑셀에서 측점 / 접선 방향 열을 찾지 못했습니다.')
        north_col = next((c for c in df if c in ('Northing', '북거', '북좌표', 'Y')), None)
        east_col = next((c for c in df if c in ('Easting', '동거', '동좌표', 'X')), None)
        if north_col is None or east_col is None:
            raise ValueError('엑셀에서 Northing/Easting 열을 찾지 못했습니다.')
        rows = []
        for _, r in df.iterrows():
            try:
                rows.append((station_value(r['측점']), float(r[east_col]),
                             float(r[north_col]), parse_bearing(r['접선 방향'], 'civil3dreport')))
            except (ValueError, TypeError):
                continue
    elif ext == '.csv':
        df = None
        for enc in ('utf-8-sig', 'cp949', 'utf-16'):
            try:
                candidate = pd.read_csv(path, encoding=enc)
                if {'Display_Station', 'Bearing(Rad)', 'Northing', 'Easting'}.issubset(candidate.columns):
                    df = candidate
                    break
            except (UnicodeError, pd.errors.ParserError):
                continue
        if df is None:
            raise ValueError('AcadLisp CSV 필수 열을 찾지 못했습니다.')
        rows = []
        for _, r in df.iterrows():
            try:
                sta = station_value(r['Real_Station'] if 'Real_Station' in df else r['Display_Station'])
                rows.append((sta, float(r['Easting']), float(r['Northing']),
                             parse_bearing(r['Bearing(Rad)'], 'acadlisp')))
            except (ValueError, TypeError):
                continue
    else:
        raise ValueError('지원 형식: .TXT, .xls, .xlsx, .csv')
    if len(rows) < 3:
        raise ValueError('유효한 Civil 3D 측점이 3개 미만입니다.')
    data = np.asarray(rows, dtype=float)
    data = data[np.argsort(data[:, 0])]
    if np.any(np.diff(data[:, 0]) <= 0):
        raise ValueError('중복 측점이 있습니다.')
    data[:, 3] = np.unwrap(data[:, 3])
    return data


def load_bve_export(path):
    for enc in ('utf-8-sig', 'cp949', 'utf-16'):
        try:
            with open(path, encoding=enc, newline='') as f:
                reader = csv.DictReader(f)
                if not {'측점', 'Radius', 'Pitch'}.issubset(reader.fieldnames or []):
                    continue
                return {round(float(r['측점']), 4): r for r in reader}
        except UnicodeError:
            continue
    raise ValueError('BVE 추출 파일에서 측점, Radius, Pitch 열을 찾지 못했습니다.')


def angle_wrap(value):
    return (value + math.pi) % (2 * math.pi) - math.pi


def chord_move(theta, delta, length):
    half = delta / 2
    sinc = 1 - half**2 / 6 + half**4 / 120 if abs(half) < 1e-4 else math.sin(half) / half
    return length * sinc * np.array((math.cos(theta + half), math.sin(theta + half)))


def identify_runs(original_radius):
    curved = np.abs(original_radius) > 1e-8
    # Preserve latest algorithm: bridge isolated zero-radius block between curves.
    for i in range(1, len(curved) - 1):
        if not curved[i] and curved[i - 1] and curved[i + 1]:
            curved[i] = True
    runs = []
    i = 0
    while i < len(curved):
        if not curved[i]:
            i += 1
            continue
        a = i
        while i < len(curved) and curved[i]:
            i += 1
        runs.append((a, i))
    return runs, curved


def simulate(theta0, deltas, pitches, distances, flat=False):
    xy = np.zeros((len(deltas) + 1, 2))
    headings = np.empty(len(deltas) + 1)
    headings[0] = theta0
    for i, delta in enumerate(deltas):
        # Matches the previously tested straight-locked converter's model.
        # Straight blocks use full 25m; curved blocks use pitch-reduced length.
        horizontal = distances[i] if flat or abs(delta) < 1e-13 else distances[i] / math.sqrt(1 + pitches[i]**2)
        xy[i + 1] = xy[i] + chord_move(headings[i], delta, horizontal)
        headings[i + 1] = headings[i] + delta
    return xy, headings


def solve_curve(civil, pitches, distances, initial_delta, a, b, start_xy, start_theta, flat):
    target_xy = civil[b, 1:3]
    target_theta = civil[b, 3]
    prior = initial_delta[a:b].copy()
    if b < len(distances) and abs(initial_delta[b]) < 1e-12:
        k = b + 1
        while k < len(distances) and abs(initial_delta[k]) < 1e-12:
            k += 1
        vector = civil[k, 1:3] - civil[b, 1:3]
        target_theta = math.atan2(vector[1], vector[0])
    if a > 0 and abs(initial_delta[a - 1]) < 1e-12:
        k = a - 1
        while k > 0 and abs(initial_delta[k - 1]) < 1e-12:
            k -= 1
        vector = civil[a, 1:3] - civil[k, 1:3]
        start_theta = math.atan2(vector[1], vector[0])
    reference = civil[a + 1:b, 1:3]
    def evaluate(z):
        points, angles = simulate(start_theta, z, pitches[a:b], distances[a:b], flat)
        return points + start_xy, angles
    def residual(z):
        points, angles = evaluate(z)
        parts = [(points[-1] - target_xy) * 1e5,
                 np.array([angle_wrap(angles[-1] - target_theta) * 1e7]),
                 (z - prior) * 2]
        if len(reference):
            parts.append(((points[1:-1] - reference) * 0.2).ravel())
        if len(z) >= 3:
            parts.append(np.diff(z, 2) * 0.3)
        return np.concatenate(parts)
    sol = least_squares(residual, prior, method='trf', max_nfev=100,
                        ftol=1e-11, xtol=1e-11, gtol=1e-11)
    points, angles = evaluate(sol.x)
    return sol.x, points, angles, sol.success


def convert(civil_path, bve_path, output_dir, flat=False):
    civil = load_civil(civil_path)
    bve = load_bve_export(bve_path)
    # Only the shared Civil / reference BVE station range can be optimized.
    civil = civil[np.array([round(s, 4) in bve for s in civil[:, 0]])]
    if len(civil) < 3:
        raise ValueError('Civil 3D와 BVE 추출 파일 사이에 공통 측점이 없습니다.')
    station = civil[:, 0]
    ds = np.diff(station)
    if np.any(np.abs(ds - 25) > 1e-6):
        raise ValueError('25m 고정 블록만 지원합니다. 원본 증분 측점 보고서를 확인하세요.')
    original_radius = np.array([float(bve[round(s, 4)]['Radius']) for s in station[:-1]])
    pitch = np.array([float(bve[round(s, 4)]['Pitch']) for s in station[:-1]])
    horizontal = ds if flat else ds / np.sqrt(1 + pitch**2)
    delta = np.divide(-horizontal, original_radius, out=np.zeros(len(ds)), where=np.abs(original_radius) > 1e-9)
    runs, curved = identify_runs(original_radius)
    if not runs:
        raise ValueError('BVE 추출 파일에서 곡선 구간을 찾지 못했습니다.')
    first_curve_start = runs[0][0]
    if first_curve_start == 0:
        initial_theta = civil[0, 3]
    else:
        v = civil[first_curve_start, 1:3] - civil[0, 1:3]
        initial_theta = math.atan2(v[1], v[0])
    theta = initial_theta
    xy = civil[0, 1:3].copy()
    predicted = np.empty((len(civil), 2))
    headings = np.empty(len(civil))
    predicted[0], headings[0] = xy, theta
    diagnostics = []
    runs_by_start = dict(runs)
    i = 0
    while i < len(ds):
        if i in runs_by_start:
            b = runs_by_start[i]
            z, points, angles, success = solve_curve(civil, pitch, ds, delta, i, b, xy, theta, flat)
            delta[i:b] = z
            predicted[i+1:b+1] = points[1:]
            headings[i+1:b+1] = angles[1:]
            xy, theta = points[-1], angles[-1]
            diagnostics.append((station[i], station[b],
                                float(np.linalg.norm(points[-1] - civil[b, 1:3])),
                                math.degrees(angle_wrap(angles[-1] - civil[b, 3])),
                                float(np.max(np.linalg.norm(points - civil[i:b+1, 1:3], axis=1))),
                                success))
            i = b
        else:
            xy = xy + chord_move(theta, 0, ds[i])
            predicted[i+1], headings[i+1] = xy, theta
            i += 1
    radius = np.divide(-horizontal, delta, out=np.zeros(len(ds)), where=np.abs(delta) > 1e-12)
    radius[~curved] = 0
    errors = np.linalg.norm(predicted - civil[:, 1:3], axis=1)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / 'C:\TEMP\평면선형.txt').open('w', encoding='utf-8') as f:
        for s, r in zip(station[:-1], radius):
            f.write(f'{s:.2f},.curve {r:.12f};0;\n')
        f.write(f'{station[-1]:.2f},.curve 0;0;\n')
    with (output_dir / 'error_check.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Station', 'Civil_X', 'Civil_Y', 'Sim_X', 'Sim_Y', 'Error_m',
                         'CurveBlock', 'Sim_Tangent_rad', 'Radius', 'Pitch'])
        for j, s in enumerate(station):
            writer.writerow([s, *civil[j, 1:3], *predicted[j], errors[j],
                             int(curved[j]) if j < len(ds) else 0, headings[j],
                             radius[j] if j < len(ds) else 0, pitch[j] if j < len(ds) else 0])
    with (output_dir / '곡선구간_진단.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['CurveStart', 'CurveEnd', 'EndpointError_m',
                         'EndpointHeadingError_vs_DMS_deg', 'MaxCurveError_m', 'SolverSuccess'])
        writer.writerows(diagnostics)
    # A separate .Direction file prevents silently forgetting the route header update.
    with (output_dir / '시작방향_설정.txt').open('w', encoding='utf-8') as f:
        f.write('With Route\n')
        f.write(f'.PositionX {civil[0, 1]:.7f}\n')
        f.write(f'.PositionY {civil[0, 2]:.7f}\n')
        f.write(f'.Direction {math.degrees(initial_theta):.14f}\n')
        f.write('\n주의: 실제 노선의 .Direction 값을 교체하세요.\n')
        f.write('PITCH 0 실험 모드는 실제 BVE 노선에서도 PITCH를 0으로 설정해야 비교 가능합니다.\n')
    straight = np.r_[~curved, True]
    summary = {'curve_count': len(runs), 'station_count': len(station),
               'max_error_m': float(errors.max()),
               'max_straight_error_m': float(errors[straight].max()),
               'max_curve_endpoint_error_m': max((d[2] for d in diagnostics), default=0),
               'direction_deg': math.degrees(initial_theta), 'flat': flat}
    return summary


def main():
    root = Tk()
    root.withdraw()
    try:
        civil_path = askopenfilename(title='Civil 3D 보고서 또는 AcadLisp CSV',
                                     filetypes=[('선형 보고서', '*.TXT *.txt *.xls *.xlsx *.csv'), ('모든 파일', '*.*')])
        if not civil_path:
            return
        bve_path = askopenfilename(title='기존 BVE 추출 파일 선택 (측점, Radius, Pitch)',
                                   filetypes=[('BVE 추출 파일', '*.txt *.csv'), ('모든 파일', '*.*')])
        if not bve_path:
            return
        output_dir = askdirectory(title='결과 저장 폴더 선택')
        if not output_dir:
            return
        # Default: reproduce the previously tested, pitch-aware optimization.
        # CLI supports --flat for an explicit no-PITCH experiment.
        flat = messagebox.askyesno('PITCH 선택',
            'PITCH를 제거한 평면선형 실험을 진행할까요?\n\n'
            '예: PITCH=0 기준으로 최적화 (실제 노선도 PITCH=0이어야 함)\n'
            '아니요: 기존 BVE 추출 파일의 PITCH를 적용')
        result = convert(civil_path, bve_path, output_dir, flat=flat)
        msg = ('변환 완료\n\n'
               f"곡선 구간: {result['curve_count']}개\n"
               f"전체 시뮬레이션 최대 오차: {result['max_error_m']:.6f}m\n"
               f"직선 시뮬레이션 최대 오차: {result['max_straight_error_m']:.6f}m\n"
               f"곡선 종료점 최대 오차: {result['max_curve_endpoint_error_m']:.9f}m\n"
               f"시작 .Direction: {result['direction_deg']:.12f}°\n\n"
               '실제 BVE 재추출 좌표로 최종 검증이 필요합니다.')
        print(msg)
        messagebox.showinfo('Civil3D → BVE 변환', msg)
    except Exception as exc:
        print(f'변환 실패: {exc}', file=sys.stderr)
        messagebox.showerror('변환 실패', str(exc))
    finally:
        root.destroy()


if __name__ == '__main__':
    if len(sys.argv) >= 4:
        print(convert(sys.argv[1], sys.argv[2], sys.argv[3], flat='--flat' in sys.argv[4:]))
    else:
        main()
