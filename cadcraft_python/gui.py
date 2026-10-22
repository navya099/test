# test_gui.py
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
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

    def get_scene(self, mm_per_unit):
        """Project 상태와 포인트 데이터를 받아 PlanView에 전달할 씬(Scene) 생성"""
        state = self.project.state
        state['points'] = self.project.points
        return plan_scene(state, {'mmPerUnit': mm_per_unit})

    def on_fit_clicked(items):
        """포인트 위치를 기준으로 화면 배율과 중심 맞춤"""
        pass  # 아래 실제 메서드로 구현됨

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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TestMainWindow()
    window.show()
    sys.exit(app.exec())