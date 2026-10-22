# cad_linework.py
import math

CAD_TAG = "CIVILCRAFT"  # featureline.js에서 사용하는 태그

INSUNITS = {
    1: ('in', 0.0254), 2: ('ft', 0.3048), 3: ('mi', 1609.344), 4: ('mm', 0.001),
    5: ['cm', 0.01], 6: ('m', 1), 7: ('km', 1000), 8: ('microinch', 2.54e-8),
    9: ('mil', 2.54e-5), 10: ('yd', 0.9144), 14: ('dm', 0.1), 21: ('ftUS', 1200 / 3937),
}
FEET = {'ft', 'ftUS'}
MAX_DEPTH = 8
MAX_VERTICES = 5000000
STEP = math.pi / 36  # 5°


def cad_units(header=None):
    if header is None:
        header = {}
    code = header.get('INSUNITS', 0)
    u = INSUNITS.get(code)
    if u:
        return {'code': code, 'label': u[0], 'metres': u[1]}
    return {'code': code, 'label': '', 'metres': None}


def unit_scale(header, project_unit='ft'):
    u = cad_units(header)
    to_unit = 'm' if project_unit == 'm' else 'ft'
    if not u['metres']:
        return {'scale': 1, 'from': '', 'to': to_unit, 'note': f"알 수 없는 CAD 단위 (대상: {to_unit})"}
    if to_unit == 'ft' and u['label'] in FEET:
        return {'scale': 1, 'from': u['label'], 'to': to_unit, 'note': None if u['label'] == 'ft' else None}
    if to_unit == 'm' and u['label'] == 'm':
        return {'scale': 1, 'from': 'm', 'to': to_unit, 'note': None}

    proj_m = 1 if to_unit == 'm' else 1200 / 3937
    if to_unit == 'ft' and u['label'] in {'in', 'mi', 'yd', 'mil', 'microinch'}:
        scale = u['metres'] / 0.3048
    else:
        scale = u['metres'] / proj_m
    return {'scale': scale, 'from': u['label'], 'to': to_unit,
            'note': f"단위 변환 스케일 적용: {u['label']} -> {to_unit} (배율: {scale:.10f})"}


# ---------------------------------------------------------------- 3D 아핀 변환 (3×4 행렬)
def mul(a, b):  # a ∘ b
    o = [0.0] * 12
    for r in range(3):
        for c in range(3):
            o[r * 4 + c] = a[r * 4] * b[c] + a[r * 4 + 1] * b[4 + c] + a[r * 4 + 2] * b[8 + c]
        o[r * 4 + 3] = a[r * 4] * b[3] + a[r * 4 + 1] * b[7] + a[r * 4 + 2] * b[11] + a[r * 4 + 3]
    return o


def apply_transform(m, x, y, z):
    return [
        m[0] * x + m[1] * y + m[2] * z + m[3],
        m[4] * x + m[5] * y + m[6] * z + m[7],
        m[8] * x + m[9] * y + m[10] * z + m[11]
    ]


def translate(x, y, z):
    return [1, 0, 0, x, 0, 1, 0, y, 0, 0, 1, z]


def ocs(ext):
    if not ext or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in
                          [ext.get('x', 0), ext.get('y', 0), ext.get('z', 0)]):
        return None
    x, y, z = ext['x'], ext['y'], ext['z']
    L = math.hypot(x, y, z)
    if not L:
        return None
    az = [x / L, y / L, z / L]
    if abs(az[0]) < 1e-12 and abs(az[1]) < 1e-12 and az[2] > 0:
        return None

    def cross(a, b):
        return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]

    ax = cross([0, 1, 0], az) if abs(az[0]) < 1 / 64 and abs(az[1]) < 1 / 64 else cross([0, 0, 1], az)
    n = math.hypot(*ax)
    if n > 0:
        ax = [v / n for v in ax]
    ay = cross(az, ax)
    return [ax[0], ay[0], az[0], 0, ax[1], ay[1], az[1], 0, ax[2], ay[2], az[2], 0]


def with_ocs(m, ext):
    o = ocs(ext)
    return mul(m, o) if o else m


