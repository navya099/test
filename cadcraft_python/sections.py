import math

MAX_SECTIONS = 2000


def SAMPLE_DEFAULTS(units='ft'):
    return {'step': 20, 'left': 30, 'right': 30} if units == 'm' else {'step': 50, 'left': 100, 'right': 100}


def clean_sampling(o, units='ft'):
    if not o or not isinstance(o, dict):
        return None
    d = SAMPLE_DEFAULTS(units)

    def pos(v, k, mx):
        return v if (isinstance(v, (int, float)) and math.isfinite(v) and 0 < v <= mx) else d[k]

    raw_extra = o.get('extra', [])
    extra = sorted(
        list(set([v for v in raw_extra if isinstance(v, (int, float)) and math.isfinite(v) and abs(v) < 1e8])))[:500]

    return {
        'step': pos(o.get('step'), 'step', 1e5),
        'left': pos(o.get('left'), 'left', 1e4),
        'right': pos(o.get('right'), 'right', 1e4),
        'extra': extra
    }


def sample_stations(al, step=None, extra=None, from_sta=None, to_sta=None):
    if not getattr(al, 'ok', True):
        return []
    al_start = getattr(al, 'start', 0.0)
    al_end = getattr(al, 'end', 0.0)
    lo = max(al_start, from_sta if (from_sta is not None and math.isfinite(from_sta)) else al_start)
    hi = min(al_end, to_sta if (to_sta is not None and math.isfinite(to_sta)) else al_end)
    if hi < lo:
        return []

    st = {lo, hi}
    s_val = step if step is not None else 50
    if s_val > 0:
        k = math.ceil(lo / s_val - 1e-9)
        while k * s_val < hi - 1e-9 and len(st) < MAX_SECTIONS:
            st.add(round(k * s_val, 6))
            k += 1

    key_stations = al.key_stations() if hasattr(al, 'key_stations') else (
        al.keyStations() if hasattr(al, 'keyStations') else [])
    for k in key_stations:
        sta = k.get('sta') if isinstance(k, dict) else getattr(k, 'sta', 0)
        if lo < sta < hi:
            st.add(sta)

    for s in (extra or []):
        if lo <= s <= hi:
            st.add(s)

    sorted_sts = sorted(list(st))
    out = []
    for i, s in enumerate(sorted_sts):
        if i == 0 or s - sorted_sts[i - 1] > 1e-6:
            out.append(s)
    return out[:MAX_SECTIONS]


def sample_line(al, sta, left, right):
    p = al.point_at(sta) if hasattr(al, 'point_at') else al.pointAt(sta)
    rx = math.sin(p['dir'])
    ry = -math.cos(p['dir'])
    return {
        'sta': sta,
        'c': {'x': p['x'], 'y': p['y']},
        'a': {'x': p['x'] - rx * left, 'y': p['y'] - ry * left},
        'b': {'x': p['x'] + rx * right, 'y': p['y'] + ry * right},
        'dir': p['dir'],
        'left': left,
        'right': right
    }


def seg_cross(px, py, rx, ry, qx, qy, sx, sy):
    den = rx * sy - ry * sx
    if abs(den) < 1e-15:
        return None
    t0 = ((qx - px) * sy - (qy - py) * sx) / den
    u = ((qx - px) * ry - (qy - py) * rx) / den
    if -1e-12 <= t0 <= 1 + 1e-12 and -1e-12 <= u <= 1 + 1e-12:
        return max(0.0, min(1.0, t0))
    return None


def seg_hits_box(ax, ay, bx, by, x0, y0, x1, y1):
    t0, t1 = 0.0, 1.0
    dx, dy = bx - ax, by - ay
    edges = [[-dx, ax - x0], [dx, x1 - ax], [-dy, ay - y0], [dy, y1 - ay]]
    for p, q in edges:
        if p == 0:
            if q < 0: return False
            continue
        r = q / p
        if p < 0:
            if r > t1: return False
            if r > t0: t0 = r
        else:
            if r < t0: return False
            if r < t1: t1 = r
    return True


