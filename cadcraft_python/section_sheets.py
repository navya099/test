import math
from datetime import datetime

INK = '#000000'
EG = '#606060'
FG = '#c00000'
GRID = '#c4c4c4'
CUT = '#f3c9a6'
FILL = '#bfe3c4'
MARK = '#8a6200'

SHEET_VEXES = [10, 5, 2, 1]
MARGIN = 36
TITLE_H = 20


def fin(v):
    return isinstance(v, (int, float)) and math.isfinite(v)


def fixed(v, d=2):
    if not fin(v):
        return ""
    return f"{v:.{d}f}"


def format_station(sta, units='ft'):
    if not fin(sta):
        return ""
    return f"{sta:.2f}"


def unit_of(units):
    if units == 'm':
        return {'area': 'sq m'}
    return {'area': 'sq ft'}


def paper_by(paper):
    papers = {
        'letter': {'w': 612, 'h': 792},
        'a4': {'w': 595, 'h': 842},
        'tabloid': {'w': 792, 'h': 1224}
    }
    return papers.get(str(paper).lower(), papers['tabloid'])


def orient(p, landscape):
    w, h = p['w'], p['h']
    if landscape and w < h:
        return {'w': h, 'h': w}
    elif not landscape and w > h:
        return {'w': h, 'h': w}
    return {'w': w, 'h': h}


def z_at(runs, o_val):
    for r in runs:
        if not r:
            continue
        if o_val < r[0]['o'] - 1e-9 or o_val > r[-1]['o'] + 1e-9:
            continue
        for i in range(1, len(r)):
            if o_val <= r[i]['o'] + 1e-9:
                p, q = r[i - 1], r[i]
                w = q['o'] - p['o']
                return p['z'] + ((q['z'] - p['z']) * (o_val - p['o'])) / w if w > 0 else q['z']
    return None