# ---------------------------------------------------------------- 곡선 → 정점 변환
def arc_pts(cx, cy, r, a0, a1, z=0):
    sweep = a1 - a0
    while sweep <= 0:
        sweep += 2 * math.pi
    n = max(2, math.ceil(sweep / STEP))
    out = []
    for i in range(n + 1):
        a = a0 + (sweep * i) / n
        out.append([cx + r * math.cos(a), cy + r * math.sin(a), z])
    return out


def bulged_pts(vs, closed, z_of):
    out = []
    n = len(vs)
    for i in range(n):
        a = vs[i]
        z = z_of(a)
        out.append([a['x'], a['y'], z])
        if i == n - 1 and not closed:
            break
        b = vs[(i + 1) % n]
        bu = a.get('bulge', 0)
        if not bu or not math.isfinite(bu):
            continue
        dx = b['x'] - a['x']
        dy = b['y'] - a['y']
        c = math.hypot(dx, dy)
        if not c:
            continue
        theta = 4 * math.atan(bu)
        r = c / (2 * math.sin(theta / 2))
        mx = (a['x'] + b['x']) / 2
        my = (a['y'] + b['y']) / 2
        h = r * math.cos(theta / 2)
        cx = mx - (dy / c) * h
        cy = my + (dx / c) * h
        a0 = math.atan2(a['y'] - cy, a['x'] - cx)
        steps = max(1, math.ceil(abs(theta) / STEP))
        zb = z_of(b)
        for k in range(1, steps):
            ang = a0 + (theta * k) / steps
            R = abs(r)
            out.append([cx + R * math.cos(ang), cy + R * math.sin(ang), z + ((zb - z) * k) / steps])
    return out


def shape_of(e):
    def P(q):
        return [q.get('x', 0), q.get('y', 0), q.get('z', 0)]

    etype = e.get('type')
    if etype == 'LINE':
        return {'parts': [[P(e['start']), P(e['end'])]], 'wcs': True}
    elif etype == 'POINT':
        return {'point': P(e['position']), 'wcs': True}
    elif etype == 'CIRCLE':
        c = e['center']
        pts = arc_pts(c['x'], c['y'], e['radius'], 0, 2 * math.pi, c.get('z', 0))
        pts.pop()
        return {'parts': [pts], 'closed': True}
    elif etype == 'ARC':
        c = e['center']
        return {'parts': [arc_pts(c['x'], c['y'], e['radius'], e['startAngle'], e['endAngle'], c.get('z', 0))]}
    elif etype == 'LWPOLYLINE':
        z = e.get('elevation', 0)
        return {'parts': [bulged_pts(e.get('vertices', []), bool(e.get('closed')), lambda _: z)],
                'closed': bool(e.get('closed'))}
    elif etype == 'POLYLINE_3D':
        vs = [v for v in e.get('vertices', []) if not (v.get('flags', 0) & 16)]
        return {'parts': [[P(v) for v in vs]], 'closed': bool(e.get('closed')), 'wcs': True}
    return None


def dedupe(r):
    out = []
    for p in r:
        if not out or out[-1][0] != p[0] or out[-1][1] != p[1] or out[-1][2] != p[2]:
            out.append(p)
    if len(out) > 1 and out[0] == out[-1]:
        out.pop()
    return out


LINEWORK = {'LINE', 'POINT', 'CIRCLE', 'ARC', 'ELLIPSE', 'LWPOLYLINE', 'POLYLINE_2D', 'POLYLINE_3D', 'SPLINE', 'SOLID',
            'TRACE', '3DFACE', 'INSERT', 'MINSERT'}


