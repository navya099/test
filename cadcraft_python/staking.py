import math
from datetime import datetime
import re

EPS = 1e-9


def fin(v):
    return isinstance(v, (int, float)) and math.isfinite(v)


# --- 헬퍼 및 모의 구현 (i18n, units, plot 대체) ---
def format_station(sta, units='ft'):
    if not fin(sta):
        return ""
    return f"{sta:.2f}"


def fixed(v, d=2):
    if not fin(v):
        return ""
    return f"{v:.{d}f}"


def t(key, params=None):
    translations = {
        'sk.c.point': 'Point', 'sk.c.sta': 'Station', 'sk.c.off': 'Offset ({u})',
        'sk.c.n': 'Northing', 'sk.c.e': 'Easting', 'sk.c.design': 'Design',
        'sk.c.ground': 'Ground', 'sk.c.cf': 'C/F ({u})', 'sk.c.cfn': 'C/F Val',
        'sk.strip': 'Alignment staking report ({n} points, {u})',
        'pp.sheet': 'Sheet {n} of {N}', 'pp.made': 'Date: {date}'
    }
    text = translations.get(key, key)
    if params:
        for k, val in params.items():
            text = text.replace(f"{{{k}}}", str(val))
    return text


MARGIN = 36
TITLE_H = 20


def paper_by(paper):
    papers = {'letter': {'w': 612, 'h': 792}, 'a4': {'w': 595, 'h': 842}}
    return papers.get(paper.lower(), papers['letter'])


def orient(p, landscape):
    if landscape and p['w'] < p['h']:
        return {'w': p['h'], 'h': p['w']}
    elif not landscape and p['w'] > p['h']:
        return {'w': p['h'], 'h': p['w']}
    return p


# --- 핵심 기능 구현 ---

def stake_stations(al, from_val=None, to_val=None, step=50, keys=True):
    al_start = getattr(al, 'start', 0)
    al_end = getattr(al, 'end', 0)
    f_val = al_start if from_val is None else from_val
    t_val = al_end if to_val is None else to_val

    a = max(al_start, min(f_val, t_val))
    b = min(al_end, max(f_val, t_val))

    st_set = {a, b}
    if step > 0:
        k = math.ceil((a - EPS) / step)
        while k * step <= b + EPS:
            st_set.add(min(b, max(a, k * step)))
            k += 1

    if keys:
        elements = getattr(al, 'elements', [])
        for e in elements:
            e_sta = e.get('sta', 0) if isinstance(e, dict) else getattr(e, 'sta', 0)
            e_len = e.get('len', 0) if isinstance(e, dict) else getattr(e, 'len', 0)
            for s in [e_sta, e_sta + e_len]:
                if s > a + EPS and s < b - EPS:
                    st_set.add(s)

    sorted_sts = sorted(list(st_set))
    filtered = []
    for i, s in enumerate(sorted_sts):
        if i == 0 or s - sorted_sts[i - 1] > 1e-6:
            filtered.append(s)
    return filtered


def place(al, sta, off):
    # al.point_at 또는 al.pointAt 지원
    p = al.point_at(sta) if hasattr(al, 'point_at') else al.pointAt(sta)
    # 우측이 양수 (+) : 전진 방향의 우측 법선 벡터
    return {
        'x': p['x'] + off * math.sin(p['dir']),
        'y': p['y'] - off * math.cos(p['dir'])
    }


def stake_rows(al, stations, offsets=None, design=lambda *_: None, ground=lambda *_: None, first=1, prefix=''):
    if offsets is None:
        offsets = [0]
    rows = []
    n = first
    for sta in stations:
        for off in offsets:
            pt = place(al, sta, off)
            x, y = pt['x'], pt['y']
            d = design(sta, off, x, y)
            g = ground(x, y)
            rows.append({
                'id': f"{prefix}{n}",
                'sta': sta,
                'off': off,
                'x': x,
                'y': y,
                'design': d if fin(d) else None,
                'ground': g if fin(g) else None,
                'cf': (g - d) if (fin(d) and fin(g)) else None
            })
            n += 1
    return rows


