import math


def ang(a, b, c):
    a1 = math.atan2(b['y'] - a['y'], b['x'] - a['x'])
    a2 = math.atan2(c['y'] - b['y'], c['x'] - b['x'])
    d = a2 - a1
    while d > math.pi:
        d -= 2 * math.pi
    while d < -math.pi:
        d += 2 * math.pi
    return d


def down(v):
    return math.floor(v * 100 + 1e-9) / 100


def up(v):
    return math.ceil(v * 100 - 1e-9) / 100


def dist(p, q):
    return math.hypot(q['x'] - p['x'], q['y'] - p['y'])


def curves_of(pis):
    res = []
    for i, p in enumerate(pis):
        if i == 0 or i == len(pis) - 1:
            res.append({'d': 0, 'r': 0, 'T': 0, 'tanHalf': 0, 'back': False})
        else:
            d = ang(pis[i - 1], p, pis[i + 1])
            r = float(p.get('r', 0)) if p.get('r') is not None and float(p.get('r', 0)) > 0 else 0.0
            tan_half = math.tan(abs(d) / 2)
            back = abs(abs(d) - math.pi) < 1e-6
            T = 0 if back or abs(d) < 1e-9 else r * tan_half
            res.append({'d': d, 'r': r, 'T': T, 'tanHalf': tan_half, 'back': back})
    return res


def max_radius(pis, i):
    C = curves_of(pis)
    if i < 0 or i >= len(C):
        return 0
    c = C[i]
    if i == 0 or i == len(pis) - 1 or c['back']:
        return 0
    if abs(c['d']) < 1e-9:
        return float('inf')
    room = min(dist(pis[i - 1], pis[i]) - C[i - 1]['T'], dist(pis[i], pis[i + 1]) - C[i + 1]['T'])
    return 0 if room <= 0 else room / c['tanHalf']


def curve_why(pis, min_r=0):
    P = [p for p in (pis or []) if isinstance(p.get('x'), (int, float)) and isinstance(p.get('y'), (int, float))]
    if len(P) < 3:
        return []
    C = curves_of(P)
    out = []
    for i, c in enumerate(C):
        if c['back'] and c['r'] > 0:
            out.append({'kind': 'back', 'pi': i})

    for a in range(len(P) - 1):
        b = a + 1
        L = dist(P[a], P[b])
        Ta = C[a]['T']
        Tb = C[b]['T']
        if Ta + Tb <= L + 1e-9:
            continue

        def inner(i):
            return i > 0 and i < len(P) - 1 and not C[i]['back'] and abs(C[i]['d']) > 1e-9

        def fix(i, other):
            if not inner(i):
                return None
            here = L - other
            far = dist(P[a - 1], P[a]) - C[a - 1]['T'] if i == a else dist(P[b], P[b + 1]) - C[b + 1]['T']
            room = min(here, far)
            return down(room / C[i]['tanHalf']) if room > 0 else None

        f = L / (Ta + Tb) if (Ta + Tb) > 0 else 1.0
        out.append({
            'kind': 'overlap',
            'a': a,
            'b': b,
            'dist': L,
            'need': Ta + Tb,
            'Ta': Ta,
            'Tb': Tb,
            'fixA': fix(a, Tb),
            'fixB': fix(b, Ta),
            'both': {
                'ra': down(C[a]['r'] * f) if inner(a) else 0,
                'rb': down(C[b]['r'] * f) if inner(b) else 0
            }
        })

    if min_r > 0:
        for i, c in enumerate(C):
            if i == 0 or i == len(P) - 1 or not (c['r'] > 0) or c['r'] >= min_r - 1e-9 or c['back']:
                continue
            max_r = max_radius(P, i)
            out.append({
                'kind': 'min',
                'pi': i,
                'r': c['r'],
                'minR': min_r,
                'maxR': max_r,
                'fix': up(min_r) if min_r <= max_r + 1e-9 else None
            })
    return out


def vertical_why(pvis_in):
    pvis = []
    for i, p in enumerate(pvis_in or []):
        if isinstance(p.get('sta'), (int, float)) and isinstance(p.get('z'), (int, float)):
            pvis.append({**p, 'i0': i})
    pvis.sort(key=lambda x: x['sta'])

    out = []
    prev_end = pvis[0]['sta'] if pvis else 0
    for i in range(1, len(pvis) - 1):
        v = pvis[i]
        g1 = (v['z'] - pvis[i - 1]['z']) / (v['sta'] - pvis[i - 1]['sta'])
        g2 = (pvis[i + 1]['z'] - v['z']) / (pvis[i + 1]['sta'] - v['sta'])
        A = (g2 - g1) * 100
        L = float(v.get('L', 0) or 0)
        if not L and float(v.get('K', 0) or 0) > 0:
            L = float(v.get('K', 0)) * abs(A)
        if not (L > 0) or abs(A) < 1e-9:
            continue
        back = v['sta'] - max(pvis[i - 1]['sta'], prev_end)
        fwd = pvis[i + 1]['sta'] - v['sta']
        room = 2 * min(back, fwd)
        if L > room + 1e-9:
            fix_val = down(room) if room > 0 else None
            out.append({
                'kind': 'vc',
                'pvi': i,
                'index': v['i0'],
                'L': L,
                'room': room,
                'fix': fix_val,
                'K': (fix_val / abs(A)) if fix_val is not None else None,
                'side': 'before' if back < fwd else 'past'
            })
            prev_end = v['sta'] + (fix_val if fix_val is not None else 0) / 2
        else:
            prev_end = v['sta'] + L / 2
    return out