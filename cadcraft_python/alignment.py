import math

TAU = math.pi * 2


def norm_ang(a):
    a %= TAU
    if a <= -math.pi:
        a += TAU
    if a > math.pi:
        a -= TAU
    return a


def build_alignment(pis, start=0):
    errors = []
    elements = []

    # 유효한 좌표를 가진 PI 필터링
    P = [p for p in (pis or []) if isinstance(p.get('x'), (int, float)) and isinstance(p.get('y'), (int, float))]

    # 연속된 중복 PI 제거
    Q = [p for i, p in enumerate(P) if i == 0 or math.hypot(p['x'] - P[i - 1]['x'], p['y'] - P[i - 1]['y']) > 1e-9]

    if len(Q) < 2:
        return Alignment([], start, ["최소 2개 이상의 유효한 PI가 필요합니다."], Q)

    n = len(Q)
    curves = [None] * n

    # 각 내부 PI에서의 곡선 요소 계산
    for i in range(1, n - 1):
        r = float(Q[i].get('r', 0) or 0)
        a1 = math.atan2(Q[i]['y'] - Q[i - 1]['y'], Q[i]['x'] - Q[i - 1]['x'])
        a2 = math.atan2(Q[i + 1]['y'] - Q[i]['y'], Q[i + 1]['x'] - Q[i]['x'])
        d = norm_ang(a2 - a1)

        if r <= 0 or abs(d) < 1e-9:
            curves[i] = {'r': 0, 'd': d, 'T': 0, 'a1': a1, 'a2': a2}
            continue
        if abs(abs(d) - math.pi) < 1e-6:
            errors.append(f"PI {i + 1}: 선형이 역방향으로 꺾입니다.")
            curves[i] = {'r': 0, 'd': d, 'T': 0, 'a1': a1, 'a2': a2}
            continue
        curves[i] = {'r': r, 'd': d, 'T': r * math.tan(abs(d) / 2), 'a1': a1, 'a2': a2}

    # 접선 길이 검증 (곡선 간 겹침 확인)
    for i in range(n - 1):
        L = math.hypot(Q[i + 1]['x'] - Q[i]['x'], Q[i + 1]['y'] - Q[i]['y'])
        need = (curves[i].get('T', 0) if curves[i] else 0) + (curves[i + 1].get('T', 0) if curves[i + 1] else 0)
        if need > L + 1e-9:
            errors.append(f"PI {i + 1}과 PI {i + 2} 사이의 곡선이 겹칩니다. (필요 접선합: {need:.2f}, 실제 거리: {L:.2f})")

    if errors:
        return Alignment([], start, errors, Q)

    sta = start
    cur = {'x': Q[0]['x'], 'y': Q[0]['y']}

    for i in range(1, n):
        c = curves[i] if i < n - 1 else None
        dir_val = math.atan2(Q[i]['y'] - Q[i - 1]['y'], Q[i]['x'] - Q[i - 1]['x'])
        ux, uy = math.cos(dir_val), math.sin(dir_val)
        T = c.get('T', 0) if c else 0
        end = {'x': Q[i]['x'] - ux * T, 'y': Q[i]['y'] - uy * T}  # PC 또는 마지막 점

        length = math.hypot(end['x'] - cur['x'], end['y'] - cur['y'])
        if length > 1e-9:
            elements.append({'type': 'line', 'p0': cur, 'p1': end, 'dir': dir_val, 'sta': sta, 'len': length})
            sta += length

        if c and c['r'] > 0:
            ccw = c['d'] > 0
            r = c['r']
            delta = abs(c['d'])
            nx = -uy if ccw else uy
            ny = ux if ccw else -ux
            ctr = {'x': end['x'] + nx * r, 'y': end['y'] + ny * r}
            dir2 = c['a2']
            pt = {'x': Q[i]['x'] + math.cos(dir2) * T, 'y': Q[i]['y'] + math.sin(dir2) * T}
            a0 = math.atan2(end['y'] - ctr['y'], end['x'] - ctr['x'])
            arc_len = r * delta

            elements.append({
                'type': 'arc', 'p0': end, 'p1': pt, 'c': ctr, 'r': r, 'ccw': ccw, 'delta': delta,
                'a0': a0, 'sta': sta, 'len': arc_len, 'pi': {'x': Q[i]['x'], 'y': Q[i]['y']}, 'piIndex': i,
                'T': T, 'E': r * (1 / math.cos(delta / 2) - 1), 'M': r * (1 - math.cos(delta / 2)),
                'chord': 2 * r * math.sin(delta / 2), 'dirIn': dir_val, 'dirOut': dir2
            })
            sta += arc_len
            cur = pt
        else:
            cur = {'x': Q[i]['x'], 'y': Q[i]['y']}

    return Alignment(elements, start, [], Q)


