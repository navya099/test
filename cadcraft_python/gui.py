# test_gui.py
import math
import sys

from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPen, QColor, QBrush, QPainter
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout

from alignment import build_alignment
from alignment_props_ui import AlignmentPropsDialog
from project import Project
from plan_view import PlanViewWidget
from scene import plan_scene
from staking_ui import StakingDialog


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

        # DXF 내보내기 버튼 추가
        self.btn_export_dxf = QPushButton("DXF 내보내기")
        self.btn_export_dxf.clicked.connect(lambda: self.export_alignment_to_dxf())
        toolbar_layout.addWidget(self.btn_export_dxf)

        self.btn_staking = QPushButton("측량 보고서 (Staking)")  # [추가됨]
        self.btn_staking.clicked.connect(self.on_staking_clicked)
        toolbar_layout.addWidget(self.btn_staking)

        self.btn_al_props = QPushButton("선형 속성 (Properties)")  # [추가됨]
        self.btn_al_props.clicked.connect(self.on_alignment_props_clicked)
        toolbar_layout.addWidget(self.btn_al_props)

        layout.addLayout(toolbar_layout)

        # 3. 평면도 뷰어 위젯 생성 (scene_provider 콜백 연결)
        self.plan_view = PlanViewWidget(scene_provider=self.get_scene)
        layout.addWidget(self.plan_view)

        # 초기 화면 범위를 포인트 위치에 맞춤
        self.on_fit_clicked()

        # 완화곡선과 원곡선이 정상적으로 안착하는 넉넉한 간격의 PI 데이터
        self.alignment_pis = [
            {'x': 0.0, 'y': 0.0, 'r': 0.0, 'ls': 0.0},
            {'x': 1000.0, 'y': 0.0, 'r': 300.0, 'ls': 80.0},  # 첫 번째 완화곡선 (Ls=80, R=300)
            {'x': 1500.0, 'y': 1000.0, 'r': 400.0, 'ls': 100.0},  # 두 번째 완화곡선 (Ls=100, R=400)
            {'x': 2500.0, 'y': 1000.0, 'r': 0.0, 'ls': 0.0}
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

            if hasattr(self.project, 'edit_points'):
                self.project.edit_points("포인트 추가", lambda pts, s: new_pts)
            else:
                self.project.points = new_pts

            self.plan_view.update()
        except Exception as e:
            print(f"[크래시 방지 예외 포착]: {e}")

    def draw_custom_overlay(self, painter: QPainter, view):
        """선형 폴리라인, 스테이션 눈금(Ticks), 주요 제원 마커, PI 그립을 오버레이에 렌더링"""
        painter.save()

        # 1. alignment 엔진으로 선형 계산
        alignment = build_alignment(self.alignment_pis)
        if alignment.ok:
            # A. 선형 폴리라인 렌더링
            poly_pts = alignment.polyline(max_seg=1.0)
            if len(poly_pts) >= 2:
                painter.setPen(QPen(QColor('#1e48c8'), 2.5))
                painter.setBrush(Qt.BrushStyle.NoBrush)

                from PyQt6.QtGui import QPainterPath
                path = QPainterPath()
                first_sp = view.to_screen(poly_pts[0]['x'], poly_pts[0]['y'])
                path.moveTo(first_sp.x(), first_sp.y())

                for p in poly_pts[1:]:
                    sp = view.to_screen(p['x'], p['y'])
                    path.lineTo(sp.x(), sp.y())

                painter.drawPath(path)

            # B. 스테이션 틱(Ticks) 및 눈금 라벨 렌더링 (예: 20미터 간격)
            tick_step = 20.0
            ticks = alignment.ticks(step=tick_step)
            for t in ticks:
                sta = t['sta']
                x, y, dir_val = t['x'], t['y'], t['dir']

                # 선형 진행 방향의 수직 법선 벡터 (좌측 방향 기준)
                nx = -math.sin(dir_val)
                ny = math.cos(dir_val)
                tick_len = 3.0  # 눈금 길이 (월드 단위, 미터)

                p_inner = view.to_screen(x, y)
                p_outer = view.to_screen(x + nx * tick_len, y + ny * tick_len)

                # 눈금선 그리기
                painter.setPen(QPen(QColor('#555555'), 1.0))
                painter.drawLine(p_inner, p_outer)

                # 100미터 단위(메이저 스테이션)마다 번호 텍스트 표시
                if abs(sta % 100) < 1e-5:
                    label_pt = view.to_screen(x + nx * (tick_len + 4.0), y + ny * (tick_len + 4.0))
                    painter.setPen(QPen(QColor('#222222'), 1.0))

                    km = int(sta // 1000)
                    m = int(sta % 1000)
                    sta_str = f"{km}+{m:03d}"

                    painter.drawText(label_pt, sta_str)

            # C. 주요 제원 포인트 (Start, TS, SC, CS, ST, End 등) 마커 렌더링
            key_stas = alignment.key_stations()
            for ks in key_stas:
                sta = ks['sta']
                kind = ks['kind']
                p = alignment.point_at(sta)
                if p:
                    sp = view.to_screen(p['x'], p['y'])

                    painter.setPen(QPen(QColor('#b3122e'), 1.5))
                    painter.setBrush(QBrush(QColor('#ffffff')))
                    painter.drawEllipse(sp, 3.5, 3.5)

                    km = int(sta // 1000)
                    m = int(sta % 1000)
                    sta_fmt = f"{km}+{m:03d}"

                    painter.setPen(QPen(QColor('#b3122e'), 1.0))
                    painter.drawText(QPointF(sp.x() + 6, sp.y() + 4), f"{kind} ({sta_fmt})")

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
        pos = event.position()
        if event.button() == Qt.MouseButton.LeftButton:
            for i, pi in enumerate(self.alignment_pis):
                sp = self.plan_view.to_screen(pi['x'], pi['y'])
                dist = math.hypot(sp.x() - pos.x(), sp.y() - pos.y())
                if dist <= 10.0:
                    self.dragging_pi_index = i
                    return

        if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton):
            self.plan_view._is_panning = True
            self.plan_view._last_mouse_pos = pos
            self.plan_view.setCursor(Qt.CursorShape.ClosedHandCursor)

    def custom_mouse_move(self, event):
        pos = event.position()
        w_pos = self.plan_view.to_world(pos.x(), pos.y())

        if self.dragging_pi_index is not None:
            pi = self.alignment_pis[self.dragging_pi_index]
            pi['x'] = w_pos['x']
            pi['y'] = w_pos['y']
            self.plan_view.update()
            return

        if getattr(self.plan_view, '_is_panning', False):
            dx = pos.x() - self.plan_view._last_mouse_pos.x()
            dy = pos.y() - self.plan_view._last_mouse_pos.y()
            self.plan_view.pan_by(dx, dy)
            self.plan_view._last_mouse_pos = pos

    def custom_mouse_release(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.dragging_pi_index is not None:
            self.dragging_pi_index = None

        if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton):
            self.plan_view._is_panning = False
            self.plan_view.setCursor(Qt.CursorShape.ArrowCursor)

    def export_alignment_to_dxf(self, filepath="c:/temp/test_spiral_civilcraft.dxf"):
        """현재 선형(폴리라인, 스테이션 틱, 제원 텍스트)을 모두 포함하여 DXF 파일로 내보내기"""
        import os
        alignment = build_alignment(self.alignment_pis)
        if not alignment.ok:
            print(f"DXF 내보내기 실패: 선형 에러 발생 ({alignment.errors})")
            return

        poly_pts = alignment.polyline(max_seg=1.0)
        if not poly_pts:
            print("DXF 내보내기 실패: 샘플링 포인트가 없습니다.")
            return

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            # 1. DXF 헤더 및 테이블 섹션
            f.write("0\nSECTION\n2\nHEADER\n0\nENDSEC\n")
            f.write("0\nSECTION\n2\nTABLES\n0\nENDSEC\n")
            f.write("0\nSECTION\n2\nENTITIES\n")

            # 2. 도로 중심선 LWPOLYLINE 엔티티 추가
            f.write("0\nLWPOLYLINE\n")
            f.write("8\nC-ROAD-CNTR\n")       # 레이어
            f.write(f"90\n{len(poly_pts)}\n") # 정점 개수
            f.write("70\n0\n")                # 열린 폴리라인
            for p in poly_pts:
                f.write(f"10\n{p['x']}\n")
                f.write(f"20\n{p['y']}\n")

            # 3. 스테이션 틱(Tick) LINE 엔티티들 추가 (20m 간격)
            tick_step = 20.0
            ticks = alignment.ticks(step=tick_step)
            for t in ticks:
                sta = t['sta']
                x, y, dir_val = t['x'], t['y'], t['dir']
                nx = -math.sin(dir_val)
                ny = math.cos(dir_val)
                tick_len = 3.0

                x_out = x + nx * tick_len
                y_out = y + ny * tick_len

                f.write("0\nLINE\n")
                f.write("8\nC-ROAD-TICK\n")
                f.write(f"10\n{x}\n")
                f.write(f"20\n{y}\n")
                f.write(f"30\n0.0\n")
                f.write(f"11\n{x_out}\n")
                f.write(f"21\n{y_out}\n")
                f.write(f"31\n0.0\n")

                # 100m 주기의 메이저 스테이션 텍스트 (TEXT 엔티티)
                if abs(sta % 100) < 1e-5:
                    tx = x + nx * (tick_len + 4.0)
                    ty = y + ny * (tick_len + 4.0)
                    km = int(sta // 1000)
                    m = int(sta % 1000)
                    sta_str = f"{km}+{m:03d}"

                    f.write("0\nTEXT\n")
                    f.write("8\nC-ROAD-TEXT\n")
                    f.write(f"10\n{tx}\n")
                    f.write(f"20\n{ty}\n")
                    f.write(f"30\n0.0\n")
                    f.write("40\n3.0\n")  # 텍스트 높이
                    f.write(f"1\n{sta_str}\n")

            # 4. 주요 제원 포인트 마커 및 텍스트 (TS, SC, CS, ST 등) 추가
            key_stas = alignment.key_stations()
            for ks in key_stas:
                sta = ks['sta']
                kind = ks['kind']
                p = alignment.point_at(sta)
                if p:
                    km = int(sta // 1000)
                    m = int(sta % 1000)
                    sta_fmt = f"{km}+{m:03d}"
                    label_text = f"{kind} ({sta_fmt})"

                    f.write("0\nTEXT\n")
                    f.write("8\nC-ROAD-KEY\n")
                    f.write(f"10\n{p['x'] + 4.0}\n")
                    f.write(f"20\n{p['y'] + 4.0}\n")
                    f.write(f"30\n0.0\n")
                    f.write("40\n3.5\n")
                    f.write(f"1\n{label_text}\n")

            f.write("0\nENDSEC\n0\nEOF\n")

        print(f"DXF 파일 저장 성공 (틱 및 텍스트 포함): {filepath}")

    def on_staking_clicked(self):
        """측량 말뚝박기(Staking) 보고서 다이얼로그 호출"""
        # StakingDialog가 project.alignment(id)를 호출하므로,
        # 프로젝트 객체에 현재 선형을 반환하는 메서드 동적 바인딩
        if not hasattr(self.project, 'alignment'):
            self.project.alignment = lambda alignment_id: build_alignment(self.alignment_pis)

        # 단위 설정 ('m' 또는 'ft')
        ctx = {
            'project': self.project,
            'units': 'm'  # 미터법 기준 (필요시 동적 변경 가능)
        }

        # StakingDialog 팝업 실행
        dialog = StakingDialog(alignment_id=0, ctx=ctx, parent=self)
        dialog.exec()

    def on_alignment_props_clicked(self):
        """선형 제원 및 PVI 편집 다이얼로그 호출"""
        # 다이얼로그에 전달할 선형 데이터 묶음
        al_data = {
            'id': 0,
            'name': getattr(self, 'alignment_name', 'Main Alignment'),
            'start': 0.0,
            'min_r': 0.0,
            'pis': self.alignment_pis  # 메인 뷰어의 PI 리스트 참조 공유
        }

        ctx = {
            'project': self.project,
            'units': 'm'  # 미터법 기준 (필요시 동적 연동)
        }

        # AlignmentPropsDialog 팝업 실행
        dialog = AlignmentPropsDialog(al_data, ctx, parent=self)

        # 다이얼로그가 닫힐 때 변경된 데이터 반영 및 뷰 갱신
        if dialog.exec():
            # 이름이나 PI 정보가 변경되었을 경우 동기화
            if 'name' in al_data:
                self.alignment_name = al_data['name']
            self.alignment_pis = al_data['pis']

            # 메인 뷰어 화면 다시 그리기
            self.update()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TestMainWindow()
    window.show()
    sys.exit(app.exec())