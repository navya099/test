import math
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath


def nice_step(raw, steps):
    for s in steps:
        if s >= raw:
            return s
    return steps[-1] * math.ceil(raw / steps[-1])


class SectionView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        self.pad = {'l': 58, 'r': 16, 't': 26, 'b': 30}
        self.o0 = -10
        self.o1 = 10
        self.z0 = 0
        self.z1 = 10
        self.ve = 1.0

    def set_data(self, d):
        self.data = d
        self.fit()
        self.update()  # 화면 갱신 (repaint)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit()
        self.update()

    @property
    def plot_rect(self):
        w = self.width()
        h = self.height()
        p = self.pad
        return {'x0': p['l'], 'x1': w - p['r'], 'y0': h - p['b'], 'y1': p['t']}

    def fit(self):
        d = self.data
        if not d or 'section' not in d:
            return
        s = d['section']
        P = self.plot_rect
        self.o0 = -s.get('left', 10)
        self.o1 = s.get('right', 10)

        lo, hi = float('inf'), float('-inf')
        for r in s.get('ground', []) + s.get('design', []):
            for q in r:
                lo = min(lo, q['z'])
                hi = max(hi, q['z'])
        for m in s.get('marks', []):
            if math.isfinite(m.get('z', float('nan'))):
                lo = min(lo, m['z'])
                hi = max(hi, m['z'])
        if not math.isfinite(lo):
            lo, hi = 0.0, 10.0

        plot_w = max(1.0, P['x1'] - P['x0'])
        plot_h = max(1.0, P['y0'] - P['y1'])
        px_per_o = plot_w / max(self.o1 - self.o0, 1e-9)

        span = max(hi - lo, 1.0) * 1.3
        fit_ve = (plot_h / span) / px_per_o
        exag = d.get('exaggeration')
        self.ve = exag if (exag is not None and exag > 0) else max(1.0, fit_ve)

        span = plot_h / (px_per_o * self.ve)
        mid = (lo + hi) / 2.0
        self.z0 = mid - span / 2.0
        self.z1 = mid + span / 2.0

    def to_screen(self, o, z):
        P = self.plot_rect
        x = P['x0'] + ((o - self.o0) / (self.o1 - self.o0)) * (P['x1'] - P['x0'])
        y = P['y0'] - ((z - self.z0) / (self.z1 - self.z0)) * (P['y0'] - P['y1'])
        return x, y

    def to_data(self, sx, sy):
        P = self.plot_rect
        o = self.o0 + ((sx - P['x0']) / (P['x1'] - P['x0'])) * (self.o1 - self.o0)
        z = self.z0 + ((P['y0'] - sy) / (P['y0'] - P['y1'])) * (self.z1 - self.z0)
        return {'o': o, 'z': z}

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        # 색상 토큰 정의
        bg = QColor("#ffffff")
        ink = QColor("#17202b")
        ink2 = QColor("#34404e")
        grid_col = QColor("#d5dde5")
        eg_col = QColor("#708090")
        fg_col = QColor("#b3122e")
        cut_col = QColor("#b4530f")
        fill_col = QColor("#17703a")
        ochre_col = QColor("#8a6a00")

        painter.fillRect(0, 0, w, h, bg)

        d = self.data
        s = d.get('section') if d else None
        if not s:
            painter.setPen(ink2)
            painter.setFont(QFont("Arial", 12))
            painter.drawText(0, 0, w, h, Qt.AlignmentFlag.AlignCenter, d.get('empty', '') if d else '')
            return

        P = self.plot_rect
        plot_w = P['x1'] - P['x0']
        plot_h = P['y0'] - P['y1']

        px_per_o = plot_w / max(self.o1 - self.o0, 1e-9)
        px_per_z = plot_h / max(self.z1 - self.z0, 1e-9)

        o_step = nice_step(60 / px_per_o, [1, 2, 5, 10, 20, 25, 50, 100, 200, 500])
        z_step = nice_step(24 / px_per_z, [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100])

        # 그리드 및 축 렌더링
        painter.setPen(QPen(grid_col, 1))
        painter.setFont(QFont("Arial", 9))

        # 오프셋(X축) 격자 및 라벨
        o_curr = math.ceil(self.o0 / o_step) * o_step
        while o_curr <= self.o1 + 1e-9:
            x, _ = self.to_screen(o_curr, 0)
            painter.drawLine(int(x), int(P['y1']), int(x), int(P['y0']))
            label = ("+" if o_curr > 0 else "") + f"{o_curr:.0f}"
            painter.setPen(ink2)
            painter.drawText(int(x) - 25, int(P['y0']) + 4, 50, 20,
                             Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, label)
            painter.setPen(QPen(grid_col, 1))
            o_curr += o_step

        # 표고(Y축) 격자 및 라벨
        z_curr = math.ceil(self.z0 / z_step) * z_step
        while z_curr <= self.z1 + 1e-9:
            _, y = self.to_screen(0, z_curr)
            painter.drawLine(int(P['x0']), int(y), int(P['x1']), int(y))
            label = f"{z_curr:.1f}" if z_step < 1 else f"{z_curr:.0f}"
            painter.setPen(ink2)
            painter.drawText(int(P['x0']) - 50, int(y) - 10, 44, 20,
                             Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label)
            painter.setPen(QPen(grid_col, 1))
            z_curr += z_step

        # 외곽 테두리
        painter.setPen(QPen(ink, 1))
        painter.drawRect(int(P['x0']), int(P['y1']), int(plot_w), int(plot_h))

        # 센터라인 (CL) 점선
        cl_x, _ = self.to_screen(0, 0)
        pen = QPen(fg_col, 1)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawLine(int(cl_x), int(P['y1']), int(cl_x), int(P['y0']))

        # 도화 영역 클리핑 (절토/성토 음영용)
        painter.save()
        painter.setClipRect(int(P['x0']), int(P['y1']), int(plot_w), int(plot_h))

        def z_at(runs, o_val):
            for r in runs:
                if o_val < r[0]['o'] - 1e-9 or o_val > r[-1]['o'] + 1e-9:
                    continue
                for i in range(1, len(r)):
                    if o_val <= r[i]['o'] + 1e-9:
                        p, q = r[i - 1], r[i]
                        w = q['o'] - p['o']
                        return p['z'] + ((q['z'] - p['z']) * (o_val - p['o'])) / w if w > 0 else q['z']
            return None

        os_list = sorted(list(set([q['o'] for r in s.get('ground', []) + s.get('design', []) for q in r])))

        # 절토(Cut) 및 성토(Fill) 채우기
        for part in s.get('parts', []):
            o0, o1 = part['o0'], part['o1']
            xs = [o0] + [o for o in os_list if o > o0 and o < o1] + [o1]

            path = QPainterPath()
            first = True
            for o_val in xs:
                z_val = z_at(s.get('design', []), o_val)
                if z_val is None: continue
                sx, sy = self.to_screen(o_val, z_val)
                if first:
                    path.moveTo(sx, sy)
                    first = False
                else:
                    path.lineTo(sx, sy)
            for o_val in reversed(xs):
                z_val = z_at(s.get('ground', []), o_val)
                if z_val is None: continue
                sx, sy = self.to_screen(o_val, z_val)
                path.lineTo(sx, sy)
            path.closeSubpath()

            c = cut_col if part['kind'] == 'cut' else fill_col
            brush_color = QColor(c)
            brush_color.setAlphaF(0.28)
            painter.fillPath(path, QBrush(brush_color))

        # 지반 및 설계선 그리기
        def draw_runs(runs, color, width, style=Qt.PenStyle.SolidLine):
            p_pen = QPen(color, width)
            p_pen.setStyle(style)
            painter.setPen(p_pen)
            for r in runs:
                path = QPainterPath()
                for idx, q in enumerate(r):
                    sx, sy = self.to_screen(q['o'], q['z'])
                    if idx == 0:
                        path.moveTo(sx, sy)
                    else:
                        path.lineTo(sx, sy)
                painter.drawPath(path)

        draw_runs(s.get('ground', []), eg_col, 1.6)
        if s.get('design') != s.get('ground'):
            draw_runs(s.get('design', []), fg_col, 2.2)

        painter.restore()  # 클리핑 복원

        # 코리더 포인트 마크 및 라벨 (겹침 방지 로직 포함)
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        last_x = -float('inf')
        row = 0
        for m in s.get('marks', []):
            mz = m.get('z')
            if not math.isfinite(mz): continue
            px, py = self.to_screen(m['o'], mz)

            painter.setPen(QPen(ochre_col, 1.5))
            painter.setBrush(bg)
            painter.drawEllipse(QPointF(px, py), 3.5, 3.5)

            text = m['code'].replace('_L', '').replace('_R', '')
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(text)

            if px - last_x < tw + 6:
                row = (row + 1) % 2
            else:
                row = 0
            last_x = px

            painter.setPen(ink2)
            painter.drawText(int(px) - tw // 2, int(py) - 18 - row * 13, tw + 4, 14, Qt.AlignmentFlag.AlignCenter, text)

        # 상단 헤더 (측점 정보 및 면적/배율 라벨)
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.setPen(ink)
        painter.drawText(int(P['x0']), 6, 200, 20, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                         d.get('station', ''))

        L = d.get('labels', {})
        parts_txt = [L[k] for k in ['cut', 'fill', 've'] if k in L]
        painter.setFont(QFont("Arial", 10))
        painter.setPen(ink2)
        painter.drawText(int(P['x1']) - 300, 6, 300, 20, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
                         "    ".join(parts_txt))