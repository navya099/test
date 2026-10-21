import math


def sample_surface(surface, alignment, step=None):
    if not surface or not getattr(alignment, 'ok', True):
        return []
    al_len = getattr(alignment, 'length', 1000.0)
    al_start = getattr(alignment, 'start', 0.0)
    al_end = getattr(alignment, 'end', 1000.0)

    st = step if (step is not None and step > 0) else max(0.5, al_len / 1000.0)
    stas = set()

    s = al_start
    while s < al_end:
        stas.add(round(s, 6))
        s += st
    stas.add(al_end)

    key_stations = alignment.key_stations() if hasattr(alignment, 'key_stations') else []
    for k in key_stations:
        stas.add(k.get('sta') if isinstance(k, dict) else getattr(k, 'sta', 0))

    out = []
    for sta in sorted(list(stas)):
        p = alignment.point_at(sta) if hasattr(alignment, 'point_at') else alignment.pointAt(sta)
        z = surface.elevation_at(p['x'], p['y'], 1e-6) if hasattr(surface, 'elevation_at') else None
        out.append({'sta': sta, 'z': z})
    return out


def build_profile(pvis_in):
    errors = []
    pvis = []
    for p in (pvis_in or []):
        if math.isfinite(p.get('sta', float('nan'))) and math.isfinite(p.get('z', float('nan'))):
            pvis.append(dict(p))
    pvis.sort(key=lambda x: x['sta'])

    for i in range(1, len(pvis)):
        if pvis[i]['sta'] - pvis[i - 1]['sta'] < 1e-6:
            errors.append(f"Two PVIs too close at station {pvis[i]['sta']}")

    grades = []
    for i in range(len(pvis) - 1):
        dx = pvis[i + 1]['sta'] - pvis[i]['sta']
        dz = pvis[i + 1]['z'] - pvis[i]['z']
        g = dz / dx if dx > 0 else 0.0
        grades.append({'from': pvis[i]['sta'], 'to': pvis[i + 1]['sta'], 'g': g})

    curves = []
    for i in range(1, len(pvis) - 1):
        v = pvis[i]
        g1 = grades[i - 1]['g']
        g2 = grades[i]['g']
        A = (g2 - g1) * 100.0

        L = float(v.get('L', 0) or 0)
        if not L and float(v.get('K', 0) or 0) > 0:
            L = float(v.get('K', 0)) * abs(A)
        v['L'] = L

        if L <= 0 or abs(A) < 1e-9:
            continue

        bvc = v['sta'] - L / 2.0
        evc = v['sta'] + L / 2.0
        kind = 'crest' if g2 < g1 else 'sag'
        z_bvc = v['z'] - g1 * L / 2.0
        z_evc = v['z'] + g2 * L / 2.0

        c = {
            'i': i, 'pvi': v['sta'], 'zPvi': v['z'],
            'bvc': bvc, 'evc': evc, 'L': L, 'K': L / abs(A),
            'g1': g1, 'g2': g2, 'A': A, 'zBvc': z_bvc, 'zEvc': z_evc,
            'kind': kind
        }

        if g1 * g2 < 0:
            x = -g1 * L / (g2 - g1)
            pt = {'sta': bvc + x, 'z': z_bvc + g1 * x + (g2 - g1) * x * x / (2.0 * L)}
            if kind == 'crest':
                c['high'] = pt
            else:
                c['low'] = pt
        curves.append(c)

    for k, c in enumerate(curves):
        prev_end = curves[k - 1]['evc'] if k > 0 else pvis[0]['sta']
        left = pvis[c['i'] - 1]['sta']
        right = pvis[c['i'] + 1]['sta']
        if c['bvc'] < left - 1e-9 or c['bvc'] < prev_end - 1e-9:
            errors.append(f"Vertical curve at PVI {c['i'] + 1} extends before neighbor/start (L={c['L']:.2f})")
        if c['evc'] > right + 1e-9:
            errors.append(f"Vertical curve at PVI {c['i'] + 1} extends past neighbor (L={c['L']:.2f})")

    return Profile(pvis, grades, curves, errors)


class Profile:
    def __init__(self, pvis, grades, curves, errors):
        self.pvis = pvis
        self.grades = grades
        self.curves = curves
        self.errors = errors
        self.start = pvis[0]['sta'] if pvis else 0.0
        self.end = pvis[-1]['sta'] if pvis else 0.0

    @property
    def ok(self):
        return len(self.pvis) >= 2 and not self.errors

    def elevation_at(self, sta):
        P = self.pvis
        if len(P) < 2 or sta < self.start - 1e-9 or sta > self.end + 1e-9:
            return None
        for c in self.curves:
            if c['bvc'] <= sta <= c['evc']:
                x = sta - c['bvc']
                return c['zBvc'] + c['g1'] * x + (c['g2'] - c['g1']) * x * x / (2.0 * c['L'])
        for i in range(len(P) - 1):
            if sta <= P[i + 1]['sta'] + 1e-9:
                return P[i]['z'] + self.grades[i]['g'] * (sta - P[i]['sta'])
        return None

    def grade_at(self, sta):
        for c in self.curves:
            if c['bvc'] <= sta <= c['evc']:
                return c['g1'] + (c['g2'] - c['g1']) * (sta - c['bvc']) / c['L']
        for g in self.grades:
            if sta <= g['to'] + 1e-9:
                return g['g']
        return None

    def sample(self, step=None):
        s = {p['sta'] for p in self.pvis}
        for c in self.curves:
            n = max(8, math.ceil(c['L'] / (step if (step is not None and step > 0) else c['L'] / 32.0)))
            for k in range(n + 1):
                s.add(c['bvc'] + (c['L'] * k) / n)
        return [{'sta': sta, 'z': self.elevation_at(sta)} for sta in sorted(list(s))]