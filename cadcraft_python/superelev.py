import math


def SUPER_DEFAULTS(units='ft'):
    if units == 'm':
        return {
            'on': False,
            'delta': 0.005,
            'rate': [[2100, None], [1300, 0.02], [800, 0.03], [550, 0.04], [380, 0.05], [0, 0.06]]
        }
    else:
        return {
            'on': False,
            'delta': 0.005,
            'rate': [[7000, None], [4300, 0.02], [2600, 0.03], [1800, 0.04], [1250, 0.05], [0, 0.06]]
        }


def fin(v):
    return isinstance(v, (int, float)) and math.isfinite(v)


def clean_super(o, units='ft'):
    if not o or not isinstance(o, dict):
        return None
    d = SUPER_DEFAULTS(units)
    raw_rate = o.get('rate', [])
    rate = []
    if isinstance(raw_rate, list):
        for r in raw_rate:
            if isinstance(r, list) and len(r) >= 2 and fin(r[0]) and 0 <= r[0] < 1e7:
                if r[1] is None or (fin(r[1]) and 0 <= r[1] <= 0.2):
                    rate.append([r[0], r[1]])
        rate.sort(key=lambda x: x[0], reverse=True)

    delta_val = o.get('delta')
    delta = delta_val if (fin(delta_val) and 0 < delta_val <= 0.05) else d['delta']
    return {
        'on': o.get('on') is True,
        'delta': delta,
        'rate': rate if rate else d['rate']
    }


def rate_for(r_val, rate):
    for r, e in rate:
        if r_val >= r:
            return e
    return rate[-1][1] if rate else None


def super_plan(al, super_obj=None, nc=0.02, lane=12):
    curves = []
    problems = []
    sp = super_obj or {}
    if not getattr(al, 'ok', True) or not sp.get('on'):
        return {'curves': curves, 'problems': problems}

    elements = getattr(al, 'elements', [])
    arcs = [e for e in elements if e.get('type') == 'arc']

    for i, c in enumerate(arcs):
        r_val = c.get('r', 0)
        e = rate_for(r_val, sp.get('rate', []))
        if e is None or not (e > 0):
            continue
        dir_str = 'left' if c.get('ccw') else 'right'
        delta = sp.get('delta', 0.005)
        Lr = (lane * e) / delta
        Lt = (nc / max(e, 1e-9)) * Lr
        pc = c.get('sta', 0)
        pt = pc + c.get('len', 0)

        st = {
            'lc0': pc - (2 * Lr) / 3.0,
            'fs0': pc + Lr / 3.0,
            'fs1': pt - Lr / 3.0,
            'lc1': pt + (2 * Lr) / 3.0
        }
        st['nc0'] = st['lc0'] - Lt
        st['nc1'] = st['lc1'] + Lt
        st['rc0'] = st['lc0'] + (Lr * min(1.0, nc / e))
        st['rc1'] = st['lc1'] - (Lr * min(1.0, nc / e))

        if st['fs1'] < st['fs0']:
            problems.append(f"Curve {i + 1} (R={r_val:.2f}) is too short for full superelevation.")

        curves.append({
            'i': i + 1,
            'R': r_val,
            'dir': dir_str,
            'outside': 'L' if dir_str == 'right' else 'R',
            'e': e,
            'Lr': Lr,
            'Lt': Lt,
            'pc': pc,
            'pt': pt,
            'stations': st
        })

    for k in range(1, len(curves)):
        if curves[k]['stations']['nc0'] < curves[k - 1]['stations']['nc1']:
            problems.append(
                f"Superelevation transitions overlap between curve {curves[k - 1]['i']} and {curves[k]['i']}.")

    return {'curves': curves, 'problems': problems}


def outside_at(c, sta, nc):
    s = c['stations']
    e = c['e']
    Lt = max(c['Lt'], 1e-9)
    Lr = max(c['Lr'], 1e-9)

    def up(x):
        if x <= s['nc0']: return nc
        if x <= s['lc0']: return nc - (nc * (x - s['nc0'])) / Lt
        return -(e * (x - s['lc0'])) / Lr

    def down(x):
        if x >= s['nc1']: return nc
        if x >= s['lc1']: return nc - (nc * (s['nc1'] - x)) / Lt
        return -(e * (s['lc1'] - x)) / Lr

    return max(up(sta), down(sta), -e)


def slopes_at(plan, sta, nc=0.02):
    l_val, r_val = nc, nc
    for c in (plan.get('curves') or []):
        s = c['stations']
        if sta <= s['nc0'] or sta >= s['nc1']:
            continue
        o = outside_at(c, sta, nc)
        inside = max(nc, -o)
        if c['outside'] == 'L':
            l_val, r_val = o, inside
        else:
            r_val, l_val = o, inside
    return {'L': l_val, 'R': r_val}


def key_stations(plan):
    out = []
    for c in (plan.get('curves') or []):
        for v in c['stations'].values():
            out.append(v)
    return out