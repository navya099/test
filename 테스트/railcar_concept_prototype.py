"""
철도차량 디자인 콘셉트용 3D 파라메트릭 통합 프로토타입 + 기본도 10장 DXF 내보내기 (Windows / Python)

필수 패키지 설치 (Windows PowerShell / CMD):
    pip install PySide6 pyvista pyvistaqt numpy ezdxf

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
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


# =============================================================================
# 1. 지오메트리 & 좌석 좌표 계산 엔진 (KTX/ITX 슈퍼엘립스 유선형 선두부)
# =============================================================================
def _superellipse_profile(t: float, exp_p: float, round_q: float = 2.4) -> float:
    """
    t=0 에서 기울기 0(차체와 매끄러운 C1 접합),
    t=1 에서 접선이 수직(뾰족하지 않고 둥근 반타원 노즈)이 되는 슈퍼엘립스 감쇠 함수.
    """
    t = min(max(t, 0.0), 1.0)
    val = max(1.0 - (t ** exp_p), 0.0)
    return float(val ** (1.0 / round_q))


def compute_seat_positions(
    total_length: float,
    cab_length: float,
    width: float,
    seat_pitch: float,
) -> tuple[list[tuple[float, float, float]], float]:
    """
    차체 치수와 출입문 간섭을 고려한 좌석 중심 좌표 (x, y, seat_depth) 목록을 계산한다.
    """
    body_len = max(total_length - cab_length, 2000.0)
    door_centers = [body_len * 0.25, body_len * 0.75]
    door_clearance = 1500.0

    raw_zones = [
        (800.0, door_centers[0] - door_clearance / 2.0),
        (door_centers[0] + door_clearance / 2.0, door_centers[1] - door_clearance / 2.0),
        (door_centers[1] + door_clearance / 2.0, body_len - 800.0),
    ]

    aisle_half = 320.0
    seat_depth = max(min((width * 0.44 - aisle_half), 950.0), 480.0)
    y_left = -(aisle_half + seat_depth / 2.0)
    y_right = +(aisle_half + seat_depth / 2.0)

    positions: list[tuple[float, float, float]] = []
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
            positions.append((sx, y_left, seat_depth))
            positions.append((sx, y_right, seat_depth))

    return positions, body_len


def compute_nose_profile_curves(
    total_length: float,
    cab_length: float,
    width: float,
    floor_z: float,
    cant_z: float,
    roof_crown: float,
    nose_exp: float,
    n_pts: int = 28,
) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
    """
    2D DXF 입면도/평면도용 KTX/ITX형 둥근 선두부 상부 루프 윤곽(X, Z)과 평면 폭 윤곽(X, Y)을 반환한다.
    """
    body_len = max(total_length - cab_length, 2000.0)
    half_w = width / 2.0
    bumper_z = floor_z + 120.0
    s_vals = np.linspace(0.0, 1.0, n_pts)
    t_vals = np.sin(s_vals * (np.pi / 2.0))

    side_roof_pts: list[tuple[float, float]] = []
    plan_half_pts: list[tuple[float, float]] = []

    for t in t_vals:
        x_val = body_len + t * cab_length
        w_scale = _superellipse_profile(t, exp_p=nose_exp, round_q=2.6)
        h_scale = _superellipse_profile(t, exp_p=max(nose_exp * 0.9, 1.1), round_q=2.2)

        top_z = bumper_z + (cant_z + roof_crown - bumper_z) * h_scale
        side_roof_pts.append((float(x_val), float(top_z)))
        plan_half_pts.append((float(x_val), float(half_w * w_scale)))

    return side_roof_pts, plan_half_pts


def build_carbody_exterior_mesh(
    total_length: float,
    cab_length: float,
    width: float,
    floor_z: float,
    cant_z: float,
    roof_crown: float,
    nose_exp: float,
    nx_cab: int = 32,
    nx_body: int = 16,
    nu: int = 36,
) -> pv.StructuredGrid:
    """
    KTX/ITX 스타일의 둥근 반타원 노즈와 수평 스커트 라인을 갖는 차체 외피 StructuredGrid 생성.
    하부 스커트가 바닥판 아래까지 내려와 감싸므로 정면 하단으로 내부가 노출되지 않는다.
    """
    body_length = max(total_length - cab_length, 2000.0)
    x_body = np.linspace(0.0, body_length, nx_body, endpoint=False)

    s_cab = np.linspace(0.0, 1.0, nx_cab)
    t_cab = np.sin(s_cab * (np.pi / 2.0))
    x_cab = body_length + t_cab * cab_length

    x_stations = np.concatenate([x_body, x_cab])
    u = np.linspace(-1.0, 1.0, nu)

    nx = len(x_stations)
    X = np.zeros((nx, nu), dtype=float)
    Y = np.zeros((nx, nu), dtype=float)
    Z = np.zeros((nx, nu), dtype=float)

    half_w = width / 2.0
    total_h = (cant_z + roof_crown) - floor_z
    bumper_z = floor_z + 100.0

    for i, x_val in enumerate(x_stations):
        t = 0.0 if x_val <= body_length else (x_val - body_length) / cab_length
        t = min(max(t, 0.0), 1.0)

        w_scale = _superellipse_profile(t, exp_p=nose_exp, round_q=2.6)
        h_scale = _superellipse_profile(t, exp_p=max(nose_exp * 0.9, 1.1), round_q=2.2)

        # 하부 스커트가 바닥판(floor_z - 120)까지 감싸도록 유지하며 끝단에서만 범퍼 높이로 마감
        curr_floor_z = (floor_z - 120.0) + (bumper_z - (floor_z - 120.0)) * (t ** 8.0)
        curr_top_z = bumper_z + (floor_z + total_h - bumper_z) * h_scale

        curr_h = max(curr_top_z - curr_floor_z, 0.0)
        crown_ratio = roof_crown / total_h
        curr_crown = curr_h * crown_ratio
        curr_cant_z = curr_top_z - curr_crown
        curr_half_w = half_w * w_scale

        y_row = np.zeros(nu)
        z_row = np.zeros(nu)

        for j, u_val in enumerate(u):
            abs_u = abs(u_val)
            sign_u = 1.0 if u_val >= 0 else -1.0

            if abs_u <= 0.45:
                frac = u_val / 0.45
                y_row[j] = frac * (curr_half_w * 0.88)
                z_row[j] = curr_cant_z + curr_crown * (1.0 - frac ** 2)
            elif abs_u <= 0.85:
                wall_frac = (abs_u - 0.45) / 0.40
                y_top = curr_half_w * 0.88
                y_mid = curr_half_w
                y_row[j] = sign_u * (y_top + (y_mid - y_top) * np.sin(wall_frac * np.pi * 0.65))
                skirt_top_z = curr_floor_z + min(220.0, curr_h * 0.18)
                z_row[j] = curr_cant_z - wall_frac * (curr_cant_z - skirt_top_z)
            else:
                skirt_frac = (abs_u - 0.85) / 0.15
                y_row[j] = sign_u * curr_half_w * (1.0 - 0.08 * skirt_frac)
                skirt_top_z = curr_floor_z + min(220.0, curr_h * 0.18)
                z_row[j] = skirt_top_z - (skirt_top_z - curr_floor_z) * skirt_frac

        X[i, :] = x_val
        Y[i, :] = y_row
        Z[i, :] = z_row

    return pv.StructuredGrid(X, Y, Z)


def build_floor_and_underframe_mesh(
    total_length: float,
    cab_length: float,
    width: float,
    floor_z: float,
    nose_exp: float,
) -> pv.PolyData:
    """선두부 내측에 완전히 수납되는 테이퍼형 객실 바닥판 + 디자인 비례용 대차 매스 2기 생성"""
    body_len = max(total_length - cab_length, 2000.0)

    _, plan_half_pts = compute_nose_profile_curves(
        total_length, cab_length, width, floor_z, 3150.0, 580.0, nose_exp, n_pts=18
    )
    scale_inner = 0.78
    half_inner = (width / 2.0) * scale_inner

    # 끝단 직전(마지막 2점 제외)까지만 바닥판 연장하여 외피 밖 돌출 방지
    taper_pts = [(x, y * scale_inner) for x, y in plan_half_pts[:-2]]
    poly_2d = (
        [(0.0, half_inner)]
        + taper_pts
        + [(x, -y) for x, y in reversed(taper_pts)]
        + [(0.0, -half_inner)]
    )
    pts_3d = np.array([[x, y, floor_z - 110.0] for x, y in poly_2d], dtype=float)
    faces = np.hstack([[len(pts_3d)], np.arange(len(pts_3d))])
    floor_poly = pv.PolyData(pts_3d, faces).triangulate().extrude((0.0, 0.0, 110.0), capping=True)

    bogie_x_positions = [3200.0, max(body_len - 1800.0, 6500.0)]
    meshes = [floor_poly]
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
    """compute_seat_positions() 좌표를 기반으로 3D 실내 좌석 및 운전실 콘솔 메쉬 생성"""
    positions, body_len = compute_seat_positions(total_length, cab_length, width, seat_pitch)

    seat_meshes = []
    for sx, sy, seat_depth in positions:
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

    console_len = min(cab_length * 0.22, 780.0)
    cab_console = pv.Box(
        bounds=(
            body_len + 150.0, body_len + 150.0 + console_len,
            -width * 0.20, width * 0.20,
            floor_z, floor_z + 750.0,
        )
    )
    seat_meshes.append(cab_console)

    if not seat_meshes:
        return pv.PolyData(), 0

    merged = seat_meshes[0]
    for m in seat_meshes[1:]:
        merged = merged.merge(m)
    return merged, len(positions)


# =============================================================================
# 2. 기본도 10장 (G-01 ~ G-10) ezdxf 내보내기 엔진
# =============================================================================
def export_10_basic_drawings_dxf(params: dict, output_path: str) -> None:
    """
    현재 UI 파라미터(외형 곡면 + 실내 좌석 배열)를 반영하여
    기본도면 10장(Paperspace 레이아웃 10개)이 담긴 DXF R2010 파일을 생성한다.
    """
    import ezdxf

    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()

    layer_defs = {
        "CAR_BODY": {"color": 7},
        "CAR_CENTER": {"color": 1, "linetype": "CENTER"},
        "BOGIE": {"color": 4},
        "INTERIOR": {"color": 3},
        "ROOF_EQUIP": {"color": 5},
        "UNDER_EQUIP": {"color": 30},
        "GAUGE_LIMIT": {"color": 6, "linetype": "DASHED"},
        "DIM": {"color": 2},
        "VIEWPORTS": {"color": 8},
    }
    for lname, lattrs in layer_defs.items():
        if lname not in doc.layers:
            doc.layers.add(lname, **lattrs)

    total_len = params["total_length"]
    cab_len = params["cab_length"]
    width = params["width"]
    floor_z = params["floor_z"]
    cant_z = params["cant_z"]
    roof_crown = params["roof_crown"]
    nose_exp = params["nose_exp"]
    seat_pitch = params["seat_pitch"]

    seat_positions, body_len = compute_seat_positions(total_len, cab_len, width, seat_pitch)
    side_roof_pts, plan_half_pts = compute_nose_profile_curves(
        total_len, cab_len, width, floor_z, cant_z, roof_crown, nose_exp
    )
    bogie_xs = [3200.0, max(body_len - 1800.0, 6500.0)]

    blk_side = doc.blocks.new(name="BLK_CAR_SIDE")
    side_outline = [(0.0, floor_z - 120.0), (0.0, cant_z + roof_crown)] + side_roof_pts + [
        (total_len, floor_z - 120.0),
    ]
    blk_side.add_lwpolyline(side_outline, close=True, dxfattribs={"layer": "CAR_BODY"})
    for dx in (body_len * 0.25, body_len * 0.75):
        blk_side.add_lwpolyline(
            [(dx - 650, floor_z + 100), (dx + 650, floor_z + 100), (dx + 650, floor_z + 1950), (dx - 650, floor_z + 1950)],
            close=True,
            dxfattribs={"layer": "CAR_BODY"},
        )
    for bx in bogie_xs:
        blk_side.add_lwpolyline(
            [(bx - 1300, 250), (bx + 1300, 250), (bx + 1300, floor_z - 150), (bx - 1300, floor_z - 150)],
            close=True,
            dxfattribs={"layer": "BOGIE"},
        )
        for wx in (bx - 1050, bx + 1050):
            blk_side.add_circle((wx, 430), radius=430, dxfattribs={"layer": "BOGIE"})
    blk_side.add_lwpolyline(
        [(body_len * 0.42, cant_z + roof_crown), (body_len * 0.58, cant_z + roof_crown),
         (body_len * 0.58, cant_z + roof_crown + 320), (body_len * 0.42, cant_z + roof_crown + 320)],
        close=True, dxfattribs={"layer": "ROOF_EQUIP"}
    )
    blk_side.add_lwpolyline(
        [(body_len * 0.38, 450), (body_len * 0.62, 450), (body_len * 0.62, floor_z - 120), (body_len * 0.38, floor_z - 120)],
        close=True, dxfattribs={"layer": "UNDER_EQUIP"}
    )

    blk_plan = doc.blocks.new(name="BLK_CAR_PLAN")
    half_w = width / 2.0
    plan_top = [(0.0, half_w)] + plan_half_pts
    plan_bot = [(x, -y) for x, y in reversed(plan_half_pts)] + [(0.0, -half_w)]
    blk_plan.add_lwpolyline(plan_top + plan_bot, close=True, dxfattribs={"layer": "CAR_BODY"})
    blk_plan.add_line((0.0, 0.0), (total_len, 0.0), dxfattribs={"layer": "CAR_CENTER"})
    for sx, sy, s_depth in seat_positions:
        blk_plan.add_lwpolyline(
            [(sx - 220, sy - s_depth / 2), (sx + 220, sy - s_depth / 2),
             (sx + 220, sy + s_depth / 2), (sx - 220, sy + s_depth / 2)],
            close=True, dxfattribs={"layer": "INTERIOR"}
        )

    blk_tb = doc.blocks.new(name="BLK_A1_TITLEBLOCK")
    blk_tb.add_lwpolyline([(10, 10), (831, 10), (831, 584), (10, 584)], close=True)
    blk_tb.add_lwpolyline([(591, 10), (831, 10), (831, 68), (591, 68)], close=True)
    blk_tb.add_attdef("DWG_NO", (600, 44), dxfattribs={"height": 6})
    blk_tb.add_attdef("DWG_TITLE", (600, 20), dxfattribs={"height": 4.5})

    car_pitch = total_len + 500.0
    for i in range(4):
        is_tail = (i == 3)
        x_ins = i * car_pitch + (total_len if is_tail else 0.0)
        msp.add_blockref("BLK_CAR_SIDE", insert=(x_ins, 0.0), dxfattribs={"xscale": -1 if is_tail else 1})

    msp.add_blockref("BLK_CAR_SIDE", insert=(0.0, 15000.0))
    msp.add_blockref("BLK_CAR_PLAN", insert=(0.0, 23000.0))
    msp.add_linear_dim(
        base=(0.0, 13800.0), p1=(0.0, 15000.0 + floor_z), p2=(total_len, 15000.0 + floor_z),
        dimstyle="Standard", dxfattribs={"layer": "DIM"}
    ).render()

    sec_pts = [
        (-half_w * 0.88, 35000 + floor_z),
        (-half_w, 35000 + floor_z + 180),
        (-half_w, 35000 + cant_z * 0.65),
        (-half_w * 0.88, 35000 + cant_z),
        (0.0, 35000 + cant_z + roof_crown),
        (half_w * 0.88, 35000 + cant_z),
        (half_w, 35000 + cant_z * 0.65),
        (half_w, 35000 + floor_z + 180),
        (half_w * 0.88, 35000 + floor_z),
    ]
    msp.add_lwpolyline(sec_pts, close=True, dxfattribs={"layer": "CAR_BODY"})
    msp.add_lwpolyline(
        [(-1700, 35000), (1700, 35000), (1700, 39500), (-1700, 39500)],
        close=True, dxfattribs={"layer": "GAUGE_LIMIT"}
    )

    consist_cx = (4 * car_pitch - 500.0) / 2.0
    car_cx = total_len / 2.0

    sheets_spec = [
        ("G-01_차량편성도", "DWG-G-01", "4량 차량편성도 (1:125)", (consist_cx, 2000.0), 125.0, ["INTERIOR"]),
        ("G-02_일반배치도", "DWG-G-02", "선두차 일반배치도 (1:50)", (car_cx, 19500.0), 50.0, ["INTERIOR"]),
        ("G-03_정면도", "DWG-G-03", "선두차 정면도 (1:20)", (0.0, 37200.0), 20.0, ["GAUGE_LIMIT"]),
        ("G-04_객실횡단면도", "DWG-G-04", "객실 횡단면도 (1:20)", (0.0, 37200.0), 20.0, []),
        ("G-05_내장재배치도", "DWG-G-05", "실내 좌석 및 내장재 배치도 (1:50)", (car_cx, 23000.0), 50.0, ["ROOF_EQUIP", "UNDER_EQUIP"]),
        ("G-06_지붕기기배치도", "DWG-G-06", "지붕 상부 기기 배치도 (1:50)", (car_cx, 17800.0), 50.0, ["INTERIOR", "UNDER_EQUIP"]),
        ("G-07_하부기기배치도", "DWG-G-07", "언더프레임 및 하부기기 배치도 (1:50)", (car_cx, 15800.0), 50.0, ["INTERIOR", "ROOF_EQUIP"]),
        ("G-08_대차일반배치도", "DWG-G-08", "대차 일반배치도 (1:15)", (bogie_xs[0], 15700.0), 15.0, ["INTERIOR", "ROOF_EQUIP"]),
        ("G-09_출입문창문배치도", "DWG-G-09", "출입문 및 측면 입면 배치도 (1:40)", (car_cx, 17200.0), 40.0, ["INTERIOR", "ROOF_EQUIP", "UNDER_EQUIP"]),
        ("G-10_차량한계검토도", "DWG-G-10", "차량한계 및 단면 검토도 (1:20)", (0.0, 37200.0), 20.0, []),
    ]

    for layout_name, dwg_no, title, view_center, scale_denom, frozen in sheets_spec:
        psp = doc.layouts.new(layout_name)
        psp.page_setup(size=(841, 594), margins=(0, 0, 0, 0), units="mm")
        psp.add_blockref("BLK_A1_TITLEBLOCK", insert=(0, 0)).add_auto_attribs(
            {"DWG_NO": dwg_no, "DWG_TITLE": title}
        )
        vp_h = 400.0
        vp = psp.add_viewport(
            center=(420.0, 325.0),
            size=(760.0, vp_h),
            view_center_point=view_center,
            view_height=vp_h * scale_denom,
            dxfattribs={"layer": "VIEWPORTS"},
        )
        for flayer in frozen:
            vp.freeze(flayer)

    doc.layers.get("VIEWPORTS").off()
    doc.saveas(output_path)


# =============================================================================
# 3. PySide6 + PyVistaQt 통합 메인 윈도우
# =============================================================================
class RailcarConceptWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("철도차량 디자인 콘셉트 3D 스튜디오 + 기본도 10장 DXF 출력")
        self.resize(1380, 840)

        self.params = {
            "total_length": 20000.0,
            "cab_length": 4500.0,
            "width": 3120.0,
            "floor_z": 1100.0,
            "cant_z": 3150.0,
            "roof_crown": 480.0,
            "nose_exp": 1.8,
            "seat_pitch": 920.0,
        }
        self.view_mode = "solid"

        self._init_ui()
        self._init_scene()
        self._update_all_geometry(reset_camera=True)

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        left_panel = QWidget()
        left_panel.setFixedWidth(345)
        left_layout = QVBoxLayout(left_panel)

        grp_preset = QGroupBox("선두부 콘셉트 프리셋")
        hlay_preset = QHBoxLayout(grp_preset)
        btn_ktx = QPushButton("KTX-이음형 (유선형)")
        btn_itx = QPushButton("ITX-마음형 (준고속)")
        btn_ktx.clicked.connect(lambda: self._apply_preset(cab_len=5200.0, nose_exp=1.6, roof_crown=450.0))
        btn_itx.clicked.connect(lambda: self._apply_preset(cab_len=3400.0, nose_exp=2.4, roof_crown=380.0))
        hlay_preset.addWidget(btn_ktx)
        hlay_preset.addWidget(btn_itx)

        grp_shape = QGroupBox("외형 곡면 · 치수 제어 (실시간)")
        form_shape = QFormLayout(grp_shape)

        self.lbl_roof, self.sld_roof = self._create_slider(150, 950, int(self.params["roof_crown"]), "mm")
        self.sld_roof.valueChanged.connect(lambda v: self._on_param_change("roof_crown", float(v), self.lbl_roof, "mm"))
        form_shape.addRow("상부 지붕 곡률:", self._wrap_slider(self.sld_roof, self.lbl_roof))

        self.lbl_nose, self.sld_nose = self._create_slider(10, 35, int(self.params["nose_exp"] * 10), "")
        self.sld_nose.valueChanged.connect(
            lambda v: self._on_param_change("nose_exp", v / 10.0, self.lbl_nose, "", scale=0.1)
        )
        form_shape.addRow("정면 노즈 곡률:", self._wrap_slider(self.sld_nose, self.lbl_nose))

        self.lbl_cab, self.sld_cab = self._create_slider(2500, 7000, int(self.params["cab_length"]), "mm")
        self.sld_cab.valueChanged.connect(lambda v: self._on_param_change("cab_length", float(v), self.lbl_cab, "mm"))
        form_shape.addRow("선두부 길이:", self._wrap_slider(self.sld_cab, self.lbl_cab))

        self.lbl_width, self.sld_width = self._create_slider(2600, 3400, int(self.params["width"]), "mm")
        self.sld_width.valueChanged.connect(lambda v: self._on_param_change("width", float(v), self.lbl_width, "mm"))
        form_shape.addRow("차체 폭:", self._wrap_slider(self.sld_width, self.lbl_width))

        self.lbl_len, self.sld_len = self._create_slider(15000, 25000, int(self.params["total_length"]), "mm")
        self.sld_len.valueChanged.connect(lambda v: self._on_param_change("total_length", float(v), self.lbl_len, "mm"))
        form_shape.addRow("차량 전장:", self._wrap_slider(self.sld_len, self.lbl_len))

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

        grp_export = QGroupBox("도면 출력 (기본도 10장)")
        vlay_exp = QVBoxLayout(grp_export)
        btn_export_dxf = QPushButton("기본도 10장 DXF 내보내기 (ezdxf)")
        btn_export_dxf.setMinimumHeight(40)
        btn_export_dxf.clicked.connect(self._on_export_dxf_clicked)
        vlay_exp.addWidget(btn_export_dxf)

        left_layout.addWidget(grp_preset)
        left_layout.addWidget(grp_shape)
        left_layout.addWidget(grp_interior)
        left_layout.addWidget(grp_view)
        left_layout.addWidget(grp_export)
        left_layout.addStretch()

        self.plotter = QtInteractor(self)
        main_layout.addWidget(left_panel)
        main_layout.addWidget(self.plotter.interactor, 1)

    def _apply_preset(self, cab_len: float, nose_exp: float, roof_crown: float):
        self.sld_cab.setValue(int(cab_len))
        self.sld_nose.setValue(int(nose_exp * 10))
        self.sld_roof.setValue(int(roof_crown))

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

    def _on_export_dxf_clicked(self):
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "기본도 10장 DXF 저장",
            "railcar_basic_10_sheets.dxf",
            "DXF Files (*.dxf)",
        )
        if not save_path:
            return
        try:
            export_10_basic_drawings_dxf(self.params, save_path)
            QMessageBox.information(
                self,
                "내보내기 완료",
                f"기본도 10장(G-01 ~ G-10)이 성공적으로 저장되었습니다.\n\n경로: {save_path}",
            )
        except ImportError:
            QMessageBox.critical(
                self,
                "패키지 필요",
                "ezdxf 패키지가 설치되어 있지 않습니다.\n'pip install ezdxf' 실행 후 다시 시도해 주세요.",
            )
        except Exception as exc:
            QMessageBox.critical(self, "내보내기 오류", f"DXF 생성 중 오류가 발생했습니다:\n{exc}")

    def _update_all_geometry(self, reset_camera: bool = False):
        p = self.params

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

        underframe = build_floor_and_underframe_mesh(
            total_length=p["total_length"],
            cab_length=p["cab_length"],
            width=p["width"],
            floor_z=p["floor_z"],
            nose_exp=p["nose_exp"],
        )
        self.plotter.add_mesh(underframe, name="underframe_bogie", color="#485460", smooth_shading=False)

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