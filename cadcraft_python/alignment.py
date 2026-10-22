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

    P = [p for p in (pis or []) if isinstance(p.get('x'), (int, float)) and isinstance(p.get('y'), (int, float))]
    Q = [p for i, p in enumerate(P) if i == 0 or math.hypot(p['x'] - P[i - 1]['x'], p['y'] - P[i - 1]['y']) > 1e-9]

    if len(Q) < 2:
        return Alignment([], start, ["최소 2개 이상의 유효한 PI가 필요합니다."], Q)

    n = len(Q)
    curves = [None] * n

    # 1단계: 각 내부 PI에서의 곡선 요소 및 필요 접선장(Ts) 사전 계산 및 검증
    for i in range(1, n - 1):
        pi = Q[i]
        r = float(pi.get('r', 0) or 0)
        ls = float(pi.get('ls', 0) or 0)

        dir_in = math.atan2(pi['y'] - Q[i - 1]['y'], pi['x'] - Q[i - 1]['x'])
        dir_out = math.atan2(Q[i + 1]['y'] - pi['y'], Q[i + 1]['x'] - pi['x'])
        d = norm_ang(dir_out - dir_in)
        delta_abs = abs(d)

        if r <= 0 or delta_abs < 1e-9:
            curves[i] = {'r': 0, 'ls': 0, 'Ts': 0, 'd': d, 'delta': delta_abs}
            continue

        if abs(delta_abs - math.pi) < 1e-6:
            errors.append(f"PI {i + 1}: 선형이 역방향으로 꺾입니다.")
            curves[i] = {'r': 0, 'ls': 0, 'Ts': 0, 'd': d, 'delta': delta_abs}
            continue

        p_shift = (ls ** 2) / (6.0 * r) if ls > 0 else 0.0
        q_offset = (ls / 2.0) if ls > 0 else 0.0
        Ts = (r + p_shift) * math.tan(delta_abs / 2.0) + q_offset

        curves[i] = {'r': r, 'ls': ls, 'Ts': Ts, 'd': d, 'delta': delta_abs}

    # 2단계: 인접 곡선 간 접선 길이 겹침 검증
    for i in range(n - 1):
        L = math.hypot(Q[i + 1]['x'] - Q[i]['x'], Q[i + 1]['y'] - Q[i]['y'])
        Ts_prev = curves[i].get('Ts', 0) if i > 0 and curves[i] else 0
        Ts_curr = curves[i + 1].get('Ts', 0) if i < n - 1 and curves[i + 1] else 0

        if Ts_prev + Ts_curr > L + 1e-9:
            errors.append(f"PI {i + 1}과 PI {i + 2} 사이의 곡선이 겹칩니다.")

    if errors:
        return Alignment([], start, errors, Q)

    # 3단계: 실제 선형 요소(Elements) 빌드
    sta = start
    cur = {'x': Q[0]['x'], 'y': Q[0]['y']}

    for i in range(1, n):
        prev_pi = Q[i - 1]
        pi = Q[i]
        c = curves[i] if i < n - 1 else None

        dir_in = math.atan2(pi['y'] - prev_pi['y'], pi['x'] - prev_pi['x'])

        if c and c['r'] > 0 and c['delta'] > 1e-9:
            Ts = c['Ts']
            ccw = c['d'] > 0
            r = c['r']
            ls = c['ls']
            delta_abs = c['delta']
            A = math.sqrt(r * ls) if ls > 0 else 0

            dist_pi = math.hypot(pi['x'] - prev_pi['x'], pi['y'] - prev_pi['y'])
            if Ts >= dist_pi / 2.0:
                Ts = dist_pi / 2.0

            ux, uy = math.cos(dir_in), math.sin(dir_in)
            ts_pt = {'x': pi['x'] - ux * Ts, 'y': pi['y'] - uy * Ts}

            # 1. 직선 구간
            line_len = math.hypot(ts_pt['x'] - cur['x'], ts_pt['y'] - cur['y'])
            if line_len > 1e-9:
                elements.append({'type': 'line', 'p0': cur, 'p1': ts_pt, 'dir': dir_in, 'sta': sta, 'len': line_len})
                sta += line_len
                cur = ts_pt

            cur_dir = dir_in

            # 2. 진입 완화곡선
            if ls > 0:
                elements.append({
                    'type': 'transition_in', 'p0': cur, 'r_start': float('inf'), 'r_end': r,
                    'A': A, 'ls': ls, 'ccw': ccw, 'sta': sta, 'len': ls, 'dir': cur_dir
                })
                # 끝점 계산 (단일 적분)
                tr_end_pt, cur_dir = _calc_clothoid_endpoint(A, ls, cur['x'], cur['y'], cur_dir, ccw, is_exit=False,
                                                             r=r)
                cur = tr_end_pt
                sta += ls
                theta_s = ls / (2.0 * r)
            else:
                theta_s = 0.0

            # 3. 원곡선
            arc_delta = delta_abs - (2.0 * theta_s)
            if arc_delta > 0:
                arc_len = r * arc_delta
                nx = -math.sin(cur_dir) if ccw else math.sin(cur_dir)
                ny = math.cos(cur_dir) if ccw else -math.cos(cur_dir)

                ctr = {'x': cur['x'] + nx * r, 'y': cur['y'] + ny * r}
                a0 = math.atan2(cur['y'] - ctr['y'], cur['x'] - ctr['x'])

                elements.append({
                    'type': 'arc', 'p0': cur, 'c': ctr, 'r': r, 'ccw': ccw, 'delta': arc_delta,
                    'a0': a0, 'sta': sta, 'len': arc_len
                })

                final_a = a0 + (arc_delta if ccw else -arc_delta)
                cur = {'x': ctr['x'] + math.cos(final_a) * r, 'y': ctr['y'] + math.sin(final_a) * r}
                cur_dir = final_a + (math.pi / 2 if ccw else -math.pi / 2)
                sta += arc_len

            # 4. 진출 완화곡선
            if ls > 0:
                elements.append({
                    'type': 'transition_out', 'p0': cur, 'r_start': r, 'r_end': float('inf'),
                    'A': A, 'ls': ls, 'ccw': ccw, 'sta': sta, 'len': ls, 'dir': cur_dir
                })
                tr_out_end_pt, cur_dir = _calc_clothoid_endpoint(A, ls, cur['x'], cur['y'], cur_dir, ccw, is_exit=True,
                                                                 r=r)
                cur = tr_out_end_pt
                sta += ls
        else:
            target = {'x': pi['x'], 'y': pi['y']}
            line_len = math.hypot(target['x'] - cur['x'], target['y'] - cur['y'])
            if line_len > 1e-9:
                elements.append({'type': 'line', 'p0': cur, 'p1': target, 'dir': dir_in, 'sta': sta, 'len': line_len})
                sta += line_len
                cur = target

    return Alignment(elements, start, errors, Q)