def surface_section(surface, a, b, off_a, off_b):
    if not surface:
        return []
    X, Y, tris = surface.X, surface.Y, surface.tris
    ox, oy = surface.ox, surface.oy
    ax, ay = a['x'] - ox, a['y'] - oy
    bx, by = b['x'] - ox, b['y'] - oy
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy)
    if L <= 0:
        return []

    ts = [0.0, 1.0]
    g = surface.grid()
    clamp_i = lambda v, n: max(0, min(n - 1, math.floor(v)))
    x0, x1 = min(ax, bx), max(ax, bx)
    y0, y1 = min(ay, by), max(ay, by)

    gb = g['b']
    if not (x1 < gb['minX'] or x0 > gb['maxX'] or y1 < gb['minY'] or y0 > gb['maxY']):
        i0 = clamp_i((x0 - gb['minX']) / g['cw'], g['nx'])
        i1 = clamp_i((x1 - gb['minX']) / g['cw'], g['nx'])
        j0 = clamp_i((y0 - gb['minY']) / g['ch'], g['ny'])
        j1 = clamp_i((y1 - gb['minY']) / g['ch'], g['ny'])
        seen = set()
        for j in range(j0, j1 + 1):
            for i in range(i0, i1 + 1):
                cx0 = gb['minX'] + i * g['cw']
                cy0 = gb['minY'] + j * g['ch']
                if not seg_hits_box(ax, ay, bx, by, cx0, cy0, cx0 + g['cw'], cy0 + g['ch']):
                    continue
                k = j * g['nx'] + i
                for s_idx in range(g['start'][k], g['start'][k + 1]):
                    tri = g['items'][s_idx]
                    if tri in seen: continue
                    seen.add(tri)
                    for e in range(3):
                        p = tris[3 * tri + e]
                        q = tris[3 * tri + ((e + 1) % 3)]
                        tt = seg_cross(ax, ay, dx, dy, X[p], Y[p], X[q] - X[p], Y[q] - Y[p])
                        if tt is not None:
                            ts.append(tt)

    ts.sort()
    runs = []
    run = None
    last = -1.0
    for tt in ts:
        if tt - last < 1e-12: continue
        last = tt
        z = surface.elevation_at(a['x'] + (b['x'] - a['x']) * tt, a['y'] + (b['y'] - a['y']) * tt, 1e-7)
        o = off_a + (off_b - off_a) * tt
        if z is None:
            run = None
            continue
        if not run:
            run = []
            runs.append(run)
        run.append({'o': o, 'z': z})

    return [r for r in runs if len(r) >= 2]


def z_at(runs, o):
    for r in runs:
        if o < r[0]['o'] - 1e-9 or o > r[-1]['o'] + 1e-9:
            continue
        for i in range(1, len(r)):
            if o <= r[i]['o'] + 1e-9:
                p, q = r[i - 1], r[i]
                d = q['o'] - p['o']
                return p['z'] + ((q['z'] - p['z']) * (o - p['o'])) / d if d > 0 else q['z']
    return None


def cut_fill(ground, design):
    os = set()
    for r in list(ground) + list(design):
        for p in r:
            os.add(p['o'])
    xs = sorted(list(os))
    cut = 0.0
    fill = 0.0
    parts = []

    def push(o0, o1, kind, area):
        nonlocal cut, fill
        if area <= 0 or o1 - o0 <= 0:
            return
        if parts and parts[-1]['kind'] == kind and abs(parts[-1]['o1'] - o0) < 1e-9:
            parts[-1]['o1'] = o1
        else:
            parts.append({'o0': o0, 'o1': o1, 'kind': kind})
        if kind == 'cut':
            cut += area
        else:
            fill += area

    for i in range(1, len(xs)):
        o0, o1 = xs[i - 1], xs[i]
        om = (o0 + o1) / 2.0
        if z_at(ground, om) is None or z_at(design, om) is None:
            continue
        g0, g1 = z_at(ground, o0), z_at(ground, o1)
        d0, d1 = z_at(design, o0), z_at(design, o1)
        if any(v is None for v in [g0, g1, d0, d1]):
            continue
        e0, e1 = d0 - g0, d1 - g1
        w = o1 - o0
        if e0 >= 0 and e1 >= 0:
            push(o0, o1, 'fill', ((e0 + e1) / 2.0) * w)
        elif e0 <= 0 and e1 <= 0:
            push(o0, o1, 'cut', ((-e0 - e1) / 2.0) * w)
        else:
            om2 = o0 + (w * e0) / (e0 - e1)
            a0 = (abs(e0) / 2.0) * (om2 - o0)
            a1 = (abs(e1) / 2.0) * (o1 - om2)
            push(o0, om2, 'fill' if e0 > 0 else 'cut', a0)
            push(om2, o1, 'fill' if e1 > 0 else 'cut', a1)

    return {'cut': cut, 'fill': fill, 'parts': parts}


