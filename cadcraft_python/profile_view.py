import math
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath, QTransform

def format_station(sta, units='ft', decimals=2):
    if sta is None or not math.isfinite(sta):
        return ""
    return f"{sta:.{decimals}f}"

def fixed(v, decimals=2):
    if v is None or not math.isfinite(v):
        return ""
    return f"{v:.{decimals}f}"

def pct(g):
    if g is None or not math.isfinite(g):
        return ""
    return f"{g * 100:.2f}%"

def nice_step(raw, steps):
    for s in steps:
        if s >= raw:
            return s
    return steps[-1] * math.ceil(raw / steps[-1])

class ProfileView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        self.pad = {'l': 58, 'r': 16, 't': 14, 'b': 30}
        self.z0 = 0.0
        self.z1 = 10.0

    def set_data(self, d):
        keep = self.data and d and self.data.get('key') == d.get('key')
        self.data = d
        if not keep:
            self.fit_y()
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_y()
        self.update()

    def fit_y(self):
        d = self.data
        if not d:
            return
        lo, hi = float('inf'), float('-inf')
        for p in d.get('eg', []):
            z = p.get('z')
            if z is not None and math.isfinite(z):
                lo = min(lo, z)
                hi = max(hi, z)
        for v in d.get('pvis', []):
            z = v.get('z')
            if z is not None and math.isfinite(z):
                lo = min(lo, z)
                hi = max(hi, z)
        for f in d.get('features', []):
            pts = f.get('crossings', []) + [pt for r in f.get('runs', []) for pt in r]
            for q in pts:
                z = q.get('z')
                if z is not None and math.isfinite(z):
                    lo = min(lo, z)
                    hi = max(hi, z)
        if not math.isfinite(lo):
            lo, hi = 0.0, 10.0
        span = max(hi - lo, 2.0)
        m = span * 0.15
        self.z0 = lo - m
        self.z1 = hi + m

    @property
    def plot_rect(self):
        w, h = self.width(), self.height()
        p = self.pad
        return {'x0': p['l'], 'x1': w - p['r'], 'y0': h - p['b'], 'y1': p['t']}

    def to_screen(self, sta, z):
        d = self.data
        P = self.plot_rect
        sta_start = d.get('start', 0.0)
        sta_end = d.get('end', 1.0)
        dx = max(sta_end - sta_start, 1e-9)
        dz = max(self.z1 - self.z0, 1e-9)
        sx = P['x0'] + (sta - sta_start) / dx * (P['x1'] - P['x0'])
        sy = P['y0'] - (z - self.z0) / dz * (P['y0'] - P['y1'])
        return sx, sy

    def to_data(self, sx, sy):
        d = self.data
        P = self.plot_rect
        sta_start = d.get('start', 0.0)
        sta_end = d.get('end', 1.0)
        sta = sta_start + (sx - P['x0']) / max(P['x1'] - P['x0'], 1e-9) * (sta_end - sta_start)
        z = self.z0 + (P['y0'] - sy) / max(P['y0'] - P['y1'], 1e-9) * (self.z1 - self.z0)
        return {'sta': sta, 'z': z}

    def hit_pvi(self, sx, sy, px=9):
        d = self.data
        if not d:
            return -1
        best, bd = -1, px
        for i, v in enumerate(d.get('pvis', [])):
            x, y = self.to_screen(v['sta'], v['z'])
            dd = math.hypot(x - sx, y - sy)
            if dd < bd:
                bd = dd
                best = i
        return best

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        bg = QColor("#ffffff")
        ink = QColor("#17202b")
        ink2 = QColor("#34404e")
        grid_col = QColor("#d5dde5")
        eg_col = QColor("#708090")
        fg_col = QColor("#b3122e")
        action_col = QColor("#1e48c8")
        green_col = QColor("#17703a")
        muted_col = QColor("#808080")
        fl_col = QColor("#5b3cc4")

        painter.fillRect(0, 0, w, h, bg)

        d = self.data
        if not d:
            painter.setPen(ink2)
            painter.setFont(QFont("Arial", 12))
            painter.drawText(0, 0, w, h, Qt.AlignmentFlag.AlignCenter, "No profile data")
            return

        P = self.plot_rect
        u = d.get('units', 'ft')
        sta_start = d.get('start', 0.0)
        sta_end = d.get('end', 1.0)
        length = sta_end - sta_start

        px_per_sta = (P['x1'] - P['x0']) / max(length, 1e-9)
        s_step_opts = [10, 20, 50, 100, 200, 500, 1000] if u == 'm' else [25, 50, 100, 200, 500, 1000, 2000]
        s_step = nice_step(70 / max(px_per_sta, 1e-9), s_step_opts)

        px_per_z = (P['y0'] - P['y1']) / max(self.z1 - self.z0, 1e-9)
        z_step = nice_step(28 / max(px_per_z, 1e-9), [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100])

        # 그리드 축 & 라벨
        painter.setPen(QPen(grid_col, 1))
        painter.setFont(QFont("Arial", 9))

        s_curr = math.ceil(sta_start / s_step) * s_step
        while s_curr <= sta_end + 1e-9:
            x, _ = self.to_screen(s_curr, self.z0)
            painter.drawLine(int(x), int(P['y1']), int(x), int(P['y0']))
            painter.setPen(ink2)
            painter.drawText(int(x) - 30, int(P['y0']) + 4, 60, 20, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, format_station(s_curr, u, 0))
            painter.setPen(QPen(grid_col, 1))
            s_curr += s_step

        z_curr = math.ceil(self.z0 / z_step) * z_step
        while z_curr <= self.z1 + 1e-9:
            _, y = self.to_screen(sta_start, z_curr)
            painter.drawLine(int(P['x0']), int(y), int(P['x1']), int(y))
            painter.setPen(ink2)
            painter.drawText(int(P['x0']) - 50, int(y) - 10, 44, 20, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, fixed(z_curr, 1 if z_step < 1 else 0))
            painter.setPen(QPen(grid_col, 1))
            z_curr += z_step

        painter.setPen(QPen(ink, 1))
        painter.drawRect(int(P['x0']), int(P['y1']), int(P['x1'] - P['x0']), int(P['y0'] - P['y1']))

        ve = px_per_z / max(px_per_sta, 1e-9)
        painter.setPen(ink2)
        painter.drawText(int(P['x0']) + 6, int(P['y1']) + 4, 150, 20, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, f"VE: {round(ve) if ve >= 10 else f'{ve:.1f}'}x")

        # 도화 영역 클리핑
        painter.save()
        painter.setClipRect(int(P['x0']), int(P['y1']), int(P['x1'] - P['x0']), int(P['y0'] - P['y1']))

        # 기존 지반선 (EG)
        pen_eg = QPen(eg_col, 1.5)
        painter.setPen(pen_eg)
        path_eg = QPainterPath()
        pen_down = False
        for p in d.get('eg', []):
            z = p.get('z')
            if z is None:
                pen_down = False
                continue
            sx, sy = self.to_screen(p['sta'], z)
            if pen_down:
                path_eg.lineTo(sx, sy)
            else:
                path_eg.moveTo(sx, sy)
                pen_down = True
        painter.drawPath(path_eg)

        # PVI 접선 (Dash Line)
        pvis = d.get('pvis', [])
        if len(pvis) >= 2:
            pen_pvi = QPen(muted_col, 1, Qt.PenStyle.DashLine)
            painter.setPen(pen_pvi)
            path_pvi = QPainterPath()
            for i, v in enumerate(pvis):
                sx, sy = self.to_screen(v['sta'], v['z'])
                if i == 0:
                    path_pvi.moveTo(sx, sy)
                else:
                    path_pvi.lineTo(sx, sy)
            painter.drawPath(path_pvi)

        # 계획 종단선 (Design Profile)
        prof = d.get('profile')
        if prof and hasattr(prof, 'sample'):
            pen_prof = QPen(fg_col, 2.2)
            painter.setPen(pen_prof)
            path_prof = QPainterPath()
            samples = prof.sample(length / 400.0)
            for i, q in enumerate(samples):
                if q.get('z') is None:
                    continue
                sx, sy = self.to_screen(q['sta'], q['z'])
                if i == 0:
                    path_prof.moveTo(sx, sy)
                else:
                    path_prof.lineTo(sx, sy)
            painter.drawPath(path_prof)

        # 교차 피처 라인
        for f in d.get('features', []):
            col = action_col if f.get('id') == d.get('featSel') else fl_col
            pen_fl = QPen(col, 1.6, Qt.PenStyle.DashLine)
            painter.setPen(pen_fl)
            for r in f.get('runs', []):
                path_fl = QPainterPath()
                for i, q in enumerate(r):
                    sx, sy = self.to_screen(q['sta'], q['z'])
                    if i == 0:
                        path_fl.moveTo(sx, sy)
                    else:
                        path_fl.lineTo(sx, sy)
                painter.drawPath(path_fl)

        painter.restore()

        # 라벨 및 곡선 정보
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        if prof and hasattr(prof, 'grades'):
            for g in getattr(prof, 'grades', []):
                m_sta = (g['from'] + g['to']) / 2.0
                z_from = prof.elevation_at(g['from']) if hasattr(prof, 'elevation_at') else 0
                z_to = prof.elevation_at(g['to']) if hasattr(prof, 'elevation_at') else 0
                z_m = prof.elevation_at(m_sta) if hasattr(prof, 'elevation_at') else 0
                a = self.to_screen(g['from'], z_from or 0)
                b = self.to_screen(g['to'], z_to or 0)
                s = self.to_screen(m_sta, z_m or 0)

                if b[0] - a[0] >= 60:
                    painter.save()
                    angle = math.atan2(b[1] - a[1], b[0] - a[0])
                    painter.translate(s[0], s[1] - 4)
                    painter.rotate(math.degrees(angle))
                    painter.setPen(fg_col)
                    painter.drawText(-30, -2, 60, 15, Qt.AlignmentFlag.AlignCenter, pct(g.get('g', 0)))
                    painter.restore()

            for c in getattr(prof, 'curves', []):
                ax, ay = self.to_screen(c['bvc'], c['zBvc'])
                bx, by = self.to_screen(c['evc'], c['zEvc'])
                vx, vy = self.to_screen(c['pvi'], c['zPvi'])

                painter.setPen(QPen(fg_col, 1))
                painter.drawLine(int(ax), int(ay - 8), int(ax), int(ay + 8))
                painter.drawLine(int(bx), int(by - 8), int(bx), int(by + 8))

                up = (c.get('kind') == 'crest')
                ly = (min(vy, ay, by) - 16) if up else (max(vy, ay, by) + 16)

                painter.setPen(ink)
                lk_txt = f"L={fixed(c.get('L'), 2)} K={fixed(c.get('K'), 1)}"
                painter.drawText(int(vx) - 60, int(ly), 120, 15, Qt.AlignmentFlag.AlignCenter, lk_txt)

                hp = c.get('high') or c.get('low')
                if hp:
                    hx, hy = self.to_screen(hp['sta'], hp['z'])
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(green_col)
                    painter.drawEllipse(QPointF(hx, hy), 3.2, 3.2)

        # PVI 포인트 마커
        for i, v in enumerate(pvis):
            vx, vy = self.to_screen(v['sta'], v['z'])
            is_sel = (d.get('sel') == i)
            is_hov = (d.get('hover') == i)

            pen_pvi_pt = QPen(action_col if is_sel else fg_col, 2.4 if is_sel else 1.6)
            painter.setPen(pen_pvi_pt)
            painter.setBrush(bg)
            r_val = 6.0 if (is_sel or is_hov) else 4.5
            painter.drawEllipse(QPointF(vx, vy), r_val, r_val)

            if is_sel or len(pvis) <= 8:
                painter.setPen(ink2)
                painter.setFont(QFont("Arial", 8))
                lbl = f"PVI: {format_station(v['sta'], u)}\nEl: {fixed(v['z'], 2)}"
                painter.drawText(int(vx) - 50, int(vy) + 9, 100, 30, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, lbl)