def section_sheets(set_data, paper='tabloid', landscape=True, scale=None, vex=5, units='ft', title='', name='',
                   from_sta=float('-inf'), to_sta=float('inf')):
    all_secs = set_data.get('sections', []) if set_data else []
    secs = [x for x in all_secs if from_sta - 1e-9 <= x.get('sta', 0) <= to_sta + 1e-9]
    notes = []

    if not secs:
        return {'sheets': [], 'cell': None, 'perPage': 0, 'vex': vex, 'notes': ['No sections in range.']}

    P = orient(paper_by(paper), landscape)
    area = {
        'x0': MARGIN + 4,
        'x1': P['w'] - MARGIN - 4,
        'y0': MARGIN + TITLE_H + 4,
        'y1': P['h'] - MARGIN - 4
    }

    # Scale configuration
    s = scale.get('mmPerUnit', 1.0) if scale else 1.0
    left = secs[0].get('left', 10.0)
    right = secs[0].get('right', 10.0)

    def relief(x):
        lo, hi = float('inf'), float('-inf')
        for r in x.get('ground', []) + x.get('design', []):
            for q in r:
                lo = min(lo, q['z'])
                hi = max(hi, q['z'])
        return [lo, hi] if math.isfinite(lo) else None

    rel = [relief(x) for x in secs]
    valid_rel = [r for r in rel if r is not None]
    max_rel = max([1.0] + [hi - lo for lo, hi in valid_rel])

    pad_x, pad_top, pad_bot = 14, 6, 13
    cw = (left + right) * s + pad_x + 4
    if cw > area['x1'] - area['x0']:
        notes.append("Sections are too wide for the page.")

    def fit_v(v):
        return max_rel * 1.2 * s * v + pad_top + pad_bot <= area['y1'] - area['y0']

    want = vex if vex in SHEET_VEXES else 5
    used = 1
    for v in SHEET_VEXES:
        if v <= want and fit_v(v):
            used = v
            break

    if used != want:
        notes.append(f"Vertical exaggeration changed from {want}x to {used}x to fit.")

    sv = s * used
    ch = max_rel * 1.2 * sv + pad_top + pad_bot

    cols = max(1, math.floor((area['x1'] - area['x0']) / cw))
    rows = max(1, math.floor((area['y1'] - area['y0']) / ch))
    per_page = cols * rows
    pages = math.ceil(len(secs) / per_page)

    o_step_raw = 10 / s
    o_step = next((v for v in [1, 2, 5, 10, 20, 25, 50, 100, 200] if v >= o_step_raw), 200)

    z_step_raw = 5 / sv
    z_step = next((v for v in [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50] if v >= z_step_raw), 50)

    h_label = scale.get('label', '') if scale else ''
    v_label = f"1:{round(1000 / sv)}" if units == 'm' else f"1\" = {+(25.4 / sv):.1f}'"
    area_u = unit_of(units)['area']

    sheets = []

    for pg in range(pages):
        strokes, texts, fills = [], [], []
        here = secs[pg * per_page: (pg + 1) * per_page]

        for k, x in enumerate(here):
            col = k % cols
            row = k // cols
            cx0 = area['x0'] + col * cw + pad_x
            cy1 = area['y1'] - row * ch - pad_top
            cy0 = cy1 - (ch - pad_top - pad_bot)

            r = rel[pg * per_page + k] or [0, 1]
            zmid = (r[0] + r[1]) / 2
            z_span = (cy1 - cy0) / sv
            z0 = math.floor((zmid - z_span / 2) / z_step) * z_step

            def X(o):
                return cx0 + (o + left) * s

            def Y(z):
                return cy0 + (z - z0) * sv

            xr = X(right)

            # 격자 (Grid)
            o_curr = math.ceil(-left / o_step) * o_step
            while o_curr <= right + 1e-9:
                strokes.append(
                    {'color': GRID, 'width': 0.08, 'pts': [{'x': X(o_curr), 'y': cy0}, {'x': X(o_curr), 'y': cy1}]})
                texts.append({'color': INK, 'x': X(o_curr), 'y': cy0 - 2.6, 'h': 1.3, 'rot': 0, 'align': 'center',
                              'text': ("+" if o_curr > 0 else "") + fixed(o_curr, 0)})
                o_curr += o_step

            z_curr = z0
            while z_curr <= z0 + z_span + 1e-9:
                y_val = Y(z_curr)
                if y_val > cy1 + 1e-6:
                    break
                strokes.append({'color': GRID, 'width': 0.08, 'pts': [{'x': cx0, 'y': y_val}, {'x': xr, 'y': y_val}]})
                texts.append(
                    {'color': INK, 'x': cx0 - 1, 'y': y_val, 'h': 1.3, 'rot': 0, 'align': 'right', 'middle': True,
                     'text': fixed(z_curr, 1 if z_step < 1 else 0).replace(',', '')})
                z_curr += z_step

            # 셀 외곽선 및 센터라인
            strokes.append({'color': INK, 'width': 0.25,
                            'pts': [{'x': cx0, 'y': cy0}, {'x': xr, 'y': cy0}, {'x': xr, 'y': cy1},
                                    {'x': cx0, 'y': cy1}], 'closed': True})
            strokes.append({'color': FG, 'width': 0.15, 'dash': [3, 1, 0.5, 1],
                            'pts': [{'x': X(0), 'y': cy0}, {'x': X(0), 'y': cy1}]})

            # 절토 및 성토 채우기 (Fills)
            os_set = sorted(list(set([q['o'] for run in x.get('ground', []) + x.get('design', []) for q in run])))
            for part in x.get('parts', []):
                p_o0, p_o1 = part['o0'], part['o1']
                xs = [p_o0] + [o for o in os_set if p_o0 < o < p_o1] + [p_o1]
                top_pts = [{'x': X(o), 'y': Y(z_at(x.get('design', []), o))} for o in xs]
                bot_pts = [{'x': X(o), 'y': Y(z_at(x.get('ground', []), o))} for o in reversed(xs)]
                combined = top_pts + bot_pts
                if all(fin(q['y']) for q in combined):
                    fills.append({'color': CUT if part['kind'] == 'cut' else FILL, 'pts': combined})

            # 지반선 및 설계선 (Strokes)
            for run in x.get('ground', []):
                strokes.append({'color': EG, 'width': 0.25, 'dash': [1.5, 0.8],
                                'pts': [{'x': X(q['o']), 'y': Y(q['z'])} for q in run]})
            if x.get('design') != x.get('ground'):
                for run in x.get('design', []):
                    strokes.append({'color': FG, 'width': 0.4, 'pts': [{'x': X(q['o']), 'y': Y(q['z'])} for q in run]})

            # 코리더 마크
            for m in x.get('marks', []):
                if fin(m.get('z')):
                    qx, qy = X(m['o']), Y(m['z'])
                    strokes.append({'color': MARK, 'width': 0.25,
                                    'pts': [{'x': qx - 0.6, 'y': qy - 0.6}, {'x': qx + 0.6, 'y': qy + 0.6},
                                            {'x': qx - 0.6, 'y': qy + 0.6}, {'x': qx + 0.6, 'y': qy - 0.6}]})

            # 셀 하단 라벨 (Station, Cut, Fill)
            cell_txt = f"Sta {format_station(x.get('sta', 0), units)}   Cut {fixed(x.get('cut', 0), 2)} {area_u}   Fill {fixed(x.get('fill', 0), 2)} {area_u}"
            texts.append({'color': INK, 'x': (cx0 + xr) / 2, 'y': cy0 - 7.5, 'h': 1.8, 'rot': 0, 'align': 'center',
                          'text': cell_txt})

        # 도면 블록 및 테두리 (Title Strip)
        chrome = [
            {'color': INK, 'width': 0.5, 'pts': [{'x': MARGIN, 'y': MARGIN}, {'x': P['w'] - MARGIN, 'y': MARGIN},
                                                 {'x': P['w'] - MARGIN, 'y': P['h'] - MARGIN},
                                                 {'x': MARGIN, 'y': P['h'] - MARGIN}], 'closed': True},
            {'color': INK, 'width': 0.35,
             'pts': [{'x': MARGIN, 'y': MARGIN + TITLE_H}, {'x': P['w'] - MARGIN, 'y': MARGIN + TITLE_H}]}
        ]

        sta_a = format_station(here[0].get('sta', 0), units)
        sta_b = format_station(here[-1].get('sta', 0), units)
        strip_txt = f"{name} Sta {sta_a} to {sta_b}   Horiz {h_label}   Vert {v_label} ({used}x)"

        tt = [
            {'color': INK, 'x': MARGIN + 4, 'y': MARGIN + TITLE_H - 6, 'h': 4, 'rot': 0, 'align': 'left',
             'text': title or name},
            {'color': INK, 'x': MARGIN + 4, 'y': MARGIN + 3.5, 'h': 2.2, 'rot': 0, 'align': 'left', 'text': strip_txt},
            {'color': INK, 'x': P['w'] - MARGIN - 4, 'y': MARGIN + TITLE_H - 6, 'h': 4, 'rot': 0, 'align': 'right',
             'text': f"Sheet {pg + 1} of {pages}"},
            {'color': INK, 'x': P['w'] - MARGIN - 4, 'y': MARGIN + 3.5, 'h': 2.2, 'rot': 0, 'align': 'right',
             'text': f"Date: {datetime.now().strftime('%Y-%m-%d')}"}
        ]

        sheets.append({
            'w': P['w'], 'h': P['h'],
            'name': f"{title or name} {pg + 1}",
            'views': [{'clip': {'x0': MARGIN, 'y0': MARGIN + TITLE_H, 'x1': P['w'] - MARGIN, 'y1': P['h'] - MARGIN},
                       'strokes': strokes, 'texts': texts, 'fills': fills}],
            'chrome': chrome, 'chromeTexts': tt,
            'stations': [x.get('sta', 0) for x in here]
        })

    return {
        'sheets': sheets,
        'cell': {'w': cw, 'h': ch, 'cols': cols, 'rows': rows},
        'perPage': per_page,
        'vex': used,
        'notes': notes
    }