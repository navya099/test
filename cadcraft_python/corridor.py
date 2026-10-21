import math

def default_assembly(units='ft'):
    if units == 'm':
        return {'lane': 3.6, 'laneSlope': 0.02, 'shoulder': 1.2, 'shoulderSlope': 0.04, 'cut': 2, 'fill': 3, 'step': 5}
    else:
        return {'lane': 12, 'laneSlope': 0.02, 'shoulder': 4, 'shoulderSlope': 0.04, 'cut': 2, 'fill': 3, 'step': 10}

TARGET_SIDES = ['L', 'R']
TARGET_WHAT = ['width', 'elev']
TARGET_PARTS = ['eop', 'sh']
CORRIDOR_LINES = ['CL', 'EOP_L', 'SH_L', 'DL_L', 'EOP_R', 'SH_R', 'DL_R']
MAX_TARGETS = 8

def clean_targets(lst):
    if not isinstance(lst, list):
        return []
    out = []
    seen = set()
    for g in lst[:64]:
        if not g or not isinstance(g, dict):
            continue
        side = g.get('side')
        what = g.get('what')
        part = g.get('part')
        if side not in TARGET_SIDES or what not in TARGET_WHAT or part not in TARGET_PARTS:
            continue
        f = g.get('from', {})
        id_str = str(f.get('id', ''))
        from_obj = None
        if f.get('kind') == 'feature' and id_str.startswith('f') and len(id_str) <= 10:
            from_obj = {'kind': 'feature', 'id': id_str}
        elif f.get('kind') == 'corridor' and id_str.startswith('a') and f.get('line') in CORRIDOR_LINES:
            from_obj = {'kind': 'corridor', 'id': id_str, 'line': f.get('line')}
        if not from_obj:
            continue
        key = side + what + part
        if key in seen:
            continue
        seen.add(key)
        out.append({'side': side, 'what': what, 'part': part, 'from': from_obj})
        if len(out) >= MAX_TARGETS:
            break
    return out

def section_hit(p, ux, uy, line):
    best = None
    for i in range(1, len(line or [])):
        a = line[i - 1]
        b = line[i]
        dx = b['x'] - a['x']
        dy = b['y'] - a['y']
        den = ux * dy - uy * dx
        if abs(den) < 1e-15:
            continue
        wx = a['x'] - p['x']
        wy = a['y'] - p['y']
        t = (wx * dy - wy * dx) / den
        u = (wx * uy - wy * ux) / den
        if t <= 1e-9 or u < -1e-12 or u > 1 + 1e-12:
            continue
        if not best or t < best['t']:
            best = {'t': t, 'z': a['z'] + min(1.0, max(0.0, u)) * (b['z'] - a['z'])}
    return best

def cross(a, b, c, d):
    def o(p, q, r):
        return (q['x'] - p['x']) * (r['y'] - p['y']) - (q['y'] - p['y']) * (r['x'] - p['x'])
    d1 = o(a, b, c)
    d2 = o(a, b, d)
    d3 = o(c, d, a)
    d4 = o(c, d, b)
    return ((d1 > 1e-12 and d2 < -1e-12) or (d1 < -1e-12 and d2 > 1e-12)) and \
           ((d3 > 1e-12 and d4 < -1e-12) or (d3 < -1e-12 and d4 > 1e-12))