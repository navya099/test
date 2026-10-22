# plan_view.py
import math
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QFontMetrics, QPainterPath, QTransform
from PyQt6.QtWidgets import QWidget

PX_PER_MM = 96.0 / 25.4
LABEL_FONT_FAMILY = 'Helvetica, Arial, sans-serif'

WIDTHS = {
    'C-TOPO-MAJR': 1.5, 'C-TOPO-MINR': 0.75, 'C-TOPO-TINN': 0.6, 'C-TOPO-BRKL': 1.4,
    'C-TOPO-BNDY': 1.2, 'C-TOPO-SLOP': 1.0, 'C-ROAD-CNTR': 2.2, 'C-ROAD-STAN': 1.2,
    'C-ROAD-CORR': 1.4, 'C-GRAD-PADS': 2.0, 'C-GRAD-DAYL': 1.6, 'C-GRAD-SLOP': 0.6,
    'C-STRM-PIPE': 2.4, 'C-STRM-STRC': 1.6, 'C-STRM-PROB': 2.8
}

COLOR_TOKENS = {
    'bg': '#f3f6f8', 'ink': '#17202b', 'ink2': '#34404e', 'grid': '#d5dde5', 'line': '#7a8796',
    'action': '#1e48c8', 'red': '#b3122e', 'orange': '#a84a00', 'green': '#17703a',
    'blue': '#1e48c8', 'magenta': '#9a1f86', 'cyan': '#00707e', 'ochre': '#8a6200'
}

def mix_color(c1_hex, c2_hex, ratio):
    """두 Hex 색상을 비율에 따라 혼합"""
    q1 = QColor(c1_hex)
    q2 = QColor(c2_hex)
    r = int(q1.red() * (1 - ratio) + q2.red() * ratio)
    g = int(q1.green() * (1 - ratio) + q2.green() * ratio)
    b = int(q1.blue() * (1 - ratio) + q2.blue() * ratio)
    return QColor(r, g, b)

