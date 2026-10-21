import math
import re

METRES_PER = {
    'm': 1.0,
    'ft': 0.3048,
    'ftUS': 1200 / 3937  # 약 0.3048006096...
}

LIMITS = {
    'fileBytes': 200 * 1024 * 1024,  # 200MB
    'points': 500000,  # 최대 포인트 수
    'tinNodes': 500000,  # 그리드 TIN 노드 수
    'readCells': 400e6,  # 읽기 최대 셀 수
    'dim': 1e6,  # 래스터 최대 너비/높이
}

UNIT_OF_EPSG = {9001: 'm', 9002: 'ft', 9003: 'ftUS'}
EPSG_OF_UNIT = {'m': 9001, 'ft': 9002, 'ftUS': 9003}
UNIT_SHORT = {'m': 'm', 'ft': 'ft', 'ftUS': 'ft (US)'}


def unit_from_name(s):
    if s is None:
        return None
    t_str = str(s).strip().lower()
    t_str = re.sub(r'[_\s]+', ' ', t_str)
    if not t_str:
        return None
    if re.match(r'^(m|metre|meter|metres|meters|9001)$', t_str):
        return 'm'
    if re.match(r'^(us survey foot|us survey feet|survey foot|us-ft|ftus|us ft|foot us|foot_us|9003|us foot)$', t_str):
        return 'ftUS'
    if re.match(r'^(ft|foot|feet|international foot|intl foot|9002)$', t_str):
        return 'ft'
    return None


def project_z_unit(project):
    s = project.get('state', {})
    if s.get('units') == 'm':
        return 'm'
    crs = s.get('crs', {})
    return 'ft' if crs.get('unit') == 'ft' else 'ftUS'


def z_factor(from_unit, to_unit):
    return METRES_PER[from_unit] / METRES_PER[to_unit]


def box_through(b, fn, n=16):
    o = {'minX': float('inf'), 'minY': float('inf'), 'maxX': float('-inf'), 'maxY': float('-inf')}

    def add(x, y):
        res = fn(x, y)
        if not res or len(res) < 2:
            return
        u, v = res[0], res[1]
        if not (math.isfinite(u) and math.isfinite(v)):
            return
        o['minX'] = min(o['minX'], u)
        o['maxX'] = max(o['maxX'], u)
        o['minY'] = min(o['minY'], v)
        o['maxY'] = max(o['maxY'], v)

    for i in range(n + 1):
        t_val = i / n
        x = b['minX'] + (b['maxX'] - b['minX']) * t_val
        y = b['minY'] + (b['maxY'] - b['minY']) * t_val
        add(x, b['minY'])
        add(x, b['maxY'])
        add(b['minX'], y)
        add(b['maxX'], y)
    return o if math.isfinite(o['minX']) else None


def node_xy(src, col, row):
    g = src['gt']
    c = col + 0.5
    r = row + 0.5
    return [g[0] + c * g[1] + r * g[2], g[3] + c * g[4] + r * g[5]]


def grid_window(src, box):
    g = src['gt']
    det = g[1] * g[5] - g[2] * g[4]
    if not det or not box:
        return None

    def inv(x, y):
        dx = x - g[0]
        dy = y - g[3]
        return [(g[5] * dx - g[2] * dy) / det - 0.5, (-g[4] * dx + g[1] * dy) / det - 0.5]

    c0, r0, c1, r1 = float('inf'), float('inf'), float('-inf'), float('-inf')
    corners = [
        (box['minX'], box['minY']),
        (box['maxX'], box['minY']),
        (box['maxX'], box['maxY']),
        (box['minX'], box['maxY'])
    ]
    for x, y in corners:
        c, r = inv(x, y)
        c0 = min(c0, c)
        c1 = max(c1, c)
        r0 = min(r0, r)
        r1 = max(r1, r)

    w = {
        'c0': max(0, math.ceil(c0 - 1e-9)),
        'r0': max(0, math.ceil(r0 - 1e-9)),
        'c1': min(src['width'], math.floor(c1 + 1e-9) + 1),
        'r1': min(src['height'], math.floor(r1 + 1e-9) + 1)
    }
    return w if w['c1'] > w['c0'] and w['r1'] > w['r0'] else None


def next_number(points):
    hi = 0
    for p in points:
        try:
            n = int(p.get('n', 0))
            if n > hi and n < 1e12:
                hi = n
        except (TypeError, ValueError):
            pass
    return hi + 1


def grid_points(grid, src, fn, zf=1.0, desc='DEM', start=1):
    out = []
    n = start
    nx = grid['nx']
    ny = grid['ny']
    z_arr = grid['z']
    c0 = grid['c0']
    r0 = grid['r0']
    step = grid['step']

    for j in range(ny):
        for i in range(nx):
            z = z_arr[j * nx + i]
            if math.isnan(z):
                continue
            sx, sy = node_xy(src, c0 + i * step, r0 + j * step)
            res = fn(sx, sy)
            if not res or len(res) < 2:
                continue
            x, y = res[0], res[1]
            if not (math.isfinite(x) and math.isfinite(y)):
                continue
            out.append({'n': str(n), 'x': x, 'y': y, 'z': z * zf, 'd': desc})
            n += 1
    return out


def grid_tin(grid, src, fn, zf=1.0):
    nx = grid['nx']
    ny = grid['ny']
    z_arr = grid['z']
    c0 = grid['c0']
    r0 = grid['r0']
    step = grid['step']

    idx = [-1] * (nx * ny)
    pts = []

    for j in range(ny):
        for i in range(nx):
            v = z_arr[j * nx + i]
            if math.isnan(v):
                continue
            sx, sy = node_xy(src, c0 + i * step, r0 + j * step)
            res = fn(sx, sy)
            if not res or len(res) < 2:
                continue
            x, y = res[0], res[1]
            if not (math.isfinite(x) and math.isfinite(y)):
                continue
            idx[j * nx + i] = len(pts)
            pts.append({'x': x, 'y': y, 'z': v * zf})

    faces = []
    cells = 0
    skipped = 0

    for j in range(ny - 1):
        for i in range(nx - 1):
            a = idx[(j + 1) * nx + i]
            b = idx[(j + 1) * nx + i + 1]
            c = idx[j * nx + i + 1]
            d = idx[j * nx + i]
            cells += 1
            if a >= 0 and b >= 0 and c >= 0:
                faces.append([a, b, c])
            else:
                skipped += 1
            if a >= 0 and c >= 0 and d >= 0:
                faces.append([a, c, d])
            else:
                skipped += 1

    return {'pts': pts, 'faces': faces, 'cells': cells, 'skipped': skipped}


def nice_step(x):
    if not (x > 0) or not math.isfinite(x):
        return 1.0
    p = 10.0 ** math.floor(math.log10(x))
    m = x / p
    if m <= 1.0 + 1e-9:
        factor = 1.0
    elif m <= 2.0 + 1e-9:
        factor = 2.0
    elif m <= 5.0 + 1e-9:
        factor = 5.0
    else:
        factor = 10.0
    return factor * p