import math
import itertools
from delaunator import Delaunator
from robust_predicates import orient2d, incircle

SNAP = 1e-4


def next_e(e):
    return e - 2 if (e % 3 == 2) else e + 1


def prev_e(e):
    return e + 2 if (e % 3 == 0) else e - 1


# ---------------------------------------------------------------------------
# Building Surface

def build_surface(points=None, breaklines=None, boundary=None, max_edge=0):
    points = points or []
    breaklines = breaklines or []
    report = {
        'notes': [], 'errors': [], 'skippedNoZ': 0, 'merged': 0,
        'crossings': 0, 'zConflicts': 0, 'constraintFailures': 0
    }
    clipped = None
    if boundary and len(boundary) >= 3:
        first = _triangulate(points, breaklines, None, 0, {
            'notes': [], 'errors': [], 'skippedNoZ': 0, 'merged': 0,
            'crossings': 0, 'zConflicts': 0, 'constraintFailures': 0
        })
        if not first['surface']:
            report['errors'].extend(first['report']['errors'])
            return {'surface': None, 'report': report}
        hull = first['surface'].hull()
        clipped = clip_convex(ccw(boundary), hull)
        if len(clipped) < 3:
            report['errors'].append("Boundary could not be clipped.")
            return {'surface': None, 'report': report}

        clipped = [{'x': p['x'], 'y': p['y'], 'z': first['surface'].elevation_at(p['x'], p['y'], 1e-6)} for p in
                   clipped]
        if any(p['z'] is None for p in clipped):
            report['errors'].append("Boundary extends outside the surface data.")
            return {'surface': None, 'report': report}

    return _triangulate(points, breaklines, clipped, max_edge, report)