class PlanViewWidget(QWidget):
    """
    PyQt6 기반 평면도 뷰포트 위젯 (view.js 1:1 포팅)
    """
    cursor_moved = pyqtSignal(float, float)  # 마우스 월드 좌표 변경 시그널

    def __init__(self, scene_provider, parent=None):
        super().__init__(parent)
        self.scene_provider = scene_provider  # scene(mm_per_unit) 콜백
        
        # 카메라 및 뷰포트 상태 변수
        self.cx = 0.0
        self.cy = 0.0
        self.zoom = 1.0
        self.origin = {'x': 0.0, 'y': 0.0}
        
        # 인터랙션 상태
        self._is_panning = False
        self._last_mouse_pos = QPointF()
        
        # 오버레이 드로잉 콜백 (외부에서 저장)
        self.draw_overlay_fn = None
        
        # 색상 및 테마 설정
        self.colors = {k: QColor(v) for k, v in COLOR_TOKENS.items()}
        self.colors['major'] = self.colors['ink']
        self.colors['minor'] = mix_color(COLOR_TOKENS['ink'], COLOR_TOKENS['bg'], 0.5)
        self.colors['tin'] = mix_color(COLOR_TOKENS['line'], COLOR_TOKENS['bg'], 0.35)
        
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    # ---- 좌표 변환 메커니즘 (World <-> Screen) ----
    def to_screen(self, x, y):
        """월드 좌표(x, y) -> 스크린 피셀 좌표(sx, sy)"""
        sw = self.width()
        sh = self.height()
        sx = (x - self.cx) * self.zoom + sw / 2.0
        sy = sh / 2.0 - (y - self.cy) * self.zoom
        return QPointF(sx, sy)

    def to_world(self, sx, sy):
        """스크린 피셀 좌표(sx, sy) -> 월드 좌표(x, y)"""
        sw = self.width()
        sh = self.height()
        x = (sx - sw / 2.0) / self.zoom + self.cx
        y = (sh / 2.0 - sy) / self.zoom + self.cy
        return {'x': x, 'y': y}

    def zoom_at(self, sx, sy, factor):
        """특정 스크린 좌표(sx, sy)를 기준으로 줌 인/아웃"""
        before = self.to_world(sx, sy)
        self.zoom = min(1e6, max(1e-6, self.zoom * factor))
        after = self.to_world(sx, sy)
        self.cx += before['x'] - after['x']
        self.cy += before['y'] - after['y']
        self.update()

    def pan_by(self, dx, dy):
        """화면 평행 이동(Pan)"""
        self.cx -= dx / self.zoom
        self.cy += dy / self.zoom
        self.update()

    def fit_bounds(self, bounds):
        """지정한 바운딩 박스로 화면에 맞춤 (Fit)"""
        if not bounds or 'minX' not in bounds:
            self.zoom = 1.0
            self.update()
            return
        bw = max(bounds['maxX'] - bounds['minX'], 1e-6)
        bh = max(bounds['maxY'] - bounds['minY'], 1e-6)
        self.cx = (bounds['minX'] + bounds['maxX']) / 2.0
        self.cy = (bounds['minY'] + bounds['maxY']) / 2.0
        self.zoom = min(self.width() / bw, self.height() / bh) * 0.88
        self.update()

    def view_bounds(self):
        """현재 화면에 보이는 월드 영역 경계"""
        a = self.to_world(0, self.height())
        b = self.to_world(self.width(), 0)
        return {'minX': a['x'], 'minY': a['y'], 'maxX': b['x'], 'maxY': b['y']}

    def mm_bucket(self):
        """축척 기반 텍스트 크기 조절용 Bucket"""
        mm = self.zoom / PX_PER_MM
        return math.pow(2, round(math.log2(mm))) if mm > 0 else 1.0

    # ---- PyQt6 메인 렌더링 루프 ----
    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # 1. 배경 채우기
            painter.fillRect(self.rect(), self.colors['bg'])

            # 2. Scene 데이터 가져오기
            mm = self.mm_bucket()
            sc = self.scene_provider(mm) if self.scene_provider else None

            if sc:
                self._paint_base_scene(painter, sc)

            # 3. 오버레이
            if self.draw_overlay_fn:
                self.draw_overlay_fn(painter, self)

        except Exception as e:
            print(f"[렌더링 뷰 크래시 방지 에러 포착]: {e}")

    def _paint_base_scene(self, painter, sc):
        """도면 기하요소(선, 원호, 포인트, 텍스트) 그려주기"""
        layer_tokens = {l['name']: l['token'] for l in sc.get('layers', [])}
        ox, oy = self.origin['x'], self.origin['y']
        
        # 3-1. 월드 좌표계 변환 행렬 적용 (Y축 반전)
        painter.save()
        sw, sh = self.width(), self.height()
        
        transform = QTransform()
        transform.translate(sw / 2.0, sh / 2.0)
        transform.scale(self.zoom, -self.zoom)
        transform.translate(-(self.cx - ox), -(self.cy - oy))
        painter.setTransform(transform)
        
        # 선형/폴리라인 및 원호 그리기
        for it in sc.get('items', []):
            kind = it['kind']
            token = layer_tokens.get(it['layer'], 'ink')
            color = self.colors.get(token, self.colors['ink'])
            width = (WIDTHS.get(it['layer'], 1.0)) / self.zoom
            
            if kind == 'poly':
                pts = it['pts']
                if len(pts) >= 2:
                    path = QPainterPath()
                    path.moveTo(pts[0]['x'] - ox, pts[0]['y'] - oy)
                    for p in pts[1:]:
                        path.lineTo(p['x'] - ox, p['y'] - oy)
                    if it.get('closed'):
                        path.closePath()
                    
                    pen = QPen(color, width)
                    if it.get('dashed'):
                        pen.setStyle(Qt.PenStyle.DashLine)
                    painter.setPen(pen)
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawPath(path)
                    
            elif kind == 'arc':
                c, r = it['c'], it['r']
                a0, a1 = it['a0'], it['a1']
                path = QPainterPath()
                # QPainterPath arcTo (각도는 Degree 단위)
                rect = QRectF(c['x'] - ox - r, c['y'] - oy - r, 2 * r, 2 * r)
                start_angle_deg = math.degrees(a0)
                sweep_angle_deg = math.degrees(a1 - a0)
                path.addArc(rect, start_angle_deg, sweep_angle_deg)
                
                painter.setPen(QPen(color, width))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(path)

        painter.restore()  # 월드 변환 해제 (스크린 좌표계로 복귀)

        # 3-2. 텍스트 및 측량점 (스크린 공간 렌더링)
        vb = self.view_bounds()
        m = 40.0 / self.zoom
        
        def in_view(x, y):
            return (vb['minX'] - m <= x <= vb['maxX'] + m) and (vb['minY'] - m <= y <= vb['maxY'] + m)

        # 측량 포인트 십자가 표시
        painter.setPen(QPen(self.colors['green'], 1.2))
        for it in sc.get('items', []):
            if it['kind'] == 'point' and in_view(it['x'], it['y']):
                sp = self.to_screen(it['x'], it['y'])
                k = 2.5
                painter.drawLine(QPointF(sp.x() - k, sp.y() - k), QPointF(sp.x() + k, sp.y() + k))
                painter.drawLine(QPointF(sp.x() - k, sp.y() + k), QPointF(sp.x() + k, sp.y() - k))

        # 텍스트 라벨
        for it in sc.get('items', []):
            if it['kind'] == 'text' and in_view(it['x'], it['y']):
                sp = self.to_screen(it['x'], it['y'])
                fs = it['mm'] * PX_PER_MM / 0.72
                
                painter.save()
                painter.translate(sp.x(), sp.y())
                painter.rotate(-math.degrees(it.get('rot', 0)))
                
                font = QFont(LABEL_FONT_FAMILY, int(fs))
                font.setWeight(QFont.Weight.Bold)
                painter.setFont(font)
                
                token = layer_tokens.get(it['layer'], 'ink')
                painter.setPen(self.colors.get(token, self.colors['ink']))
                
                text_str = it['text']
                fm = QFontMetrics(font)
                tw = fm.horizontalAdvance(text_str)
                th = fm.height()
                
                tx = -tw / 2.0 if it.get('align') == 'center' else (-tw if it.get('align') == 'right' else 0)
                ty = th * 0.36 if it.get('middle') else 0
                
                # 마스크 배경 사각형
                if it.get('mask'):
                    painter.fillRect(QRectF(tx - 2, ty - th * 0.8, tw + 4, th * 0.95), self.colors['bg'])
                    
                painter.drawText(QPointF(tx, ty), text_str)
                painter.restore()

    # ---- 마우스 및 휠 이벤트 (Pan & Zoom 인터랙션) ----
    def mousePressEvent(self, event):
        if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton):
            self._is_panning = True
            self._last_mouse_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        pos = event.position()
        w_pos = self.to_world(pos.x(), pos.y())
        self.cursor_moved.emit(w_pos['x'], w_pos['y'])
        
        if self._is_panning:
            dx = pos.x() - self._last_mouse_pos.x()
            dy = pos.y() - self._last_mouse_pos.y()
            self.pan_by(dx, dy)
            self._last_mouse_pos = pos

    def mouseReleaseEvent(self, event):
        if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton):
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def wheelEvent(self, event):
        # 마우스 커서 위치 기준 Zoom In / Out
        factor = 1.15 if event.angleDelta().y() > 0 else (1.0 / 1.15)
        pos = event.position()
        self.zoom_at(pos.x(), pos.y(), factor)