def feature_marks(lines, line):
    out = []
    a, b, left, right = line['a'], line['b'], line['left'], line['right']
    dx, dy = b['x'] - a['x'], b['y'] - a['y']
    for code, pts in (lines or {}).items():
        if not isinstance(pts, list): continue
        for i in range(1, len(pts)):
            p, q = pts[i - 1], pts[i]
            tt = seg_cross(a['x'], a['y'], dx, dy, p['x'], p['y'], q['x'] - p['x'], q['y'] - p['y'])
            if tt is None: continue
            u = seg_cross(p['x'], p['y'], q['x'] - p['x'], q['y'] - p['y'], a['x'], a['y'], dx, dy)
            z = (p['z'] + (q['z'] - p['z']) * u) if (math.isfinite(p.get('z', float('nan'))) and math.isfinite(
                q.get('z', float('nan'))) and u is not None) else None
            out.append({'code': code, 'o': -left + (left + right) * tt, 'z': z})
            break
    out.sort(key=lambda m: m['o'])
    return out


def region_spans(line, regions):
    a, b, left, right = line['a'], line['b'], line['left'], line['right']
    dx, dy = b['x'] - a['x'], b['y'] - a['y']
    ts = {0.0, 1.0}
    for r in (regions or []):
        for i in range(len(r)):
            p, q = r[i], r[(i + 1) % len(r)]
            tt = seg_cross(a['x'], a['y'], dx, dy, p['x'], p['y'], q['x'] - p['x'], q['y'] - p['y'])
            if tt is not None:
                ts.add(tt)
    xs = sorted(list(ts))
    out = []

    def on_edge(x, y, r):
        for i in range(len(r)):
            p, q = r[i], r[(i + 1) % len(r)]
            ex, ey = q['x'] - p['x'], q['y'] - p['y']
            L = ex * ex + ey * ey
            u = max(0.0, min(1.0, ((x - p['x']) * ex + (y - p['y']) * ey) / L)) if L else 0.0
            if math.hypot(x - p['x'] - u * ex, y - p['y'] - u * ey) <= 1e-6 * max(1.0, math.sqrt(L)):
                return True
        return False

    def inside(x, y):
        for r in (regions or []):
            c = False
            j = len(r) - 1
            for i in range(len(r)):
                if (r[i]['y'] > y) != (r[j]['y'] > y) and x < (
                        (r[j]['x'] - r[i]['x']) * (y - r[i]['y']) / (r[j]['y'] - r[i]['y'] + 1e-12) + r[i]['x']):
                    c = not c
                j = i
            if c or on_edge(x, y, r):
                return True
        return False

    for i in range(1, len(xs)):
        tm = (xs[i - 1] + xs[i]) / 2.0
        if xs[i] - xs[i - 1] < 1e-12 or not inside(a['x'] + dx * tm, a['y'] + dy * tm):
            continue
        o0 = -left + (left + right) * xs[i - 1]
        o1 = -left + (left + right) * xs[i]
        if out and abs(out[-1][1] - o0) < 1e-9:
            out[-1][1] = o1
        else:
            out.append([o0, o1])
    return out


