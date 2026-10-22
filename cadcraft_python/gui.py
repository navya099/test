# test_gui.py
import math
import sys

from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPen, QColor, QBrush, QPainter
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout

from alignment import build_alignment
from project import Project
from plan_view import PlanViewWidget
from scene import plan_scene


class TestMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CivilCraft Python - Mini GUI Test")
        self.resize(1000, 700)

        # 1. 백엔드 브레인(Project) 초기화 및 테스트용 샘플 포인트 주입
        self.project = Project()
        self.project.set_points([
            {'n': 'P1', 'x': 0.0, 'y': 0.0, 'z': 10.0, 'd': '시작점'},
            {'n': 'P2', 'x': 50.0, 'y': 50.0, 'z': 15.0, 'd': '나무'},
            {'n': 'P3', 'x': 100.0, 'y': 0.0, 'z': 12.0, 'd': '건물코너'},
            {'n': 'P4', 'x': 50.0, 'y': -50.0, 'z': 8.0, 'd': '도로변'}
        ], 'sample_survey.csv')

        # 2. 메인 위젯 및 레이아웃 구성
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 상단 조작 툴바 (버튼들)
        toolbar_layout = QHBoxLayout()

        self.btn_fit = QPushButton("화면 맞춤 (Fit)")
        self.btn_fit.clicked.connect(self.on_fit_clicked)
        toolbar_layout.addWidget(self.btn_fit)

        self.btn_add_point = QPushButton("임의 포인트 추가 (Undo 테스트용)")
        self.btn_add_point.clicked.connect(self.on_add_point_clicked)
        toolbar_layout.addWidget(self.btn_add_point)

        layout.addLayout(toolbar_layout)

        # 3. 평면도 뷰어 위젯 생성 (scene_provider 콜백 연결)
        self.plan_view = PlanViewWidget(scene_provider=self.get_scene)
        layout.addWidget(self.plan_view)

        # 초기 화면 범위를 포인트 위치에 맞춤
        self.on_fit_clicked()

        # 1. 테스트용 간이 선형(Alignment) 데이터 추가 (PI 목록: x, y, radius)
        self.alignment_pis = [
            {'x': 0.0, 'y': 0.0, 'r': 30.0},
            {'x': 40.0, 'y': 60.0, 'r': 50.0},
            {'x': 100.0, 'y': 40.0, 'r': 0.0},
            {'x': 140.0, 'y': 100.0, 'r': 40.0}
        ]

        # 드래그 편집 상태 변수
        self.dragging_pi_index = None

        # 2. 평면 뷰어에 오버레이 렌더링 함수 등록
        self.plan_view.draw_overlay_fn = self.draw_custom_overlay

        # 3. 평면 뷰어의 마우스 이벤트 오버라이드 (그립 드래그용)
        self.plan_view.mousePressEvent = self.custom_mouse_press
        self.plan_view.mouseMoveEvent = self.custom_mouse_move
        self.plan_view.mouseReleaseEvent = self.custom_mouse_release

    def get_scene(self, mm_per_unit):
        state = self.project.state
        state['points'] = self.project.points

        # 1. alignment.py 엔진으로 선형 객체 빌드
        alignment = build_alignment(self.alignment_pis)

        alignment_items = []
        if alignment.ok:
            # 2. polyline()을 호출하여 곡선/직선이 부드럽게 이어진 샘플링 좌표 획득 (예: 1미터 간격)
            poly_pts = alignment.polyline(max_seg=1.0)
            if poly_pts:
                alignment_items.append({
                    'kind': 'poly',
                    'layer': 'C-ROAD-CNTR',  # 도로 중심선 레이어 토큰
                    'pts': [{'x': p['x'], 'y': p['y']} for p in poly_pts],
                    'closed': False,
                    'dashed': False
                })
        else:
            # 선형 에러가 있을 경우 콘솔에 출력
            print(f"선형 에러 발생: {alignment.errors}")

        # 3. 씬 아이템에 선형 병합
        state['items'] = state.get('items', []) + alignment_items
        return plan_scene(state, {'mmPerUnit': mm_per_unit})

    def on_fit_clicked(self):
        pts = self.project.points
        if not pts:
            return
        xs = [p['x'] for p in pts]
        ys = [p['y'] for p in pts]
        margin = 30
        bounds = {
            'minX': min(xs) - margin,
            'minY': min(ys) - margin,
            'maxX': max(xs) + margin,
            'maxY': max(ys) + margin
        }
        self.plan_view.fit_bounds(bounds)

    def on_add_point_clicked(self):
        """버튼을 누를 때마다 새로운 포인트를 추가하고 화면 갱신"""
        import random
        try:
            # 1. 기존 포인트 복사 후 새 포인트 생성
            current_pts = getattr(self.project, 'points', [])
            new_pts = [p.copy() for p in current_pts]
            idx = len(new_pts) + 1

            new_point = {
                'n': f'P{idx}',
                'x': float(random.uniform(-20, 120)),
                'y': float(random.uniform(-60, 60)),
                'z': float(random.uniform(5, 20)),
                'd': '추가됨'
            }
            new_pts.append(new_point)

            print(f"포인트 추가 시도: {new_point}")

            # 2. Project 에디트 메서드 호출 (만약 이 메서드 내부 구현에 문제가 있다면 확인 필요)
            if hasattr(self.project, 'edit_points'):
                self.project.edit_points("포인트 추가", lambda pts, s: new_pts)
            else:
                # edit_points가 없다면 직접 할당
                self.project.points = new_pts

            # 3. 씬 재생성 및 화면 갱신 테스트
            print("화면 갱신(update) 호출 중...")
            self.plan_view.update()
            print("화면 갱신 완료!")

        except Exception as e:
            print(f"[크래시 방지 예외 포착]: {e}")

    def draw_custom_overlay(self, painter: QPainter, view):
        """선형 계산 결과(폴리라인)와 PI 점(그립 핸들)을 오버레이에 직접 렌더링"""
        painter.save()

        # 1. alignment 엔진으로 선형 계산
        alignment = build_alignment(self.alignment_pis)
        if alignment.ok:
            poly_pts = alignment.polyline(max_seg=1.0)
            if len(poly_pts) >= 2:
                # 도로 중심선 스타일 (파란색 실선)
                painter.setPen(QPen(QColor('#1e48c8'), 2.5))
                painter.setBrush(Qt.BrushStyle.NoBrush)

                # 월드 좌표를 스크린 좌표로 변환하여 선 그리기
                from PyQt6.QtGui import QPainterPath
                path = QPainterPath()
                first_sp = view.to_screen(poly_pts[0]['x'], poly_pts[0]['y'])
                path.moveTo(first_sp.x(), first_sp.y())

                for p in poly_pts[1:]:
                    sp = view.to_screen(p['x'], p['y'])
                    path.lineTo(sp.x(), sp.y())

                painter.drawPath(path)
        else:
            # 에러가 있다면 콘솔에 출력
            # print(f"선형 에러: {alignment.errors}")
            pass

        # 2. 각 PI 위치에 빨간색/파란색 그립 사각형 표시
        for i, pi in enumerate(self.alignment_pis):
            sp = view.to_screen(pi['x'], pi['y'])

            is_selected = (i == self.dragging_pi_index)
            color = QColor('#1e48c8') if is_selected else QColor('#b3122e')

            painter.setPen(QPen(Qt.GlobalColor.white, 1.5))
            painter.setBrush(QBrush(color))

            rect = QRectF(sp.x() - 4, sp.y() - 4, 8, 8)
            painter.drawRect(rect)

            painter.setPen(color)
            painter.drawText(QPointF(sp.x() + 8, sp.y() - 4), f"PI{i + 1} (R={pi.get('r', 0)})")

        painter.restore()

    def custom_mouse_press(self, event):
        """마우스 클릭 시 PI 그립을 선택했는지 확인"""
        pos = event.position()
        w_pos = self.plan_view.to_world(pos.x(), pos.y())

        # 왼쪽 클릭일 때만 그립 선택 검사
        if event.button() == Qt.MouseButton.LeftButton:
            # 화면 픽셀 기준으로 약 10픽셀 이내에 있는 PI를 찾음
            for i, pi in enumerate(self.alignment_pis):
                sp = self.plan_view.to_screen(pi['x'], pi['y'])
                dist = math.hypot(sp.x() - pos.x(), sp.y() - pos.y())
                if dist <= 10.0:  # 10px 반경 내 클릭 시 선택
                    self.dragging_pi_index = i
                    return

        # 기본 패닝(우클릭/휠클릭) 처리 위임
        if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton):
            self.plan_view._is_panning = True
            self.plan_view._last_mouse_pos = pos
            self.plan_view.setCursor(Qt.CursorShape.ClosedHandCursor)

    def custom_mouse_move(self, event):
        """마우스 드래그 시 선택된 PI 좌표를 실시간으로 업데이트"""
        pos = event.position()
        w_pos = self.plan_view.to_world(pos.x(), pos.y())

        # 1. PI를 드래그 중인 경우
        if self.dragging_pi_index is not None:
            pi = self.alignment_pis[self.dragging_pi_index]
            pi['x'] = w_pos['x']
            pi['y'] = w_pos['y']
            self.plan_view.update()  # 화면 실시간 갱신!
            return

        # 2. 일반 패닝 중인 경우
        if getattr(self.plan_view, '_is_panning', False):
            dx = pos.x() - self.plan_view._last_mouse_pos.x()
            dy = pos.y() - self.plan_view._last_mouse_pos.y()
            self.plan_view.pan_by(dx, dy)
            self.plan_view._last_mouse_pos = pos

    def custom_mouse_release(self, event):
        """마우스 버튼 뗄 때 드래그 종료"""
        if event.button() == Qt.MouseButton.LeftButton and self.dragging_pi_index is not None:
            self.dragging_pi_index = None
            # 필요시 여기서 project.py의 undo 스택에 변경 사항 기록 가능!

        if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton):
            self.plan_view._is_panning = False
            self.plan_view.setCursor(Qt.CursorShape.ArrowCursor)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TestMainWindow()
    window.show()
    sys.exit(app.exec())