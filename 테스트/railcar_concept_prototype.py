"""
철도차량 디자인 콘셉트용 3D 파라메트릭 통합 프로토타입 (Windows / Python)

필수 패키지 설치 (Windows PowerShell / CMD):
    pip install PySide6 pyvista pyvistaqt numpy

실행 방법:
    python railcar_concept_prototype.py
"""

import sys
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QRadioButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


# =============================================================================
# 1. 지오메트리 생성 엔진 (외형 Loft 곡면 + 실내 좌석 자동 배열)
# =============================================================================
def build_carbody_exterior_mesh(
    total_length: float,
    cab_length: float,
    width: float,
    floor_z: float,
    cant_z: float,
    roof_crown: float,
    nose_exp: float,
    nx_cab: int = 24,
    nx_body: int = 20,
    nu: int = 32,
) -> pv.StructuredGrid:
    """
    객실부(일정 단면) + 선두부(정면 방향 수렴 Loft)의 외피 곡면을
    단일 StructuredGrid로 생성한다.
    """
    body_length = max(total_length - cab_length, 2000.0)

    # X 좌표 분포: [0 .. body_length] 객실부, [body_length .. total_length] 선두부
    x_body = np.linspace(0.0, body_length, nx_body, endpoint=False)
    x_cab = np.linspace(body_length, total_length, nx_cab)
    x_stations = np.concatenate([x_body, x_cab])

    # 둘레 파라미터 u in [0, 1]: 하단 우측 -> 측벽 -> 지붕 -> 좌측 측벽 -> 하단 좌측
    # 단면을 폐곡선 형태로 표현하기 위해 각도 theta in [-pi*0.75, +pi*0.75] 매핑
    u = np.linspace(-1.0, 1.0, nu)  # -1: 좌측 하부, 0: 지붕 중앙, +1: 우측 하부

    nx = len(x_stations)
    X = np.zeros((nx, nu), dtype=float)
    Y = np.zeros((nx, nu), dtype=float)
    Z = np.zeros((nx, nu), dtype=float)

    half_w = width / 2.0

    for i, x_val in enumerate(x_stations):
        if x_val <= body_length:
            t = 0.0
        else:
            t = (x_val - body_length) / cab_length  # 0.0 -> 1.0 (선두 끝단)

        # 정면 방향 수렴 곡률 (nose_exp가 클수록 끝단이 둥글게 유지되다 급격히 좁아짐)
        w_scale = max(1.0 - (t ** nose_exp), 0.10)
        h_scale = 1.0 - 0.52 * (t ** (nose_exp + 0.25))

        curr_half_w = half_w * w_scale
        curr_cant_z = floor_z + (cant_z - floor_z) * h_scale
        curr_crown = roof_crown * (1.0 - 0.65 * t)

        # 단면 둘레 좌표 (Y, Z) 계산: |u| <= 0.45는 지붕 아치, 그 외는 측벽
        y_row = np.zeros(nu)
        z_row = np.zeros(nu)

        for j, u_val in enumerate(u):
            abs_u = abs(u_val)
            sign_u = 1.0 if u_val >= 0 else -1.0

            if abs_u <= 0.45:
                # 상부 지붕 곡면 (포물선 크라운)
                frac = u_val / 0.45  # -1 ~ +1
                y_row[j] = frac * (curr_half_w * 0.88)
                z_row[j] = curr_cant_z + curr_crown * (1.0 - frac ** 2)
            elif abs_u <= 0.85:
                # 측벽 (캔트레일 -> 하부 스커트 상단, 미세한 텀블홈 반영)
                wall_frac = (abs_u - 0.45) / 0.40  # 0(상단) -> 1(하단)
                y_top = curr_half_w * 0.88
                y_mid = curr_half_w
                # 허리 부근에서 최대폭, 하부로 갈수록 약간 안쪽으로 들어감
                y_row[j] = sign_u * (y_top + (y_mid - y_top) * np.sin(wall_frac * np.pi * 0.65))
                z_row[j] = curr_cant_z - wall_frac * (curr_cant_z - (floor_z + 180.0))
            else:
                # 하부 스커트 마감
                skirt_frac = (abs_u - 0.85) / 0.15
                y_row[j] = sign_u * curr_half_w * (1.0 - 0.12 * skirt_frac)
                z_row[j] = (floor_z + 180.0) - 180.0 * skirt_frac

        X[i, :] = x_val
        Y[i, :] = y_row
        Z[i, :] = z_row

    return pv.StructuredGrid(X, Y, Z)