def point_rows(al, points, design=lambda *_: None, ground=None):
    rows = []
    outside = 0
    for p in points:
        so = al.station_offset(p['x'], p['y']) if hasattr(al, 'station_offset') else al.stationOffset(p['x'], p['y'])
        if not so or so.get('outside'):
            outside += 1
            continue
        d = design(so['sta'], so['off'], p['x'], p['y'])
        g = p['z'] if fin(p.get('z')) else (ground(p['x'], p['y']) if ground else None)
        rows.append({
            'id': p.get('n'),
            'sta': so['sta'],
            'off': so['off'],
            'x': p['x'],
            'y': p['y'],
            'design': d if fin(d) else None,
            'ground': g if fin(g) else None,
            'cf': (g - d) if (fin(d) and fin(g)) else None
        })
    rows.sort(key=lambda r: (r['sta'], r['off']))
    return {'rows': rows, 'outside': outside}


def parse_offsets(text):
    out = []
    src = str(text or '').upper()
    src = re.sub(r'\bCL\b', '0', src)
    src = re.sub(r'(^|[\s,;])([LR])\s+(\d)', r'\1\2\3', src)
    src = re.sub(r'(\d)\s+([LR])\b', r'\1\2', src)

    for tok in [t.strip() for t in re.split(r'[\s,;]+', src) if t.strip()]:
        m = re.match(r'^([LR])?(-?\d+(?:\.\d+)?)([LR])?$', tok)
        if not m or (m.group(1) and m.group(3)):
            return {'error': tok}
        v = float(m.group(2))
        side = m.group(1) or m.group(3)
        if side:
            if v < 0:
                return {'error': tok}
            v = -v if side == 'L' else v
        if abs(v) > 1e5:
            return {'error': tok}
        if not any(abs(o - v) < 1e-9 for o in out):
            out.append(v)
    if len(out) > 200:
        return {'error': '…'}
    return out


def cut_fill_text(cf):
    if not fin(cf):
        return ''
    if abs(cf) < 0.005:
        return '0.00'
    return ('C ' if cf > 0 else 'F ') + fixed(abs(cf), 2).replace(',', '')


def offset_text(off):
    if abs(off) < 0.005:
        return '0.00'
    return fixed(abs(off), 2).replace(',', '') + (' L' if off < 0 else ' R')


def num(v, d):
    return f"{v:.{d}f}" if fin(v) else ''


def staking_csv(rows, units='ft', title=''):
    u = 'm' if units == 'm' else 'ft'

    def q(val):
        s = str(val)
        if re.match(r'^-?\d', s) or s == '':
            return s
        if re.match(r'^[=+\-@\t\r]', s):
            return "'" + s
        return s

    def c(val):
        if not re.search(r'[",\r\n]', val):
            return val
        escaped = val.replace('"', '""')
        return f'"{escaped}"'

    out = []
    if title:
        out.append([title])
    out.append([t('sk.c.point'), t('sk.c.sta'), t('sk.c.off', {'u': u}), t('sk.c.n'), t('sk.c.e'), t('sk.c.design'),
                t('sk.c.ground'), t('sk.c.cf', {'u': u}), t('sk.c.cfn')])

    for r in rows:
        out.append([
            r['id'], format_station(r['sta'], units), offset_text(r['off']),
            num(r['y'], 3), num(r['x'], 3), num(r['design'], 3),
            num(r['ground'], 3), cut_fill_text(r['cf']), num(r['cf'], 3)
        ])
    return '\r\n'.join(','.join(c(q(v)) for v in row) for row in out) + '\r\n'