class Alignment:
    def __init__(self, elements, start, errors, pis=None):
        self.elements = elements
        self.start = start
        self.errors = errors
        self.pis = pis if pis is not None else []
        self.length = sum(e['len'] for e in elements)
        self.end = start + self.length

    @property
    def ok(self):
        return len(self.elements) > 0 and len(self.errors) == 0

    def element_at(self, sta):
        els = self.elements
        if not els:
            return None
        for e in els:
            if sta <= e['sta'] + e['len'] + 1e-9:
                return e
        return els[-1]

    def point_at(self, sta):
        e = self.element_at(sta)
        if not e:
            return None
        s = sta - e['sta']
        if e['type'] == 'line':
            return {
                'x': e['p0']['x'] + math.cos(e['dir']) * s,
                'y': e['p0']['y'] + math.sin(e['dir']) * s,
                'dir': e['dir']
            }
        sw = (1 if e['ccw'] else -1) * s / e['r']
        a = e['a0'] + sw
        return {
            'x': e['c']['x'] + math.cos(a) * e['r'],
            'y': e['c']['y'] + math.sin(a) * e['r'],
            'dir': a + (math.pi / 2 if e['ccw'] else -math.pi / 2)
        }

    def station_offset(self, x, y):
        best = None
        for e in self.elements:
            if e['type'] == 'line':
                ux, uy = math.cos(e['dir']), math.sin(e['dir'])
                s = max(0, min(e['len'], (x - e['p0']['x']) * ux + (y - e['p0']['y']) * uy))
                px = e['p0']['x'] + ux * s
                py = e['p0']['y'] + uy * s
                dir_val = e['dir']
            else:
                a = math.atan2(y - e['c']['y'], x - e['c']['x'])
                sw = ((a - e['a0']) * (1 if e['ccw'] else -1)) % TAU
                if sw < 0:
                    sw += TAU
                if sw > e['delta']:
                    sw = e['delta'] if (sw - e['delta'] < TAU - sw) else 0
                s = sw * e['r']
                aa = e['a0'] + (sw if e['ccw'] else -sw)
                px = e['c']['x'] + math.cos(aa) * e['r']
                py = e['c']['y'] + math.sin(aa) * e['r']
                dir_val = aa + (math.pi / 2 if e['ccw'] else -math.pi / 2)

            d = math.hypot(x - px, y - py)
            if best is None or d < best['d'] - 1e-12:
                off = (x - px) * math.sin(dir_val) - (y - py) * math.cos(dir_val)  # 우측이 양수(+)
                best = {'d': d, 'sta': e['sta'] + s, 'off': off, 'x': px, 'y': py, 'dir': dir_val}

        if best is None:
            return None

        def along(p, d_val):
            return (x - p['x']) * math.cos(d_val) + (y - p['y']) * math.sin(d_val)

        p0 = self.point_at(self.start)
        p1 = self.point_at(self.end)
        outside = (best['sta'] <= self.start + 1e-9 and along(p0, p0['dir']) < -1e-9) or \
                  (best['sta'] >= self.end - 1e-9 and along(p1, p1['dir']) > 1e-9)

        return {
            'sta': best['sta'], 'off': best['off'], 'x': best['x'], 'y': best['y'],
            'outside': outside, 'dist': best['d']
        }

    def polyline(self, max_seg=float('inf'), max_turn=math.pi / 360):
        out = []
        for e in self.elements:
            if not out:
                out.append({'x': e['p0']['x'], 'y': e['p0']['y'], 'sta': e['sta']})
            if e['type'] == 'line':
                out.append({'x': e['p1']['x'], 'y': e['p1']['y'], 'sta': e['sta'] + e['len']})
                continue
            n = max(1, math.ceil(e['delta'] / max_turn),
                    math.ceil(e['len'] / max_seg) if max_seg != float('inf') else 1)
            for k in range(1, n + 1):
                s = e['sta'] + (e['len'] * k) / n
                p = self.point_at(s)
                out.append({'x': p['x'], 'y': p['y'], 'sta': s})
        return out

    def ticks(self, step):
        if not (step > 0) or not self.elements:
            return []
        out = []
        k0 = math.ceil(self.start / step - 1e-9)
        k1 = math.floor(self.end / step + 1e-9)
        if k1 - k0 > 20000:
            return []
        for k in range(k0, k1 + 1):
            sta = k * step
            p = self.point_at(sta)
            out.append({'sta': sta, **p})
        return out

    def key_stations(self):
        out = [{'sta': self.start, 'kind': 'Start'}]
        for e in self.elements:
            if e['type'] == 'arc':
                out.append({'sta': e['sta'], 'kind': 'PC'})
                out.append({'sta': e['sta'] + e['len'], 'kind': 'PT'})
        out.append({'sta': self.end, 'kind': 'End'})
        return out