def _calc_clothoid_endpoint(A, ls, x0, y0, start_dir, ccw, is_exit=False, r=0.0):
    """완화곡선 끝점과 최종 방향각을 계산하는 고속 내부 함수"""
    if A <= 1e-9 or ls <= 1e-9:
        return {'x': x0 + ls * math.cos(start_dir), 'y': y0 + ls * math.sin(start_dir)}, start_dir

    steps = max(10, int(ls / 0.5))
    ds = ls / steps
    cx, cy = x0, y0
    curr_s = 0.0

    for _ in range(steps):
        s_mid = curr_s + ds / 2.0
        if not is_exit:
            cur_tau = (s_mid ** 2) / (2.0 * (A ** 2))
        else:
            cur_tau = (s_mid / r) - ((s_mid ** 2) / (2.0 * (A ** 2)))

        if not ccw:
            cur_tau = -cur_tau
        d_angle = start_dir + cur_tau
        cx += ds * math.cos(d_angle)
        cy += ds * math.sin(d_angle)
        curr_s += ds

    if not is_exit:
        final_tau = (ls ** 2) / (2.0 * (A ** 2))
    else:
        final_tau = (ls / r) - ((ls ** 2) / (2.0 * (A ** 2)))

    if not ccw:
        final_tau = -final_tau
    final_dir = start_dir + final_tau

    return {'x': cx, 'y': cy}, final_dir


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
        elif e['type'] == 'transition_in':
            pt, d = _calc_clothoid_endpoint(e['A'], s, e['p0']['x'], e['p0']['y'], e['dir'], e['ccw'], is_exit=False)
            return {'x': pt['x'], 'y': pt['y'], 'dir': d}
        elif e['type'] == 'transition_out':
            pt, d = _calc_clothoid_endpoint(e['A'], s, e['p0']['x'], e['p0']['y'], e['dir'], e['ccw'], is_exit=True,
                                            r=e['r_start'])
            return {'x': pt['x'], 'y': pt['y'], 'dir': d}
        elif e['type'] == 'arc':
            sw = (1 if e['ccw'] else -1) * s / e['r']
            a = e['a0'] + sw
            return {
                'x': e['c']['x'] + math.cos(a) * e['r'],
                'y': e['c']['y'] + math.sin(a) * e['r'],
                'dir': a + (math.pi / 2 if e['ccw'] else -math.pi / 2)
            }
        return None

    def polyline(self, max_seg=1.0, max_turn=math.pi / 360):
        """완화곡선 샘플링을 단일 패스로 최적화하여 렌더링 속도 대폭 향상"""
        out = []
        for e in self.elements:
            if not out:
                out.append({'x': e['p0']['x'], 'y': e['p0']['y'], 'sta': e['sta']})

            e_type = e.get('type')
            if e_type == 'line':
                p1 = e.get('p1', e['p0'])
                out.append({'x': p1['x'], 'y': p1['y'], 'sta': e['sta'] + e['len']})

            elif e_type in ('transition_in', 'transition_out'):
                # 단일 루프로 0부터 ls까지 누적 전진하며 모든 점을 한 번에 생성 ($O(N)$ 최적화)
                ls = e['len']
                steps = max(10, int(ls / 0.5))
                ds = ls / steps
                cx, cy = e['p0']['x'], e['p0']['y']
                start_dir = e['dir']
                ccw = e['ccw']
                A = e['A']
                is_exit = (e_type == 'transition_out')
                r = e.get('r_start', 0) if is_exit else 0.0

                curr_s = 0.0
                for k in range(1, steps + 1):
                    s_target = (ls * k) / steps
                    sub_ds = s_target - curr_s

                    s_mid = curr_s + sub_ds / 2.0
                    if not is_exit:
                        cur_tau = (s_mid ** 2) / (2.0 * (A ** 2))
                    else:
                        cur_tau = (s_mid / r) - ((s_mid ** 2) / (2.0 * (A ** 2)))

                    if not ccw:
                        cur_tau = -cur_tau
                    d_angle = start_dir + cur_tau
                    cx += sub_ds * math.cos(d_angle)
                    cy += sub_ds * math.sin(d_angle)
                    curr_s = s_target

                    out.append({'x': cx, 'y': cy, 'sta': e['sta'] + curr_s})

            elif e_type == 'arc':
                n = max(1, math.ceil(e['delta'] / max_turn),
                        math.ceil(e['len'] / max_seg) if max_seg != float('inf') else 1)
                for k in range(1, n + 1):
                    s = e['sta'] + (e['len'] * k) / n
                    p = self.point_at(s)
                    if p:
                        out.append({'x': p['x'], 'y': p['y'], 'sta': s})

        return out

    def ticks(self, step):
        if not (step > 0) or not self.elements:
            return []
        out = []
        k0 = math.ceil(self.start / step - 1e-9)
        k1 = math.floor(self.end / step + 1e-9)
        for k in range(k0, k1 + 1):
            sta = k * step
            p = self.point_at(sta)
            if p:
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