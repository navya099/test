import math

EPS = 1e-6  # 길이 허용오차 (1 µm)
EPS2 = EPS * EPS


def add(a, b):
    return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]


def sub(a, b):
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]


def mul(a, s):
    return [a[0] * s, a[1] * s, a[2] * s]


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0]
    ]


def length(a):
    return math.hypot(a[0], a[1], a[2])


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2])


def lerp(a, b, t):
    return [
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t,
        a[2] + (b[2] - a[2]) * t
    ]


def neg(a):
    return [-a[0], -a[1], -a[2]]


def near(a, b, tol=EPS):
    return dist(a, b) <= tol


def norm(a):
    l = length(a)
    return [a[0] / l, a[1] / l, a[2] / l] if l > 1e-15 else [0.0, 0.0, 0.0]


def perp(n):
    a = [1.0, 0.0, 0.0] if abs(n[0]) < 0.9 else [0.0, 1.0, 0.0]
    return norm(cross(n, a))


def parallel(a, b, tol=1e-9):
    return length(cross(norm(a), norm(b))) <= tol


def newell(pts):
    x, y, z = 0.0, 0.0, 0.0
    n = len(pts)
    for i in range(n):
        p = pts[i]
        q = pts[(i + 1) % n]
        x += (p[1] - q[1]) * (p[2] + q[2])
        y += (p[2] - q[2]) * (p[0] + q[0])
        z += (p[0] - q[0]) * (p[1] + q[1])
    return norm([x, y, z])


def poly_area3(pts):
    x, y, z = 0.0, 0.0, 0.0
    n = len(pts)
    for i in range(n):
        p = pts[i]
        q = pts[(i + 1) % n]
        x += (p[1] - q[1]) * (p[2] + q[2])
        y += (p[2] - q[2]) * (p[0] + q[0])
        z += (p[0] - q[0]) * (p[1] + q[1])
    return math.hypot(x, y, z) / 2.0


def plane_from(n, p):
    m = norm(n)
    k = 0 if abs(m[0]) > 1e-9 else (1 if abs(m[1]) > 1e-9 else 2)
    if m[k] < 0:
        m = neg(m)
    return {'n': m, 'd': dot(m, p)}


def on_plane(pl, p, tol=EPS):
    return abs(dot(pl['n'], p) - pl['d']) <= tol


def same_plane(a, b):
    return abs(dot(a['n'], b['n'])) > 1 - 1e-9 and abs(a['d'] * math.sign(dot(a['n'], b['n'])) - b['d']) <= EPS


def frame(n):
    u = [1.0, 0.0, 0.0] if abs(n[2]) > 0.999 else norm(cross([0.0, 0.0, 1.0], n))
    return {'u': u, 'v': cross(n, u), 'n': n}


def to2(f, p):
    return [dot(p, f['u']), dot(p, f['v'])]


def ray_to_segment(o, d, a, b):
    u = sub(b, a)
    w = sub(o, a)
    A = dot(d, d)
    B = dot(d, u)
    C = dot(u, u)
    D = dot(d, w)
    E = dot(u, w)
    den = A * C - B * B
    if den < 1e-14:
        s = 0.0
        t = -D / A if A != 0 else 0.0
    else:
        t = (B * E - C * D) / den
        s = (A * E - B * D) / den
    if s < 0.0:
        s = 0.0
        t = -D / A if A != 0 else 0.0
    elif s > 1.0:
        s = 1.0
        t = (B - D) / A if A != 0 else 0.0
    return {'t': t, 's': s, 'onRay': add(o, mul(d, t)), 'onSeg': add(a, mul(u, s))}


def closest_on_line(p, a, u):
    dot_uu = dot(u, u)
    s = dot(sub(p, a), u) / dot_uu if dot_uu != 0 else 0.0
    return {'s': s, 'p': add(a, mul(u, s))}


def line_line(o1, d1, o2, d2):
    w = sub(o1, o2)
    A = dot(d1, d1)
    B = dot(d1, d2)
    C = dot(d2, d2)
    D = dot(d1, w)
    E = dot(d2, w)
    den = A * C - B * B
    if abs(den) < 1e-14 * A * C:
        return None
    t = (B * E - C * D) / den
    s = (A * E - B * D) / den
    return {'t': t, 's': s, 'p1': add(o1, mul(d1, t)), 'p2': add(o2, mul(d2, s))}


def ray_plane(o, d, pl):
    den = dot(pl['n'], d)
    if abs(den) < 1e-12:
        return None
    t = (pl['d'] - dot(pl['n'], o)) / den
    return {'t': t, 'p': add(o, mul(d, t))}


def ray_tri(o, d, a, b, c):
    e1 = sub(b, a)
    e2 = sub(c, a)
    p = cross(d, e2)
    det = dot(e1, p)
    if abs(det) < 1e-14:
        return None
    inv = 1.0 / det
    s = sub(o, a)
    u = dot(s, p) * inv
    if u < -1e-9 or u > 1 + 1e-9:
        return None
    q = cross(s, e1)
    v = dot(d, q) * inv
    if v < -1e-9 or u + v > 1 + 1e-9:
        return None
    t = dot(e2, q) * inv
    return t if t > 0 else None


# ---- Matrices (Column-major) ----
IDENT = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]


def ident():
    return list(IDENT)