def build_floor_and_underframe_mesh(
    total_length: float,
    cab_length: float,
    width: float,
    floor_z: float,
) -> pv.PolyData:
    """객실 바닥판 + 심플 대차(Bogie) 매스 2기 생성"""
    body_len = max(total_length - cab_length, 2000.0)
    floor_box = pv.Box(
        bounds=(0.0, total_length - 300.0, -width * 0.44, width * 0.44, floor_z - 120.0, floor_z)
    )

    # 디자인 비례 확인용 대차 매스 (전위/후위 대차 중심)
    bogie_x_positions = [3200.0, max(body_len - 1800.0, 6500.0)]
    meshes = [floor_box]
    for bx in bogie_x_positions:
        bogie_frame = pv.Box(bounds=(bx - 1300.0, bx + 1300.0, -1050.0, 1050.0, 200.0, floor_z - 150.0))
        meshes.append(bogie_frame)
        for wx in (bx - 1050.0, bx + 1050.0):
            wheel_pair = pv.Cylinder(
                center=(wx, 0.0, 430.0), direction=(0.0, 1.0, 0.0), radius=430.0, height=1600.0
            )
            meshes.append(wheel_pair)

    combined = meshes[0]
    for m in meshes[1:]:
        combined = combined.merge(m)
    return combined