def cad_linework(model, file='', project_unit='ft', scale=None, layers=None, skip_feature_lines=False):
    notes, skipped = [], {}
    header = model.get('header', {}) if model else {}
    us = unit_scale(header, project_unit)
    k = scale if scale and math.isfinite(scale) and scale > 0 else us['scale']

    blocks = {}
    for b in model.get('blocks', []) if model else []:
        blocks[str(b.get('name', '')).upper()] = b

    ms = blocks.get('*MODEL_SPACE')
    if not ms:
        return {'layers': [], 'cadLayers': [], 'skipped': skipped, 'units': cad_units(header), 'scale': k,
                'notes': ['모델 스페이스가 없습니다.']}

    keep = set(map(str, layers)) if layers else None
    table_layers = {l['name']: l for l in model.get('tables', {}).get('layers', [])} if model else {}
    by = {}
    vertices, depth_hit, cut = 0, 0, False
    top = [k, 0, 0, 0, 0, k, 0, 0, 0, 0, k, 0]

    def add(layer, kind, feat):
        if layer not in by:
            by[layer] = {'lines': [], 'polygons': [], 'points': []}
        by[layer][kind].append(feat)

    def props(layer, type_name, pts):
        z0 = pts[0][2] if pts else 0
        same = all(abs(p[2] - z0) <= 1e-9 * max(1, abs(z0)) for p in pts) if pts else True
        return {'LAYER': layer, 'TYPE': type_name, 'ELEV': z0 if same and math.isfinite(z0) and z0 != 0 else None}

    def shape(pts):
        flat = all(p[2] == 0 or abs(p[2]) < 1e-12 for p in pts)
        return [[p[0], p[1]] for p in pts] if flat else pts

    def walk(ents, m, inherit, depth):
        nonlocal vertices, depth_hit, cut
        for e in ents:
            if cut:
                return
            if not e or e.get('invisible'):
                continue
            layer = inherit if e.get('layer') == '0' and inherit else str(e.get('layer', '0'))
            etype = e.get('type')
            if etype not in LINEWORK:
                skipped[etype] = skipped.get(etype, 0) + 1
                continue

            sh = shape_of(e)
            if not sh:
                skipped[etype] = skipped.get(etype, 0) + 1
                continue

            mm = m if sh.get('wcs') else with_ocs(m, e.get('extrusion'))
            if keep and layer not in keep:
                continue

            if 'point' in sh:
                p = apply_transform(mm, *sh['point'])
                if not all(math.isfinite(val) for val in p):
                    continue
                add(layer, 'points', {'g': {'t': 'pt', 'c': shape([p])[0]}, 'p': props(layer, etype, [p])})
                vertices += 1
                continue

            for part in sh['parts']:
                pts = [apply_transform(mm, q[0], q[1], q[2]) for q in part]
                pts = [p for p in pts if all(math.isfinite(val) for val in p)]
                if len(pts) < 2 or (sh.get('closed') and len(pts) < 3):
                    continue
                vertices += len(pts)
                if vertices > MAX_VERTICES:
                    cut = True
                    return
                s2 = shape(pts)
                if sh.get('closed'):
                    add(layer, 'polygons', {'g': {'t': 'pg', 'c': [[[*s2, s2[0]]]]}, 'p': props(layer, etype, pts)})
                else:
                    add(layer, 'lines', {'g': {'t': 'ln', 'c': [s2]}, 'p': props(layer, etype, pts)})

    walk(ms.get('entities', []), top, None, 0)

    out, cad_layers = [], []
    for name in sorted(by.keys()):
        b = by[name]
        tl = table_layers.get(name)
        cad_layers.append({
            'name': name,
            'on': tl.get('on', True) and not tl.get('off', False) and not tl.get('frozen', False) if tl else True,
            'frozen': bool(tl and tl.get('frozen')),
            'lines': len(b['lines']), 'polygons': len(b['polygons']), 'points': len(b['points']), 'z': True
        })
        src = {'file': file, 'format': 'CAD', 'crs': None}
        for kk, geom in [('lines', 'ln'), ('polygons', 'pg'), ('points', 'pt')]:
            if b[kk]:
                out.append({'cadLayer': name, 'name': name, 'geom': geom, 'hasZ': True,
                            'fields': [{'name': 'LAYER', 'type': 'text'}, {'name': 'TYPE', 'type': 'text'},
                                       {'name': 'ELEV', 'type': 'number'}], 'features': b[kk], 'source': src})

    return {'layers': out, 'cadLayers': cad_layers, 'skipped': skipped, 'units': cad_units(header), 'scale': k,
            'notes': notes}