def staking_sheets(rows, paper='letter', landscape=True, units='ft', title='', name=''):
    P = orient(paper_by(paper), landscape)
    x0 = MARGIN + 4
    x1 = P['w'] - MARGIN - 4
    top = P['h'] - MARGIN - 6
    bottom = MARGIN + TITLE_H + 4
    rowH = 5
    perPage = max(1, math.floor((top - bottom - rowH * 1.6) / rowH))
    u = 'm' if units == 'm' else 'ft'

    cols = [
        {'k': 'id', 'w': 0.11, 'h': t('sk.c.point'), 'a': 'left'},
        {'k': 'sta', 'w': 0.12, 'h': t('sk.c.sta'), 'a': 'right'},
        {'k': 'off', 'w': 0.11, 'h': t('sk.c.off', {'u': u}), 'a': 'right'},
        {'k': 'n', 'w': 0.15, 'h': t('sk.c.n'), 'a': 'right'},
        {'k': 'e', 'w': 0.15, 'h': t('sk.c.e'), 'a': 'right'},
        {'k': 'design', 'w': 0.12, 'h': t('sk.c.design'), 'a': 'right'},
        {'k': 'ground', 'w': 0.12, 'h': t('sk.c.ground'), 'a': 'right'},
        {'k': 'cf', 'w': 0.12, 'h': t('sk.c.cf', {'u': u}), 'a': 'right'}
    ]

    W = x1 - x0
    cx = x0
    for col in cols:
        col['x0'] = cx
        cx += col['w'] * W
        col['x1'] = cx

    def cell(r, k):
        mapping = {
            'id': str(r['id']), 'sta': format_station(r['sta'], units),
            'off': offset_text(r['off']), 'n': num(r['y'], 3),
            'e': num(r['x'], 3), 'design': num(r['design'], 2),
            'ground': num(r['ground'], 2), 'cf': cut_fill_text(r['cf'])
        }
        return mapping.get(k, '')

    pages = max(1, math.ceil(len(rows) / perPage))
    sheets = []

    INK, RULE, CUT, FILL = '#000000', '#9a9a9a', '#a84a00', '#17703a'

    for pg in range(pages):
        here = rows[pg * perPage: (pg + 1) * perPage]
        strokes, texts = [], []
        y = top
        for col in cols:
            texts.append(
                {'color': INK, 'x': col['x0'] + 1 if col['a'] == 'left' else col['x1'] - 1, 'y': y - 3.4, 'h': 2.2,
                 'rot': 0, 'align': col['a'], 'text': col['h']})
        y -= rowH * 1.2
        strokes.append({'color': INK, 'width': 0.35, 'pts': [{'x': x0, 'y': y}, {'x': x1, 'y': y}]})

        for i, r in enumerate(here):
            yb = y - rowH
            for col in cols:
                s = cell(r, col['k'])
                if not s:
                    continue
                color = INK
                if col['k'] == 'cf' and fin(r['cf']) and abs(r['cf']) >= 0.005:
                    color = CUT if r['cf'] > 0 else FILL
                texts.append(
                    {'color': color, 'x': col['x0'] + 1 if col['a'] == 'left' else col['x1'] - 1, 'y': yb + 1.5,
                     'h': 2.1, 'rot': 0, 'align': col['a'], 'text': s})
            if (i + 1) % 5 == 0 and i < len(here) - 1:
                strokes.append({'color': RULE, 'width': 0.1, 'pts': [{'x': x0, 'y': yb}, {'x': x1, 'y': yb}]})
            y = yb

        chrome = [
            {'color': INK, 'width': 0.5, 'pts': [{'x': MARGIN, 'y': MARGIN}, {'x': P['w'] - MARGIN, 'y': MARGIN},
                                                 {'x': P['w'] - MARGIN, 'y': P['h'] - MARGIN},
                                                 {'x': MARGIN, 'y': P['h'] - MARGIN}], 'closed': True},
            {'color': INK, 'width': 0.35,
             'pts': [{'x': MARGIN, 'y': MARGIN + TITLE_H}, {'x': P['w'] - MARGIN, 'y': MARGIN + TITLE_H}]}
        ]
        tt = [
            {'color': INK, 'x': MARGIN + 4, 'y': MARGIN + TITLE_H - 6, 'h': 4, 'rot': 0, 'align': 'left',
             'text': title or name},
            {'color': INK, 'x': MARGIN + 4, 'y': MARGIN + 3.5, 'h': 2.2, 'rot': 0, 'align': 'left',
             'text': t('sk.strip', {'name': name, 'n': len(rows), 'u': u})},
            {'color': INK, 'x': P['w'] - MARGIN - 4, 'y': MARGIN + TITLE_H - 6, 'h': 4, 'rot': 0, 'align': 'right',
             'text': t('pp.sheet', {'n': pg + 1, 'N': pages})},
            {'color': INK, 'x': P['w'] - MARGIN - 4, 'y': MARGIN + 3.5, 'h': 2.2, 'rot': 0, 'align': 'right',
             'text': t('pp.made', {'date': datetime.now().strftime('%Y-%m-%d')})}
        ]
        sheets.append({
            'w': P['w'], 'h': P['h'], 'name': (title or name) + ' ' + str(pg + 1),
            'views': [{'clip': {'x0': MARGIN, 'y0': MARGIN + TITLE_H, 'x1': P['w'] - MARGIN, 'y1': P['h'] - MARGIN},
                       'strokes': strokes, 'texts': texts, 'fills': []}],
            'chrome': chrome, 'chromeTexts': tt
        })
    return {'sheets': sheets, 'perPage': perPage}