def _triangulate(points, breaklines, boundary, max_edge, report):
    ox, oy = float('inf'), float('inf')
    for p in points:
        if p.get('z') is not None and math.isfinite(p['z']):
            if p['x'] < ox: ox = p['x']
            if p['y'] < oy: oy = p['y']
    for b in breaklines:
        for p in b.get('pts', []):
            if p['x'] < ox: ox = p['x']
            if p['y'] < oy: oy = p['y']

    if not math.isfinite(ox):
        report['errors'].append("No valid point elevations found.")
        return {'surface': None, 'report': report}

    ox, oy = math.floor(ox), math.floor(oy)
    X, Y, Z = [], [], []
    key_map = {}

    def k_of(x, y):
        return f"{round(x / SNAP)},{round(y / SNAP)}"

    def add_v(x, y, z, hard):
        lx, ly = x - ox, y - oy
        k = k_of(lx, ly)
        if k in key_map:
            at = key_map[k]
            if abs(Z[at] - z) > 1e-3:
                report['zConflicts'] += 1
                if hard: Z[at] = z
            elif not hard:
                report['merged'] += 1
            return at
        idx = len(X)
        key_map[k] = idx
        X.append(lx)
        Y.append(ly)
        Z.append(z)
        return idx

    for p in points:
        if p.get('z') is None or not math.isfinite(p['z']):
            report['skippedNoZ'] += 1
            continue
        add_v(p['x'], p['y'], p['z'], False)

    segs = []
    for b in breaklines:
        pts = b.get('pts', [])
        for i in range(len(pts) - 1):
            a = add_v(pts[i]['x'], pts[i]['y'], pts[i]['z'], True)
            c = add_v(pts[i + 1]['x'], pts[i + 1]['y'], pts[i + 1]['z'], True)
            if a != c:
                segs.append([a, c, True])

    n_break = len(segs)
    if boundary:
        before = report['merged']
        ids = [add_v(p['x'], p['y'], p['z'], False) for p in boundary]
        report['merged'] = before
        for i in range(len(ids)):
            a, c = ids[i], ids[(i + 1) % len(ids)]
            if a != c:
                segs.append([a, c, False])

    pieces = split_crossings(X, Y, Z, segs, key_map, k_of, report)

    if len(X) < 3:
        report['errors'].append("At least 3 non-coincident points required.")
        return {'surface': None, 'report': report}

    coords = []
    for i in range(len(X)):
        coords.append(X[i])
        coords.append(-Y[i])  # y축 반전

    del_obj = Delaunator(coords)
    if not len(del_obj.triangles):
        report['errors'].append("Collinear points; cannot triangulate.")
        return {'surface': None, 'report': report}

    mesh = Mesh(X, Y, Z, list(del_obj.triangles), list(del_obj.halfedges))
    for a, b in pieces:
        if not mesh.constrain(a, b):
            report['constraintFailures'] += 1
    if pieces:
        mesh.legalize_all()

    keep = [1] * (len(mesh.tri) // 3)
    if boundary:
        poly = [{'x': p['x'] - ox, 'y': p['y'] - oy} for p in boundary]
        for t in range(len(keep)):
            a, b, c = mesh.tri[3 * t], mesh.tri[3 * t + 1], mesh.tri[3 * t + 2]
            cx_val = (X[a] + X[b] + X[c]) / 3.0
            cy_val = (Y[a] + Y[b] + Y[c]) / 3.0
            if not point_in_poly(cx_val, cy_val, poly):
                keep[t] = 0

    if max_edge > 0:
        mesh.peel(keep, max_edge)

    tris = []
    for t in range(len(keep)):
        if keep[t]:
            tris.extend([mesh.tri[3 * t], mesh.tri[3 * t + 1], mesh.tri[3 * t + 2]])

    if not tris:
        report['errors'].append("No triangles inside boundary.")
        return {'surface': None, 'report': report}

    surface = Surface(X, Y, Z, tris, ox, oy)
    surface.constrained_edges = mesh.constrained_pairs()
    return {'surface': surface, 'report': report}


# ---------------------------------------------------------------------------
# Split Crossings

def split_crossings(X, Y, Z, segs, key_map, k_of, report):
    cuts = [[] for _ in segs]
    order = sorted(range(len(segs)), key=lambda i: min(X[segs[i][0]], X[segs[i][1]]))
    active = []

    for i in order:
        a, b = segs[i][0], segs[i][1]
        min_x = min(X[a], X[b])
        active = [k for k in active if max(X[segs[k][0]], X[segs[k][1]]) >= min_x - SNAP]

        for j in active:
            c, d = segs[j][0], segs[j][1]
            if a in (c, d) or b in (c, d):
                continue
            hit = seg_hit(X[a], Y[a], X[b], Y[b], X[c], Y[c], X[d], Y[d])
            if not hit:
                continue
            x = X[a] + (X[b] - X[a]) * hit['t']
            y = Y[a] + (Y[b] - Y[a]) * hit['t']
            zi = Z[a] + (Z[b] - Z[a]) * hit['t']
            zj = Z[c] + (Z[d] - Z[c]) * hit['u']

            k_str = k_of(x, y)
            v = key_map.get(k_str)
            z = zi if segs[i][2] and not segs[j][2] else (
                zj if segs[j][2] and not segs[i][2] else (zi if i < j else zj))
            if v is None:
                v = len(X)
                key_map[k_str] = v
                X.append(x);
                Y.append(y);
                Z.append(z)
            if segs[i][2] and segs[j][2] and abs(zi - zj) > 0.01:
                report['zConflicts'] += 1
            report['crossings'] += 1
            cuts[i].append({'t': hit['t'], 'v': v})
            cuts[j].append({'t': hit['u'], 'v': v})
        active.append(i)

    out = []
    for i, (a, b, *_) in enumerate(segs):
        c_sorted = sorted(cuts[i], key=lambda item: item['t'])
        curr_from = a
        for item in c_sorted:
            v = item['v']
            if v != curr_from:
                out.append([curr_from, v])
            curr_from = v
        if curr_from != b:
            out.append([curr_from, b])
    return out


def seg_hit(ax, ay, bx, by, cx, cy, dx, dy):
    rx, ry = bx - ax, by - ay
    sx, sy = dx - cx, dy - cy
    den = rx * sy - ry * sx
    if abs(den) < 1e-12:
        return None
    t = ((cx - ax) * sy - (cy - ay) * sx) / den
    u = ((cx - ax) * ry - (cy - ay) * rx) / den
    eps = 1e-9
    if t <= eps or t >= 1 - eps or u <= eps or u >= 1 - eps:
        return None
    return {'t': t, 'u': u}


# ---------------------------------------------------------------------------
# Half-edge Mesh with Constraints

class Mesh:
    def __init__(self, X, Y, Z, tri, he):
        self.X, self.Y, self.Z = X, Y, Z
        self.tri, self.he = tri, he
        self.con = [0] * len(he)
        self.vmap = [-1] * len(X)
        for e in range(len(tri)):
            self.vmap[tri[e]] = e

    def orient(self, a, b, c):
        return -orient2d(self.X[a], self.Y[a], self.X[b], self.Y[b], self.X[c], self.Y[c])

    def mark(self, e):
        self.con[e] = 1
        o = self.he[e]
        if o >= 0:
            self.con[o] = 1

    def around(self, v):
        out = []
        start = self.vmap[v]
        if start < 0:
            return out
        e = start
        open_hull = False
        while True:
            out.append(e)
            o = self.he[prev_e(e)]
            if o < 0:
                open_hull = True
                break
            e = o
            if e == start:
                break
        if open_hull:
            e = start
            while True:
                o = self.he[e]
                if o < 0:
                    break
                e = next_e(o)
                if e == start:
                    break
                out.append(e)
        return out

    def constrain(self, a0, b0):
        todo = [[a0, b0]]
        guard = 0
        while todo:
            guard += 1
            if guard > 100000:
                return False
            p, q = todo.pop()
            if p == q:
                continue
            if self.vmap[p] < 0 or self.vmap[q] < 0:
                return False
            r = self.walk(p, q)
            if r is None:
                return False
            if 'edge' in r:
                self.mark(r['edge'])
                if r.get('rest'):
                    todo.append(r['rest'])
                continue
            if not self.flip_out(p, q, r['crossed']):
                return False
            if r.get('rest'):
                todo.append(r['rest'])
        return True

    def walk(self, p, q):
        first = -1
        for e in self.around(p):
            b = self.tri[next_e(e)]
            c = self.tri[prev_e(e)]
            if b == q:
                return {'edge': e}
            if c == q:
                return {'edge': prev_e(e)}
            ob = self.side(p, q, b)
            oc = self.side(p, q, c)
            if ob == 0 and self.ahead(p, q, b):
                return {'edge': e, 'rest': [b, q]}
            if oc == 0 and self.ahead(p, q, c):
                return {'edge': prev_e(e), 'rest': [c, q]}
            if ob < 0 < oc:
                first = next_e(e)
                break
        if first < 0:
            return None

        crossed = []
        e = first
        for _ in range(1000000):
            if self.con[e]:
                return None
            crossed.append(e)
            o = self.he[e]
            if o < 0:
                return None
            v = self.tri[prev_e(o)]
            if v == q:
                return {'crossed': crossed, 'rest': None}
            ov = self.side(p, q, v)
            if ov == 0:
                return {'crossed': crossed, 'rest': [v, q], 'to': v}
            e = next_e(o) if ov > 0 else prev_e(o)
        return None

    def side(self, p, q, v):
        o = self.orient(p, q, v)
        if o == 0:
            return 0
        L = math.hypot(self.X[q] - self.X[p], self.Y[q] - self.Y[p])
        if abs(o) / L < 1e-7 * (1 + L):
            return 0
        return 1 if o > 0 else -1

    def ahead(self, p, q, v):
        dx, dy = self.X[q] - self.X[p], self.Y[q] - self.Y[p]
        t = ((self.X[v] - self.X[p]) * dx + (self.Y[v] - self.Y[p]) * dy) / (dx * dx + dy * dy)
        return 0 < t < 1

    def flip_out(self, p, q0, crossed):
        last = crossed[-1]
        o = self.he[last]
        q = self.tri[prev_e(o)]

        queue = list(crossed)
        made = []
        guard = 0
        while queue:
            guard += 1
            if guard > 50 * (len(crossed) + 10) ** 2:
                return False
            e = queue.pop(0)
            if not self.convex(e):
                queue.append(e)
                continue
            o = self.he[e]
            bot, top = prev_e(e), prev_e(o)
            for i in range(len(queue)):
                if queue[i] == bot:
                    queue[i] = o
                elif queue[i] == top:
                    queue[i] = e
            ne = self.flip(e)
            u, v = self.tri[ne], self.tri[next_e(ne)]
            if u not in (p, q) and v not in (p, q) and self.crosses(p, q, u, v):
                queue.append(ne)
            else:
                made.append(ne)

        found = False
        for e in self.around(p):
            if self.tri[next_e(e)] == q:
                self.mark(e);
                found = True;
                break
            if self.tri[prev_e(e)] == q:
                self.mark(prev_e(e));
                found = True;
                break
        if not found:
            return False

        stack = []
        for e in made:
            o = self.he[e]
            for f in (e, next_e(e), prev_e(e)):
                stack.append([self.tri[f], self.tri[next_e(f)]])
            if o >= 0:
                for f in (next_e(o), prev_e(o)):
                    stack.append([self.tri[f], self.tri[next_e(f)]])
        n = 0
        while stack and n < 200000:
            n += 1
            u, v = stack.pop()
            e = self.find_edge(u, v)
            if e < 0 or self.con[e] or self.he[e] < 0 or not self.illegal(e):
                continue
            ne = self.flip(e)
            o = self.he[ne]
            for f in (next_e(ne), prev_e(ne), next_e(o), prev_e(o)):
                stack.append([self.tri[f], self.tri[next_e(f)]])
        return True

    def legalize_all(self):
        stack = [[self.tri[e], self.tri[next_e(e)]] for e in range(len(self.tri)) if self.he[e] > e]
        n = 0
        while stack and n < 50 * len(self.tri):
            n += 1
            u, v = stack.pop()
            e = self.find_edge(u, v)
            if e < 0 or self.con[e] or self.he[e] < 0 or not self.illegal(e):
                continue
            ne = self.flip(e)
            o = self.he[ne]
            for f in (next_e(ne), prev_e(ne), next_e(o), prev_e(o)):
                stack.append([self.tri[f], self.tri[next_e(f)]])

    def find_edge(self, u, v):
        for e in self.around(u):
            if self.tri[next_e(e)] == v: return e
            if self.tri[prev_e(e)] == v: return prev_e(e)
        return -1

    def crosses(self, p, q, u, v):
        a = self.orient(p, q, u);
        b = self.orient(p, q, v)
        c = self.orient(u, v, p);
        d = self.orient(u, v, q)
        return ((a > 0 > b) or (a < 0 < b)) and ((c > 0 > d) or (c < 0 < d))

    def convex(self, e):
        o = self.he[e]
        if o < 0: return False
        a, b, c, d = self.tri[e], self.tri[next_e(e)], self.tri[prev_e(e)], self.tri[prev_e(o)]
        s1 = self.orient(c, d, a);
        s2 = self.orient(c, d, b)
        return (s1 > 0 > s2) or (s1 < 0 < s2)

    def illegal(self, e):
        o = self.he[e]
        if o < 0: return False
        a, b, c, d = self.tri[e], self.tri[next_e(e)], self.tri[prev_e(e)], self.tri[prev_e(o)]
        return incircle(self.X[a], self.Y[a], self.X[b], self.Y[b], self.X[c], self.Y[c], self.X[d],
                        self.Y[d]) > 0 and self.convex(e)

    def flip(self, e):
        o = self.he[e]
        bot, lft, top, rgt = prev_e(e), next_e(e), prev_e(o), next_e(o)
        adj_bot, adj_top = self.he[bot], self.he[top]
        c_bot, c_top = self.con[bot], self.con[top]

        self.tri[e] = self.tri[top]
        self.he[e] = adj_top
        if adj_top >= 0: self.he[adj_top] = e
        self.con[e] = c_top

        self.tri[o] = self.tri[bot]
        self.he[o] = adj_bot
        if adj_bot >= 0: self.he[adj_bot] = o
        self.con[o] = c_bot

        self.he[bot] = top
        self.he[top] = bot
        self.con[bot] = 0
        self.con[top] = 0

        self.vmap[self.tri[e]] = e
        self.vmap[self.tri[lft]] = lft
        self.vmap[self.tri[o]] = o
        self.vmap[self.tri[rgt]] = rgt
        return bot

    def peel(self, keep, max_edge):
        def length(e):
            return math.hypot(self.X[self.tri[next_e(e)]] - self.X[self.tri[e]],
                              self.Y[self.tri[next_e(e)]] - self.Y[self.tri[e]])

        def outer(e):
            o = self.he[e]
            return o < 0 or not keep[o // 3]

        stack = [e for e in range(len(self.tri)) if keep[e // 3] and outer(e)]
        while stack:
            e = stack.pop()
            t = e // 3
            if not keep[t] or self.con[e] or not outer(e) or length(e) <= max_edge:
                continue
            keep[t] = 0
            for f in (3 * t, 3 * t + 1, 3 * t + 2):
                o = self.he[f]
                if o >= 0 and keep[o // 3]:
                    stack.append(o)

    def constrained_pairs(self):
        out = []
        for e in range(len(self.tri)):
            if self.con[e] and (self.he[e] < 0 or e < self.he[e]):
                out.append([self.tri[e], self.tri[next_e(e)]])
        return out


# ---------------------------------------------------------------------------
# Surface Class

class Surface:
    def __init__(self, X, Y, Z, tris, ox, oy):
        self.X, self.Y, self.Z = X, Y, Z
        self.tris = tris
        self.ox, self.oy = ox, oy
        self.nT = len(tris) // 3
        self.constrained_edges = []
        self._grid = None
        self._stats = None

    def used_vertices(self):
        used = [0] * len(self.X)
        for i in self.tris:
            used[i] = 1
        return used

    def stats(self):
        if self._stats:
            return self._stats
        used = self.used_vertices()
        n, sum_z = 0, 0.0
        min_z, max_z = float('inf'), float('-inf')
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')

        for i in range(len(self.X)):
            if not used[i]: continue
            n += 1;
            sum_z += self.Z[i]
            min_z = min(min_z, self.Z[i]);
            max_z = max(max_z, self.Z[i])
            min_x = min(min_x, self.X[i]);
            max_x = max(max_x, self.X[i])
            min_y = min(min_y, self.Y[i]);
            max_y = max(max_y, self.Y[i])

        a2, a3 = 0.0, 0.0
        for t in range(0, len(self.tris), 3):
            a, b, c = self.tris[t], self.tris[t + 1], self.tris[t + 2]
            ux, uy, uz = self.X[b] - self.X[a], self.Y[b] - self.Y[a], self.Z[b] - self.Z[a]
            vx, vy, vz = self.X[c] - self.X[a], self.Y[c] - self.Y[a], self.Z[c] - self.Z[a]
            cx = uy * vz - uz * vy
            cy = uz * vx - ux * vz
            cz = ux * vy - uy * vx
            a2 += abs(cz) / 2.0
            a3 += math.hypot(cx, cy, cz) / 2.0

        self._stats = {
            'points': n, 'triangles': self.nT,
            'minZ': min_z, 'maxZ': max_z, 'meanZ': sum_z / n if n else 0,
            'area2d': a2, 'area3d': a3,
            'bounds': {'minX': min_x + self.ox, 'minY': min_y + self.oy, 'maxX': max_x + self.ox,
                       'maxY': max_y + self.oy}
        }
        return self._stats

    @property
    def bounds(self):
        return self.stats()['bounds']

    def hull(self):
        used = self.used_vertices()
        pts = [{'x': self.X[i] + self.ox, 'y': self.Y[i] + self.oy} for i in range(len(self.X)) if used[i]]
        return convex_hull(pts)

    def grid(self):
        if self._grid:
            return self._grid
        s = self.stats()
        b = {'minX': s['bounds']['minX'] - self.ox, 'minY': s['bounds']['minY'] - self.oy,
             'maxX': s['bounds']['maxX'] - self.ox, 'maxY': s['bounds']['maxY'] - self.oy}
        n = max(1, round(math.sqrt(self.nT / 2.0)))
        w = max(b['maxX'] - b['minX'], 1e-9)
        h = max(b['maxY'] - b['minY'], 1e-9)
        nx = max(1, round(n * math.sqrt(w / h)))
        ny = max(1, round(n * math.sqrt(h / w)))
        cw, ch = w / nx, h / ny

        counts = [0] * (nx * ny + 1)

        def cells(t, f):
            a, c, d = self.tris[3 * t], self.tris[3 * t + 1], self.tris[3 * t + 2]
            x0 = min(self.X[a], self.X[c], self.X[d]);
            x1 = max(self.X[a], self.X[c], self.X[d])
            y0 = min(self.Y[a], self.Y[c], self.Y[d]);
            y1 = max(self.Y[a], self.Y[c], self.Y[d])
            i0, i1 = _clamp_i((x0 - b['minX']) / cw, nx), _clamp_i((x1 - b['minX']) / cw, nx)
            j0, j1 = _clamp_i((y0 - b['minY']) / ch, ny), _clamp_i((y1 - b['minY']) / ch, ny)
            for j in range(j0, j1 + 1):
                for i in range(i0, i1 + 1):
                    f(j * nx + i)

        for t in range(self.nT):
            cells(t, lambda k: counts.__setitem__(k + 1, counts[k + 1] + 1))
        for k in range(1, len(counts)):
            counts[k] += counts[k - 1]

        items = [0] * counts[-1]
        fill = list(counts[:-1])
        for t in range(self.nT):
            def add_item(k):
                items[fill[k]] = t
                fill[k] += 1

            cells(t, add_item)

        self._grid = {'b': b, 'nx': nx, 'ny': ny, 'cw': cw, 'ch': ch, 'start': counts, 'items': items}
        return self._grid

    def locate(self, lx, ly, tol=1e-9):
        g = self.grid()
        if lx < g['b']['minX'] - tol or lx > g['b']['maxX'] + tol or ly < g['b']['minY'] - tol or ly > g['b'][
            'maxY'] + tol:
            return None
        i, j = _clamp_i((lx - g['b']['minX']) / g['cw'], g['nx']), _clamp_i((ly - g['b']['minY']) / g['ch'], g['ny'])
        k = j * g['nx'] + i
        best, best_min = None, float('-inf')

        for s in range(g['start'][k], g['start'][k + 1]):
            t = g['items'][s]
            a, b, c = self.tris[3 * t], self.tris[3 * t + 1], self.tris[3 * t + 2]
            d = (self.Y[b] - self.Y[c]) * (self.X[a] - self.X[c]) + (self.X[c] - self.X[b]) * (self.Y[a] - self.Y[c])
            if d == 0: continue
            w1 = ((self.Y[b] - self.Y[c]) * (lx - self.X[c]) + (self.X[c] - self.X[b]) * (ly - self.Y[c])) / d
            w2 = ((self.Y[c] - self.Y[a]) * (lx - self.X[c]) + (self.X[a] - self.X[c]) * (ly - self.Y[c])) / d
            w3 = 1.0 - w1 - w2
            m = min(w1, w2, w3)
            if m >= 0:
                return {'t': t, 'w': [w1, w2, w3]}
            if m > best_min:
                best_min = m
                best = {'t': t, 'w': [w1, w2, w3]}

        if best and tol > 0:
            t = best['t']
            a, b, c = self.tris[3 * t], self.tris[3 * t + 1], self.tris[3 * t + 2]
            scale = max(
                math.hypot(self.X[b] - self.X[a], self.Y[b] - self.Y[a]),
                math.hypot(self.X[c] - self.X[b], self.Y[c] - self.Y[b]),
                math.hypot(self.X[a] - self.X[c], self.Y[a] - self.Y[c])
            )
            if -best_min * scale <= tol:
                w = [max(0.0, v) for v in best['w']]
                s_sum = sum(w)
                return {'t': t, 'w': [v / s_sum for v in w]}
        return None

    def elevation_at(self, x, y, tol=1e-9):
        r = self.locate(x - self.ox, y - self.oy, tol)
        if not r:
            return None
        t, w = r['t'], r['w']
        return w[0] * self.Z[self.tris[3 * t]] + w[1] * self.Z[self.tris[3 * t + 1]] + w[2] * self.Z[
            self.tris[3 * t + 2]]

    def slope_of(self, t):
        a, b, c = self.tris[3 * t], self.tris[3 * t + 1], self.tris[3 * t + 2]
        ux, uy, uz = self.X[b] - self.X[a], self.Y[b] - self.Y[a], self.Z[b] - self.Z[a]
        vx, vy, vz = self.X[c] - self.X[a], self.Y[c] - self.Y[a], self.Z[c] - self.Z[a]
        nx = uy * vz - uz * vy
        ny = uz * vx - ux * vz
        nz = ux * vy - uy * vx
        gx, gy = -nx / nz, -ny / nz
        return {'slope': math.hypot(gx, gy), 'dir': math.atan2(-gy, -gx), 'gx': gx, 'gy': gy}

    def slopes(self):
        out = []
        for t in range(self.nT):
            a, b, c = self.tris[3 * t], self.tris[3 * t + 1], self.tris[3 * t + 2]
            s = self.slope_of(t)
            sz = math.sqrt(abs((self.X[b] - self.X[a]) * (self.Y[c] - self.Y[a]) - (self.Y[b] - self.Y[a]) * (
                        self.X[c] - self.X[a])) / 2.0)
            out.append({
                'x': (self.X[a] + self.X[b] + self.X[c]) / 3.0 + self.ox,
                'y': (self.Y[a] + self.Y[b] + self.Y[c]) / 3.0 + self.oy,
                'slope': s['slope'], 'dir': s['dir'], 'size': sz
            })
        return out


# ---------------------------------------------------------------------------
# Geometry Helpers

def _clamp_i(v, n):
    i = math.floor(v)
    return 0 if i < 0 else (n - 1 if i >= n else i)


def convex_hull(pts):
    p = sorted(pts, key=lambda q: (q['x'], q['y']))
    if len(p) < 3:
        return p

    def cr(o, a, b):
        return (a['x'] - o['x']) * (b['y'] - o['y']) - (a['y'] - o['y']) * (b['x'] - o['x'])

    lo, hi = [], []
    for q in p:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], q) <= 0: lo.pop()
        lo.append(q)
    for q in reversed(p):
        while len(hi) >= 2 and cr(hi[-2], hi[-1], q) <= 0: hi.pop()
        hi.append(q)
    lo.pop();
    hi.pop()
    return lo + hi


def poly_area(pts):
    a = 0.0
    for i in range(len(pts)):
        p, q = pts[i], pts[(i + 1) % len(pts)]
        a += p['x'] * q['y'] - q['x'] * p['y']
    return a / 2.0


def ccw(pts):
    return list(reversed(pts)) if poly_area(pts) < 0 else list(pts)


def point_in_poly(x, y, pts):
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        a, b = pts[i], pts[j]
        if (a['y'] > y) != (b['y'] > y) and x < ((b['x'] - a['x']) * (y - a['y'])) / (b['y'] - a['y'] + 1e-12) + a['x']:
            inside = not inside
        j = i
    return inside


def clip_convex(subject, clip):
    out = list(subject)
    for i in range(len(clip)):
        if not out: break
        a, b = clip[i], clip[(i + 1) % len(clip)]
        inside = lambda p: (b['x'] - a['x']) * (p['y'] - a['y']) - (b['y'] - a['y']) * (p['x'] - a['x']) >= -1e-9
        inp = out;
        out = []
        for k in range(len(inp)):
            p, q = inp[k], inp[(k + 1) % len(inp)]
            ip, iq = inside(p), inside(q)
            if ip: out.append(p)
            if ip != iq:
                dx, dy = q['x'] - p['x'], q['y'] - p['y']
                ex, ey = b['x'] - a['x'], b['y'] - a['y']
                den = dx * ey - dy * ex
                if den != 0:
                    t = ((a['x'] - p['x']) * ey - (a['y'] - p['y']) * ex) / den
                    out.append({'x': p['x'] + dx * t, 'y': p['y'] + dy * t})
    res = []
    for i, p in enumerate(out):
        q = out[(i + 1) % len(out)]
        if math.hypot(p['x'] - q['x'], p['y'] - q['y']) > 1e-9:
            res.append(p)
    return res