def build_interior_seats_mesh(
    total_length: float,
    cab_length: float,
    width: float,
    floor_z: float,
    seat_pitch: float,
) -> tuple[pv.PolyData, int]:
    """
    차체 길이, 폭, 출입문(2개소 가정) 위치에 맞춰 객실 좌석을 자동 배열한다.
    반환값: (병합된 좌석 PolyData, 배치된 총 좌석 블록 수)
    """
    body_len = max(total_length - cab_length, 2000.0)
    # 출입문 2개소 중심 위치 및 도어 포켓 여유 폭 (출입문 간섭 회피)
    door_centers = [body_len * 0.25, body_len * 0.75]
    door_clearance = 1500.0

    # 좌석 배치 가능 구간(Bay) 계산
    raw_zones = [
        (800.0, door_centers[0] - door_clearance / 2.0),
        (door_centers[0] + door_clearance / 2.0, door_centers[1] - door_clearance / 2.0),
        (door_centers[1] + door_clearance / 2.0, body_len - 800.0),
    ]

    # 차체 폭이 2900mm 이상이면 2+2(양측 2열), 미만이면 2+1 또는 1+1 형태로 폭 자동 조정
    aisle_half = 320.0
    seat_depth = max(min((width * 0.44 - aisle_half), 950.0), 480.0)
    y_left = -(aisle_half + seat_depth / 2.0)
    y_right = +(aisle_half + seat_depth / 2.0)

    seat_meshes = []
    seat_count = 0

    for z_start, z_end in raw_zones:
        usable_len = z_end - z_start
        if usable_len < 600.0:
            continue
        n_rows = int(usable_len // seat_pitch)
        if n_rows <= 0:
            continue
        start_offset = z_start + (usable_len - (n_rows - 1) * seat_pitch) / 2.0

        for r in range(n_rows):
            sx = start_offset + r * seat_pitch
            for sy in (y_left, y_right):
                # 좌판 + 등받이 심플 모듈
                cushion = pv.Box(
                    bounds=(
                        sx - 220.0, sx + 220.0,
                        sy - seat_depth / 2.0, sy + seat_depth / 2.0,
                        floor_z + 360.0, floor_z + 440.0,
                    )
                )
                backrest = pv.Box(
                    bounds=(
                        sx - 220.0, sx - 130.0,
                        sy - seat_depth / 2.0, sy + seat_depth / 2.0,
                        floor_z + 440.0, floor_z + 1080.0,
                    )
                )
                seat_meshes.append(cushion)
                seat_meshes.append(backrest)
                seat_count += 1

    # 운전실 콘솔 볼륨 추가 (선두부 진입 직전)
    cab_console = pv.Box(
        bounds=(
            body_len + 200.0, body_len + 950.0,
            -width * 0.25, width * 0.25,
            floor_z, floor_z + 900.0,
        )
    )
    seat_meshes.append(cab_console)

    if not seat_meshes:
        return pv.PolyData(), 0

    merged = seat_meshes[0]
    for m in seat_meshes[1:]:
        merged = merged.merge(m)
    return merged, seat_count


# =============================================================================
# 2. PySide6 + PyVistaQt 통합 메인 윈도우
# =============================================================================
class RailcarConceptWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("철도차량 디자인 콘셉트 3D 파라메트릭 스튜디오")
        self.resize(1380, 820)

        # 초기 디자인 파라미터 (mm)
        self.params = {
            "total_length": 20000.0,
            "cab_length": 4500.0,
            "width": 3120.0,
            "floor_z": 1100.0,
            "cant_z": 3150.0,
            "roof_crown": 580.0,   # 상부 곡면 높이
            "nose_exp": 1.6,       # 정면 방향 수렴 곡률 지수
            "seat_pitch": 920.0,   # 실내 좌석 피치
        }
        self.view_mode = "solid"   # solid | translucent | clip_x | clip_y

        self._init_ui()
        self._init_scene()
        self._update_all_geometry(reset_camera=True)

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # --- 좌측 제어 패널 ---
        left_panel = QWidget()
        left_panel.setFixedWidth(340)
        left_layout = QVBoxLayout(left_panel)

        # 1) 외형 곡면 파라미터 그룹
        grp_shape = QGroupBox("외형 곡면 · 치수 제어 (실시간)")
        form_shape = QFormLayout(grp_shape)

        self.lbl_roof, sld_roof = self._create_slider(150, 950, int(self.params["roof_crown"]), "mm")
        sld_roof.valueChanged.connect(lambda v: self._on_param_change("roof_crown", float(v), self.lbl_roof, "mm"))
        form_shape.addRow("상부 지붕 곡률:", self._wrap_slider(sld_roof, self.lbl_roof))

        self.lbl_nose, sld_nose = self._create_slider(8, 35, int(self.params["nose_exp"] * 10), "")
        sld_nose.valueChanged.connect(
            lambda v: self._on_param_change("nose_exp", v / 10.0, self.lbl_nose, "", scale=0.1)
        )
        form_shape.addRow("정면 노즈 곡률:", self._wrap_slider(sld_nose, self.lbl_nose))

        self.lbl_cab, sld_cab = self._create_slider(2500, 7000, int(self.params["cab_length"]), "mm")
        sld_cab.valueChanged.connect(lambda v: self._on_param_change("cab_length", float(v), self.lbl_cab, "mm"))
        form_shape.addRow("선두부 길이:", self._wrap_slider(sld_cab, self.lbl_cab))

        self.lbl_width, sld_width = self._create_slider(2600, 3400, int(self.params["width"]), "mm")
        sld_width.valueChanged.connect(lambda v: self._on_param_change("width", float(v), self.lbl_width, "mm"))
        form_shape.addRow("차체 폭:", self._wrap_slider(sld_width, self.lbl_width))

        self.lbl_len, sld_len = self._create_slider(15000, 25000, int(self.params["total_length"]), "mm")
        sld_len.valueChanged.connect(lambda v: self._on_param_change("total_length", float(v), self.lbl_len, "mm"))
        form_shape.addRow("차량 전장:", self._wrap_slider(sld_len, self.lbl_len))

        # 2) 실내 배치 파라미터 그룹
        grp_interior = QGroupBox("실내 좌석 자동 배열")
        form_int = QFormLayout(grp_interior)

        spin_pitch = QDoubleSpinBox()
        spin_pitch.setRange(750.0, 1200.0)
        spin_pitch.setSingleStep(20.0)
        spin_pitch.setSuffix(" mm")
        spin_pitch.setValue(self.params["seat_pitch"])
        spin_pitch.valueChanged.connect(lambda v: self._on_param_change("seat_pitch", float(v)))
        form_int.addRow("좌석 피치:", spin_pitch)

        self.lbl_seat_count = QLabel("배치 좌석: - 석")
        form_int.addRow("배치 결과:", self.lbl_seat_count)

        # 3) 외벽 표시 / 단면 컷 토글 그룹
        grp_view = QGroupBox("외벽 투시 및 단면 컷 모드")
        vlay_view = QVBoxLayout(grp_view)
        self.view_btn_group = QButtonGroup(self)

        modes = [
            ("solid", "외형 보기 (불투명)"),
            ("translucent", "투시 보기 (외벽 반투명)"),
            ("clip_y", "종단면 컷 (Y=0 절반 절단)"),
            ("clip_x", "횡단면 컷 (차체 중앙 절단)"),
        ]
        for idx, (mode_key, mode_label) in enumerate(modes):
            rb = QRadioButton(mode_label)
            if idx == 0:
                rb.setChecked(True)
            rb.toggled.connect(lambda checked, m=mode_key: checked and self._on_view_mode_change(m))
            self.view_btn_group.addButton(rb)
            vlay_view.addWidget(rb)

        left_layout.addWidget(grp_shape)
        left_layout.addWidget(grp_interior)
        left_layout.addWidget(grp_view)
        left_layout.addStretch()

        # --- 우측 PyVistaQt 3D 뷰포트 ---
        self.plotter = QtInteractor(self)
        main_layout.addWidget(left_panel)
        main_layout.addWidget(self.plotter.interactor, 1)

    def _create_slider(self, min_v: int, max_v: int, init_v: int, unit: str):
        lbl = QLabel(f"{init_v}{unit}")
        lbl.setFixedWidth(60)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        sld = QSlider(Qt.Horizontal)
        sld.setRange(min_v, max_v)
        sld.setValue(init_v)
        return lbl, sld

    def _wrap_slider(self, slider: QSlider, label: QLabel) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(slider, 1)
        h.addWidget(label)
        return w

    def _init_scene(self):
        self.plotter.set_background("#1e222a", top="#2d333f")
        self.plotter.add_axes()

    def _on_param_change(self, key: str, value: float, label: QLabel | None = None, unit: str = "", scale: float = 1.0):
        self.params[key] = value
        if label is not None:
            disp = f"{value:.1f}" if scale != 1.0 else f"{int(value)}"
            label.setText(f"{disp}{unit}")
        self._update_all_geometry(reset_camera=False)

    def _on_view_mode_change(self, mode: str):
        self.view_mode = mode
        self._update_all_geometry(reset_camera=False)

    def _update_all_geometry(self, reset_camera: bool = False):
        p = self.params

        # 1) 외형 Loft 메쉬 생성
        ext_grid = build_carbody_exterior_mesh(
            total_length=p["total_length"],
            cab_length=p["cab_length"],
            width=p["width"],
            floor_z=p["floor_z"],
            cant_z=p["cant_z"],
            roof_crown=p["roof_crown"],
            nose_exp=p["nose_exp"],
        )
        ext_surf = ext_grid.extract_surface()

        # 보기 모드에 따른 외벽 투명도 및 단면 클리핑 적용
        opacity = 1.0
        if self.view_mode == "translucent":
            opacity = 0.28
        elif self.view_mode == "clip_y":
            ext_surf = ext_surf.clip(normal=(0, 1, 0), origin=(0, 0, 0), invert=True)
        elif self.view_mode == "clip_x":
            cut_x = (p["total_length"] - p["cab_length"]) * 0.55
            ext_surf = ext_surf.clip(normal=(1, 0, 0), origin=(cut_x, 0, 0), invert=True)

        self.plotter.add_mesh(
            ext_surf,
            name="carbody_exterior",
            color="#d9e2ec",
            metallic=0.35,
            roughness=0.4,
            opacity=opacity,
            smooth_shading=True,
            show_edges=False,
        )

        # 2) 바닥 및 대차 매스 갱신
        underframe = build_floor_and_underframe_mesh(
            total_length=p["total_length"],
            cab_length=p["cab_length"],
            width=p["width"],
            floor_z=p["floor_z"],
        )
        self.plotter.add_mesh(underframe, name="underframe_bogie", color="#485460", smooth_shading=False)

        # 3) 실내 좌석 자동 배열 갱신
        seats_mesh, seat_cnt = build_interior_seats_mesh(
            total_length=p["total_length"],
            cab_length=p["cab_length"],
            width=p["width"],
            floor_z=p["floor_z"],
            seat_pitch=p["seat_pitch"],
        )
        self.lbl_seat_count.setText(f"{seat_cnt} 석 (운전실 콘솔 포함)")
        if seats_mesh.n_points > 0:
            self.plotter.add_mesh(seats_mesh, name="interior_seats", color="#2b6cb0", smooth_shading=False)

        if reset_camera:
            self.plotter.view_isometric()
            self.plotter.reset_camera()
        else:
            self.plotter.render()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RailcarConceptWindow()
    window.show()
    sys.exit(app.exec())