def mmul(a, b):
    r = [0.0] * 16
    for c in range(4):
        for rr in range(4):
            s = 0.0
            for k in range(4):
                s += a[k * 4 + rr] * b[c * 4 + k]
            r[c * 4 + rr] = s
    return r


def translation(t):
    return [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, t[0], t[1], t[2], 1.0]


def scaling(s, about=[0.0, 0.0, 0.0]):
    S = [s, 0.0, 0.0, 0.0, 0.0, s, 0.0, 0.0, 0.0, 0.0, s, 0.0, 0.0, 0.0, 0.0, 1.0]
    return mmul(translation(about), mmul(S, translation(neg(about))))


def rotation(axis, angle, about=[0.0, 0.0, 0.0]):
    x, y, z = norm(axis)
    c = math.cos(angle)
    s = math.sin(angle)
    t = 1.0 - c
    R = [
        t * x * x + c, t * x * y + s * z, t * x * z - s * y, 0.0,
        t * x * y - s * z, t * y * y + c, t * y * z + s * x, 0.0,
        t * x * z + s * y, t * y * z - s * x, t * z * z + c, 0.0,
        0.0, 0.0, 0.0, 1.0
    ]
    return mmul(translation(about), mmul(R, translation(neg(about))))


def apply(m, p):
    x, y, z = p[0], p[1], p[2]
    w = m[3] * x + m[7] * y + m[11] * z + m[15]
    if not w:
        w = 1.0
    return [
        (m[0] * x + m[4] * y + m[8] * z + m[12]) / w,
        (m[1] * x + m[5] * y + m[9] * z + m[13]) / w,
        (m[2] * x + m[6] * y + m[10] * z + m[14]) / w
    ]


def apply_dir(m, v):
    return [
        m[0] * v[0] + m[4] * v[1] + m[8] * v[2],
        m[1] * v[0] + m[5] * v[1] + m[9] * v[2],
        m[2] * v[0] + m[6] * v[1] + m[10] * v[2]
    ]


def apply_normal(m, n):
    inv = invert(m)
    return norm([
        inv[0] * n[0] + inv[1] * n[1] + inv[2] * n[2],
        inv[4] * n[0] + inv[5] * n[1] + inv[6] * n[2],
        inv[8] * n[0] + inv[9] * n[1] + inv[10] * n[2]
    ])


def det3(m):
    return (m[0] * (m[5] * m[10] - m[9] * m[6]) -
            m[4] * (m[1] * m[10] - m[9] * m[2]) +
            m[8] * (m[1] * m[6] - m[5] * m[2]))


def invert(m):
    a00, a01, a02, a03, a10, a11, a12, a13, a20, a21, a22, a23, a30, a31, a32, a33 = m
    b00 = a00 * a11 - a01 * a10
    b01 = a00 * a12 - a02 * a10
    b02 = a00 * a13 - a03 * a10
    b03 = a01 * a12 - a02 * a11
    b04 = a01 * a13 - a03 * a11
    b05 = a02 * a13 - a03 * a12
    b06 = a20 * a31 - a21 * a30
    b07 = a20 * a32 - a22 * a30
    b08 = a20 * a33 - a23 * a30
    b09 = a21 * a32 - a22 * a31
    b10 = a21 * a33 - a23 * a31
    b11 = a22 * a33 - a23 * a32

    det = b00 * b11 - b01 * b10 + b02 * b09 + b03 * b08 - b04 * b07 + b05 * b06
    if det == 0:
        return ident()
    det = 1.0 / det

    r = [0.0] * 16
    r[0] = (a11 * b11 - a12 * b10 + a13 * b09) * det
    r[1] = (a02 * b10 - a01 * b11 - a03 * b09) * det
    r[2] = (a31 * b05 - a32 * b04 + a33 * b03) * det
    r[3] = (a22 * b04 - a21 * b05 - a23 * b03) * det
    r[4] = (a12 * b08 - a10 * b11 - a13 * b07) * det
    r[5] = (a00 * b11 - a02 * b08 + a03 * b07) * det
    r[6] = (a32 * b02 - a30 * b05 - a33 * b01) * det
    r[7] = (a20 * b05 - a22 * b02 + a23 * b01) * det
    r[8] = (a10 * b10 - a11 * b08 + a13 * b06) * det
    r[9] = (a01 * b08 - a00 * b10 - a03 * b06) * det
    r[10] = (a30 * b04 - a31 * b02 + a33 * b00) * det
    r[11] = (a21 * b02 - a20 * b04 - a23 * b00) * det
    r[12] = (a11 * b07 - a10 * b09 - a12 * b06) * det
    r[13] = (a00 * b09 - a01 * b07 + a02 * b06) * det
    r[14] = (a31 * b01 - a30 * b03 - a32 * b00) * det
    r[15] = (a20 * b03 - a21 * b01 + a22 * b00) * det
    return r


def is_ident(m):
    return all(abs(v - IDENT[i]) < 1e-12 for i, v in enumerate(m))


def bbox_add(bb, p):
    if not bb:
        return {'min': list(p), 'max': list(p)}
    for k in range(3):
        if p[k] < bb['min'][k]:
            bb['min'][k] = p[k]
        if p[k] > bb['max'][k]:
            bb['max'][k] = p[k]
    return bb