def clip_runs(runs, spans):
    out = []
    for o0, o1 in spans:
        for r in runs:
            if r[-1]['o'] <= o0 or r[0]['o'] >= o1:
                continue
            z0 = z_at([r], max(o0, r[0]['o']))
            z1 = z_at([r], min(o1, r[-1]['o']))
            pts = [{'o': max(o0, r[0]['o']), 'z': z0}]
            for q in r:
                if q['o'] > o0 + 1e-12 and q['o'] < o1 - 1e-12:
                    pts.append(q)
            pts.append({'o': min(o1, r[-1]['o']), 'z': z1})
            if len(pts) >= 2 and pts[-1]['o'] - pts[0]['o'] > 1e-12:
                out.append(pts)
    return out


def build_sections(alignment, ground, design, regions=None, corridor=None, sampling=None, from_sta=None, to_sta=None):
    smp = sampling or SAMPLE_DEFAULTS()
    stations = sample_stations(alignment, step=smp.get('step'), extra=smp.get('extra'), from_sta=from_sta,
                               to_sta=to_sta)
    sections = []
    for sta in stations:
        line = sample_line(alignment, sta, smp.get('left'), smp.get('right'))
        g = surface_section(ground, line['a'], line['b'], -smp.get('left'), smp.get('right'))
        d = surface_section(design, line['a'], line['b'], -smp.get('left'), smp.get('right')) if (
                    design and design != ground) else g
        if d != g and regions:
            d = clip_runs(d, region_spans(line, regions))
        cf = cut_fill(g, d)
        sections.append({
            'sta': sta, 'a': line['a'], 'b': line['b'], 'c': line['c'],
            'left': smp.get('left'), 'right': smp.get('right'),
            'ground': g, 'design': d, 'cut': cf['cut'], 'fill': cf['fill'],
            'parts': cf['parts'], 'marks': feature_marks(corridor, line) if corridor else []
        })

    rows = []
    cum_cut, cum_fill = 0.0, 0.0
    for i, s in enumerate(sections):
        cut_vol, fill_vol = 0.0, 0.0
        if i > 0:
            p = sections[i - 1]
            L = s['sta'] - p['sta']
            cut_vol = ((p['cut'] + s['cut']) / 2.0) * L
            fill_vol = ((p['fill'] + s['fill']) / 2.0) * L
        cum_cut += cut_vol
        cum_fill += fill_vol
        rows.append({'sta': s['sta'], 'cut': s['cut'], 'fill': s['fill'], 'cutVol': cut_vol, 'fillVol': fill_vol,
                     'cumCut': cum_cut, 'cumFill': cum_fill})

    return {'sections': sections, 'rows': rows, 'totals': {'cut': cum_cut, 'fill': cum_fill}}


def sections_csv(set_data, units='ft', station_fn=str):
    ft = (units != 'm')
    vol_per = 27.0 if ft else 1.0
    head = [
        "Station", "Cut Area (sq ft)", "Fill Area (sq ft)", "Cut Vol (cu yd)", "Fill Vol (cu yd)", "Cum Cut", "Cum Fill"
    ] if ft else [
        "Station", "Cut Area (sq m)", "Fill Area (sq m)", "Cut Vol (cu m)", "Fill Vol (cu m)", "Cum Cut", "Cum Fill"
    ]

    def csv_cell(v):
        s = str(v)
        if '"' in s or ',' in s or '\r' in s or '\n' in s:
            return '"' + s.replace('"', '""') + '"'
        return s

    lines = [','.join(csv_cell(h) for h in head)]
    for r in set_data.get('rows', []):
        row_vals = [
            station_fn(r['sta']),
            f"{r['cut']:.2f}", f"{r['fill']:.2f}",
            f"{r['cutVol'] / vol_per:.1f}", f"{r['fillVol'] / vol_per:.1f}",
            f"{r['cumCut'] / vol_per:.1f}", f"{r['cumFill'] / vol_per:.1f}"
        ]
        lines.append(','.join(csv_cell(v) for v in row_vals))
    return '\r\n'.join(lines) + '\r\n'