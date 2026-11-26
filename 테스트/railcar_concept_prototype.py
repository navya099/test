"""
철도차량 디자인 콘셉트용 3D 파라메트릭 스튜디오 (고급 파라미터화 + 3D 기반 기본도 10장 DXF)

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
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)


# =============================================================================
# 1. 지오메트리 & 좌석/대차 좌표 계산 엔진
# =============================================================================
def _superellipse_profile(t: float, exp_p: float, round_q: float = 2.4) -> float:
    """
    t=0 에서 기울기 0(차체와 매끄러운 C1 접합),
    t=1 에서 접선이 수직(둥근 반타원 노즈)이 되는 슈퍼엘립스 감쇠 함수.
    """
    t = min(max(t, 0.0), 1.0)
    val = max(1.0 - (t ** exp_p), 0.0)
    return float(val ** (1.0 / round_q))


def compute_bogie_positions(
    total_length: float,
    bogie_rear_x: float,
    bogie_front_margin: float,
) -> list[float]:
    """전위/후위 대차의 X 중심 좌표를 안전 범위 내에서 계산한다."""
    x_rear = min(max(bogie_rear_x, 1400.0), total_length * 0.45)
    x_front = max(total_length - bogie_front_margin, x_rear + 3000.0)
    x_front = min(x_front, total_length - 1800.0)
    return [x_rear, x_front]


def compute_seat_positions(
    total_length: float,
    cab_length: float,
    width: float,
    seat_pitch: float,
) -> tuple[list[tuple[float, float, float]], float]:
    """차체 치수와 출입문 간섭을 고려한 좌석 중심 좌표 (x, y, seat_depth) 목록 계산"""
    body_len = max(total_length - cab_length, 2000.0)
    door_centers = [body_len * 0.25, body_len * 0.75]
    door_clearance = 1500.0

    raw_zones = [
        (800.0, door_centers[0] - door_clearance / 2.0),
        (door_centers[0] + door_clearance / 2.0, door_centers[1] - door_clearance / 2.0),
        (door_centers[1] + door_clearance / 2.0, body_len - 800.0),
    ]

    aisle_half = 320.0
    seat_depth = max(min((width * 0.39 - aisle_half), 880.0), 420.0)
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


def build_carbody_exterior_grid(
    total_length: float,
    cab_length: float,
    width: float,
    floor_z: float,
    wall_height: float,
    roof_crown: float,
    nose_exp: float,
    side_bulge: float,
    skirt_taper_pct: float,
    nx_cab: int = 32,
    nx_body: int = 16,
    nu: int = 37,
) -> tuple[pv.StructuredGrid, np.ndarray, np.ndarray, np.ndarray]:
    """
    차체 높이(floor_z, wall_height, roof_crown)와
    측면 단면 형상(side_bulge, skirt_taper_pct)을 자유롭게 반영한 3D 차체 외피 격자 생성.
    """
    cant_z = floor_z + wall_height
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
    total_h = wall_height + roof_crown
    bumper_z = floor_z + 100.0
    taper_ratio = skirt_taper_pct / 100.0

    for i, x_val in enumerate(x_stations):
        t = 0.0 if x_val <= body_length else (x_val - body_length) / cab_length
        t = min(max(t, 0.0), 1.0)

        w_scale = _superellipse_profile(t, exp_p=nose_exp, round_q=2.6)
        h_scale = _superellipse_profile(t, exp_p=max(nose_exp * 0.9, 1.1), round_q=2.2)

        curr_floor_z = (floor_z - 120.0) + (bumper_z - (floor_z - 120.0)) * (t ** 8.0)
        curr_top_z = bumper_z + (floor_z + total_h - bumper_z) * h_scale

        curr_h = max(curr_top_z - curr_floor_z, 0.0)
        crown_ratio = roof_crown / max(total_h, 1.0)
        curr_crown = curr_h * crown_ratio
        curr_cant_z = curr_top_z - curr_crown
        curr_half_w = half_w * w_scale
        curr_bulge = side_bulge * w_scale

        # 상단 캔트레일 / 허리(최대 배부름) / 스커트 최하단 폭
        y_top = curr_half_w * (0.88 if side_bulge >= 0 else 0.96)
        y_waist = max(curr_half_w + curr_bulge, curr_half_w * 0.65)
        y_skirt_bot = curr_half_w * (1.0 - taper_ratio)

        y_row = np.zeros(nu)
        z_row = np.zeros(nu)

        for j, u_val in enumerate(u):
            abs_u = abs(u_val)
            sign_u = 1.0 if u_val >= 0 else -1.0

            if abs_u <= 0.45:
                # 상부 지붕 곡면
                frac = u_val / 0.45
                y_row[j] = frac * y_top
                z_row[j] = curr_cant_z + curr_crown * (1.0 - frac ** 2)
            elif abs_u <= 0.85:
                # 측면 형상: 캔트레일(0) -> 허리 배부름(0.5) -> 스커트 상단(1.0)
                wall_frac = (abs_u - 0.45) / 0.40
                # 2차 베지어 보간으로 캔트레일-허리-스커트 연결
                y_end = curr_half_w
                y_val = ((1 - wall_frac) ** 2) * y_top + 2 * (1 - wall_frac) * wall_frac * y_waist + (wall_frac ** 2) * y_end
                y_row[j] = sign_u * y_val
                skirt_top_z = curr_floor_z + min(220.0, curr_h * 0.18)
                z_row[j] = curr_cant_z - wall_frac * (curr_cant_z - skirt_top_z)
            else:
                # 하부 스커트 꺾임(skirt_taper_pct 반영)
                skirt_frac = (abs_u - 0.85) / 0.15
                y_row[j] = sign_u * (curr_half_w + (y_skirt_bot - curr_half_w) * skirt_frac)
                skirt_top_z = curr_floor_z + min(220.0, curr_h * 0.18)
                z_row[j] = skirt_top_z - (skirt_top_z - curr_floor_z) * skirt_frac

        X[i, :] = x_val
        Y[i, :] = y_row
        Z[i, :] = z_row

    return pv.StructuredGrid(X, Y, Z), X, Y, Z


def grid_to_closed_surface(grid: pv.StructuredGrid, X: np.ndarray, Y: np.ndarray, Z: np.ndarray) -> pv.PolyData:
    """StructuredGrid 외피에 후단(X=0) 격벽 마개를 결합해 닫힌 표면 PolyData 반환"""
    ext_surf = grid.extract_surface()
    rear_pts = np.column_stack([X[0, :], Y[0, :], Z[0, :]])
    rear_faces = np.hstack([[len(rear_pts)], np.arange(len(rear_pts))])
    rear_cap = pv.PolyData(rear_pts, rear_faces).triangulate()
    return ext_surf.merge(rear_cap)


def build_floor_and_underframe_mesh(
    total_length: float,
    floor_z: float,
    bogie_rear_x: float,
    bogie_front_margin: float,
    skirt_taper_pct: float,
    X: np.ndarray,
    Y: np.ndarray,
) -> pv.PolyData:
    """실제 외피 격자 하단 폭에 맞춘 바닥판 + 자유 배치 대차 매스 2기 생성"""
    # 스커트 최하단 폭 안쪽으로 밀착
    scale_inner = max(0.95 - (skirt_taper_pct / 100.0), 0.65)
    y_max_per_station = np.max(np.abs(Y), axis=1) * scale_inner
    x_per_station = X[:, 0]

    top_edge = [(float(x_per_station[i]), float(y_max_per_station[i])) for i in range(len(x_per_station) - 2)]
    bot_edge = [(x, -y) for x, y in reversed(top_edge)]
    poly_2d = top_edge + bot_edge

    pts_3d = np.array([[x, y, floor_z - 120.0] for x, y in poly_2d], dtype=float)
    faces = np.hstack([[len(pts_3d)], np.arange(len(pts_3d))])
    floor_poly = pv.PolyData(pts_3d, faces).triangulate().extrude((0.0, 0.0, 120.0), capping=True)

    bogie_x_positions = compute_bogie_positions(total_length, bogie_rear_x, bogie_front_margin)
    meshes = [floor_poly]
    frame_top_z = max(floor_z - 150.0, 500.0)
    for bx in bogie_x_positions:
        bogie_frame = pv.Box(bounds=(bx - 1300.0, bx + 1300.0, -1050.0, 1050.0, 200.0, frame_top_z))
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
# 2. 실제 3D 메쉬 추출(Slice / 투영) 기반 기본도 10장 ezdxf 내보내기 엔진
# =============================================================================
def _write_pv_slice_to_dxf(
    target_layout,
    sliced_mesh: pv.PolyData,
    axis_u: int,
    axis_v: int,
    offset_u: float = 0.0,
    offset_v: float = 0.0,
    layer: str = "CAR_BODY",
) -> None:
    if sliced_mesh.n_points == 0 or sliced_mesh.n_lines == 0:
        return

    pts = sliced_mesh.points
    lines = sliced_mesh.lines
    idx = 0
    total_len = len(lines)

    while idx < total_len:
        n_verts = int(lines[idx])
        vert_ids = lines[idx + 1 : idx + 1 + n_verts]
        idx += 1 + n_verts

        if n_verts < 2:
            continue
        poly_pts = [
            (float(pts[vid, axis_u] + offset_u), float(pts[vid, axis_v] + offset_v))
            for vid in vert_ids
        ]
        if n_verts == 2:
            target_layout.add_line(poly_pts[0], poly_pts[1], dxfattribs={"layer": layer})
        else:
            target_layout.add_lwpolyline(poly_pts, dxfattribs={"layer": layer})


def export_10_basic_drawings_dxf(params: dict, output_path: str) -> None:
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
    wall_height = params["wall_height"]
    cant_z = floor_z + wall_height
    roof_crown = params["roof_crown"]
    nose_exp = params["nose_exp"]
    side_bulge = params["side_bulge"]
    skirt_taper = params["skirt_taper_pct"]
    bogie_rear_x = params["bogie_rear_x"]
    bogie_front_margin = params["bogie_front_margin"]
    seat_pitch = params["seat_pitch"]

    ext_grid, X, Y, Z = build_carbody_exterior_grid(
        total_len, cab_len, width, floor_z, wall_height, roof_crown, nose_exp, side_bulge, skirt_taper
    )
    ext_surf = grid_to_closed_surface(ext_grid, X, Y, Z)
    underframe_mesh = build_floor_and_underframe_mesh(
        total_len, floor_z, bogie_rear_x, bogie_front_margin, skirt_taper, X, Y
    )
    seats_mesh, _ = build_interior_seats_mesh(total_len, cab_len, width, floor_z, seat_pitch)

    body_len = max(total_len - cab_len, 2000.0)
    bogie_xs = compute_bogie_positions(total_len, bogie_rear_x, bogie_front_margin)
    mid_u = X.shape[1] // 2

    # [블록 1] 실제 3D 메쉬 측면 입면 (BLK_CAR_SIDE)
    blk_side = doc.blocks.new(name="BLK_CAR_SIDE")
    top_profile = [(float(X[i, mid_u]), float(Z[i, mid_u])) for i in range(X.shape[0])]
    bot_profile = [(float(X[i, 0]), float(Z[i, 0])) for i in reversed(range(X.shape[0]))]
    blk_side.add_lwpolyline(top_profile + bot_profile, close=True, dxfattribs={"layer": "CAR_BODY"})

    cant_idx = int(np.argmin(np.abs(np.linspace(-1.0, 1.0, X.shape[1]) - 0.45)))
    cant_line = [(float(X[i, cant_idx]), float(Z[i, cant_idx])) for i in range(X.shape[0])]
    blk_side.add_lwpolyline(cant_line, dxfattribs={"layer": "CAR_BODY"})

    for dx in (body_len * 0.25, body_len * 0.75):
        blk_side.add_lwpolyline(
            [(dx - 650, floor_z + 100), (dx + 650, floor_z + 100),
             (dx + 650, min(floor_z + 1950, cant_z - 100)), (dx - 650, min(floor_z + 1950, cant_z - 100))],
            close=True,
            dxfattribs={"layer": "CAR_BODY"},
        )
    for bx in bogie_xs:
        blk_side.add_lwpolyline(
            [(bx - 1300, 200), (bx + 1300, 200), (bx + 1300, max(floor_z - 150, 500)), (bx - 1300, max(floor_z - 150, 500))],
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

    # [블록 2] 실제 3D 메쉬 평면도 (BLK_CAR_PLAN)
    blk_plan = doc.blocks.new(name="BLK_CAR_PLAN")
    y_max_arr = np.max(Y, axis=1)
    y_min_arr = np.min(Y, axis=1)
    plan_top = [(float(X[i, 0]), float(y_max_arr[i])) for i in range(X.shape[0])]
    plan_bot = [(float(X[i, 0]), float(y_min_arr[i])) for i in reversed(range(X.shape[0]))]
    blk_plan.add_lwpolyline(plan_top + plan_bot, close=True, dxfattribs={"layer": "CAR_BODY"})
    blk_plan.add_line((0.0, 0.0), (total_len, 0.0), dxfattribs={"layer": "CAR_CENTER"})

    plan_seats_slice = seats_mesh.slice(normal=(0, 0, 1), origin=(0, 0, floor_z + 400.0))
    _write_pv_slice_to_dxf(blk_plan, plan_seats_slice, axis_u=0, axis_v=1, layer="INTERIOR")

    # [블록 3] A1 도곽
    blk_tb = doc.blocks.new(name="BLK_A1_TITLEBLOCK")
    blk_tb.add_lwpolyline([(10, 10), (831, 10), (831, 584), (10, 584)], close=True)
    blk_tb.add_lwpolyline([(591, 10), (831, 10), (831, 68), (591, 68)], close=True)
    blk_tb.add_attdef("DWG_NO", (600, 44), dxfattribs={"height": 6})
    blk_tb.add_attdef("DWG_TITLE", (600, 20), dxfattribs={"height": 4.5})

    # Modelspace 배치
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
    # 대차 중심거리 치수선 추가
    msp.add_linear_dim(
        base=(0.0, 14350.0), p1=(bogie_xs[0], 15000.0 + 430.0), p2=(bogie_xs[1], 15000.0 + 430.0),
        dimstyle="Standard", dxfattribs={"layer": "DIM"}
    ).render()

    # 횡단면도 (3D Slice)
    sec_x = body_len * 0.55
    ext_cross = ext_surf.slice(normal=(1, 0, 0), origin=(sec_x, 0, 0))
    uf_cross = underframe_mesh.slice(normal=(1, 0, 0), origin=(sec_x, 0, 0))
    seat_cross = seats_mesh.slice(normal=(1, 0, 0), origin=(sec_x, 0, 0))

    _write_pv_slice_to_dxf(msp, ext_cross, axis_u=1, axis_v=2, offset_u=0.0, offset_v=35000.0, layer="CAR_BODY")
    _write_pv_slice_to_dxf(msp, uf_cross, axis_u=1, axis_v=2, offset_u=0.0, offset_v=35000.0, layer="BOGIE")
    _write_pv_slice_to_dxf(msp, seat_cross, axis_u=1, axis_v=2, offset_u=0.0, offset_v=35000.0, layer="INTERIOR")
    msp.add_lwpolyline(
        [(-1700, 35000), (1700, 35000), (1700, 39500), (-1700, 39500)],
        close=True, dxfattribs={"layer": "GAUGE_LIMIT"}
    )

    # 정면도 (3D 선두부 등고선)
    front_offset_x = 15000.0
    nx_body_start = 15
    cab_indices = np.linspace(nx_body_start, X.shape[0] - 1, 6, dtype=int)
    for ci in cab_indices:
        pts_yz = [(float(Y[ci, j] + front_offset_x), float(Z[ci, j] + 35000.0)) for j in range(X.shape[1])]
        msp.add_lwpolyline(pts_yz, dxfattribs={"layer": "CAR_BODY"})
    uf_front = underframe_mesh.slice(normal=(1, 0, 0), origin=(bogie_xs[0], 0, 0))
    _write_pv_slice_to_dxf(msp, uf_front, axis_u=1, axis_v=2, offset_u=front_offset_x, offset_v=35000.0, layer="BOGIE")

    # 종단면도 (3D Slice)
    ext_long = ext_surf.slice(normal=(0, 1, 0), origin=(0, 0, 0))
    uf_long = underframe_mesh.slice(normal=(0, 1, 0), origin=(0, 0, 0))
    seat_long = seats_mesh.slice(normal=(0, 1, 0), origin=(0, 480.0, 0))
    _write_pv_slice_to_dxf(msp, ext_long, axis_u=0, axis_v=2, offset_u=0.0, offset_v=48000.0, layer="CAR_BODY")
    _write_pv_slice_to_dxf(msp, uf_long, axis_u=0, axis_v=2, offset_u=0.0, offset_v=48000.0, layer="BOGIE")
    _write_pv_slice_to_dxf(msp, seat_long, axis_u=0, axis_v=2, offset_u=0.0, offset_v=48000.0, layer="INTERIOR")

    consist_cx = (4 * car_pitch - 500.0) / 2.0
    car_cx = total_len / 2.0
    sec_cy = 35000.0 + (floor_z + wall_height + roof_crown) * 0.5

    sheets_spec = [
        ("G-01_차량편성도", "DWG-G-01", "4량 차량편성도 (1:125)", (consist_cx, 2000.0), 125.0, ["INTERIOR"]),
        ("G-02_일반배치도", "DWG-G-02", "선두차 일반배치도 (1:50)", (car_cx, 19500.0), 50.0, ["INTERIOR"]),
        ("G-03_정면도", "DWG-G-03", "선두차 정면도 - 3D 투영 (1:20)", (front_offset_x, sec_cy), 20.0, ["GAUGE_LIMIT"]),
        ("G-04_객실횡단면도", "DWG-G-04", "객실 횡단면도 - 3D Slice (1:20)", (0.0, sec_cy), 20.0, ["GAUGE_LIMIT"]),
        ("G-05_내장재배치도", "DWG-G-05", "실내 좌석 및 내장재 배치도 (1:50)", (car_cx, 23000.0), 50.0, ["ROOF_EQUIP", "UNDER_EQUIP"]),
        ("G-06_종단면도", "DWG-G-06", "차량 종단면도 - 3D Slice (1:50)", (car_cx, 50000.0), 50.0, ["ROOF_EQUIP", "UNDER_EQUIP"]),
        ("G-07_지붕하부기기배치도", "DWG-G-07", "지붕 및 하부 기기 배치도 (1:50)", (car_cx, 17000.0), 50.0, ["INTERIOR"]),
        ("G-08_대차일반배치도", "DWG-G-08", "후위 대차 일반배치도 (1:15)", (bogie_xs[0], 15700.0), 15.0, ["INTERIOR", "ROOF_EQUIP"]),
        ("G-09_출입문창문배치도", "DWG-G-09", "출입문 및 측면 입면 배치도 (1:40)", (car_cx, 17200.0), 40.0, ["INTERIOR", "ROOF_EQUIP", "UNDER_EQUIP"]),
        ("G-10_차량한계검토도", "DWG-G-10", "차량한계 및 3D 단면 검토도 (1:20)", (0.0, sec_cy), 20.0, []),
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
# 3. PySide6 + PyVistaQt 통합 메인 윈도우 (고급 파라미터 UI)
# =============================================================================
class RailcarConceptWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("철도차량 디자인 콘셉트 3D 스튜디오 (고급 파라미터화 + 기본도 10장)")
        self.resize(1420, 880)

        self.params = {
            "total_length": 20000.0,
            "cab_length": 4500.0,
            "width": 3120.0,
            "floor_z": 1100.0,
            "wall_height": 2050.0,      # 측벽 높이 (floor_z ~ cant_z)
            "roof_crown": 480.0,        # 상부 지붕 곡률 높이
            "nose_exp": 1.8,            # 정면 노즈 곡률 지수
            "side_bulge": 80.0,         # 측면 배부름 (+볼록 / 0수직 / -오목)
            "skirt_taper_pct": 10.0,    # 하부 스커트 안쪽 꺾임 (%)
            "bogie_rear_x": 3200.0,     # 후위 대차 중심 (X=0 기준)
            "bogie_front_margin": 5500.0,  # 전위 대차 중심 (선두 끝단에서 안쪽 거리)
            "seat_pitch": 920.0,
        }
        self.view_mode = "solid"
        self.sliders: dict[str, tuple[QSlider, QLabel, str, float]] = {}

        self._init_ui()
        self._init_scene()
        self._update_all_geometry(reset_camera=True)

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # 좌측 스크롤 가능한 고급 파라미터 패널
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(380)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # 0) 콘셉트 프리셋 (KTX / ITX / 박스형 전동차)
        grp_preset = QGroupBox("차종 콘셉트 프리셋")
        hlay_preset = QHBoxLayout(grp_preset)
        btn_ktx = QPushButton("KTX-이음형")
        btn_itx = QPushButton("ITX-마음형")
        btn_metro = QPushButton("도시철도형")
        btn_ktx.clicked.connect(lambda: self._apply_preset(cab=5200, nose=16, crown=450, wall=2000, bulge=120, taper=15))
        btn_itx.clicked.connect(lambda: self._apply_preset(cab=3400, nose=24, crown=380, wall=2050, bulge=60, taper=10))
        btn_metro.clicked.connect(lambda: self._apply_preset(cab=2200, nose=35, crown=240, wall=2200, bulge=0, taper=2))
        hlay_preset.addWidget(btn_ktx)
        hlay_preset.addWidget(btn_itx)
        hlay_preset.addWidget(btn_metro)

        # 1) 외형 높이 & 측면 & 선두부 파라미터
        grp_shape = QGroupBox("외형 치수 · 높이 · 측면 곡면 (실시간)")
        form_shape = QFormLayout(grp_shape)

        self._add_slider_row(form_shape, "floor_z", "바닥 높이:", 850, 1350, "mm")
        self._add_slider_row(form_shape, "wall_height", "측벽 높이:", 1600, 2600, "mm")
        self._add_slider_row(form_shape, "roof_crown", "상부 지붕 곡률:", 100, 950, "mm")
        self._add_slider_row(form_shape, "side_bulge", "측면 배부름:", -120, 220, "mm")
        self._add_slider_row(form_shape, "skirt_taper_pct", "하부 스커트 꺾임:", 0, 28, "%")
        self._add_slider_row(form_shape, "nose_exp", "정면 노즈 곡률:", 10, 38, "", scale=0.1)
        self._add_slider_row(form_shape, "cab_length", "선두부 길이:", 2000, 7500, "mm")
        self._add_slider_row(form_shape, "width", "차체 폭:", 2600, 3400, "mm")
        self._add_slider_row(form_shape, "total_length", "차량 전장:", 15000, 26000, "mm")

        # 2) 대차 위치 및 실내 좌석 배치
        grp_bogie_int = QGroupBox("대차 위치 · 실내 좌석 배치")
        form_bi = QFormLayout(grp_bogie_int)

        self._add_slider_row(form_bi, "bogie_rear_x", "후위 대차 (X=0):", 1600, 6000, "mm")
        self._add_slider_row(form_bi, "bogie_front_margin", "전위 대차 (앞여백):", 2200, 8500, "mm")

        spin_pitch = QDoubleSpinBox()
        spin_pitch.setRange(750.0, 1200.0)
        spin_pitch.setSingleStep(20.0)
        spin_pitch.setSuffix(" mm")
        spin_pitch.setValue(self.params["seat_pitch"])
        spin_pitch.valueChanged.connect(lambda v: self._on_param_change("seat_pitch", float(v)))
        form_bi.addRow("좌석 피치:", spin_pitch)

        self.lbl_seat_count = QLabel("배치 좌석: - 석")
        form_bi.addRow("배치 결과:", self.lbl_seat_count)

        # 3) 외벽 표시 / 단면 컷 토글
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

        # 4) 기본도 10장 DXF 내보내기
        grp_export = QGroupBox("도면 출력 (기본도 10장)")
        vlay_exp = QVBoxLayout(grp_export)
        btn_export_dxf = QPushButton("기본도 10장 DXF 내보내기 (3D 추출)")
        btn_export_dxf.setMinimumHeight(40)
        btn_export_dxf.clicked.connect(self._on_export_dxf_clicked)
        vlay_exp.addWidget(btn_export_dxf)

        left_layout.addWidget(grp_preset)
        left_layout.addWidget(grp_shape)
        left_layout.addWidget(grp_bogie_int)
        left_layout.addWidget(grp_view)
        left_layout.addWidget(grp_export)
        left_layout.addStretch()

        scroll.setWidget(left_panel)
        self.plotter = QtInteractor(self)
        main_layout.addWidget(scroll)
        main_layout.addWidget(self.plotter.interactor, 1)

    def _add_slider_row(self, form: QFormLayout, key: str, title: str, min_v: int, max_v: int, unit: str, scale: float = 1.0):
        init_raw = int(round(self.params[key] / scale))
        disp = f"{self.params[key]:.1f}" if scale != 1.0 else f"{init_raw}"
        lbl = QLabel(f"{disp}{unit}")
        lbl.setFixedWidth(62)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        sld = QSlider(Qt.Horizontal)
        sld.setRange(min_v, max_v)
        sld.setValue(init_raw)
        sld.valueChanged.connect(lambda v, k=key, lb=lbl, u=unit, sc=scale: self._on_param_change(k, v * sc, lb, u, sc))

        self.sliders[key] = (sld, lbl, unit, scale)

        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(sld, 1)
        h.addWidget(lbl)
        form.addRow(title, w)

    def _apply_preset(self, cab: int, nose: int, crown: int, wall: int, bulge: int, taper: int):
        mapping = {
            "cab_length": cab,
            "nose_exp": nose,
            "roof_crown": crown,
            "wall_height": wall,
            "side_bulge": bulge,
            "skirt_taper_pct": taper,
        }
        for key, raw_val in mapping.items():
            sld = self.sliders[key][0]
            sld.setValue(raw_val)

    def _init_scene(self):
        self.plotter.set_background("#1e222a", top="#2d333f")
        self.plotter.add_axes()

    def _on_param_change(self, key: str, value: float, label: QLabel | None = None, unit: str = "", scale: float = 1.0):
        self.params[key] = value
        if label is not None:
            disp = f"{value:.1f}" if scale != 1.0 else f"{int(round(value))}"
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
                f"3D 메쉬에서 추출한 기본도 10장(G-01 ~ G-10)이 저장되었습니다.\n\n경로: {save_path}",
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

        ext_grid, X, Y, Z = build_carbody_exterior_grid(
            total_length=p["total_length"],
            cab_length=p["cab_length"],
            width=p["width"],
            floor_z=p["floor_z"],
            wall_height=p["wall_height"],
            roof_crown=p["roof_crown"],
            nose_exp=p["nose_exp"],
            side_bulge=p["side_bulge"],
            skirt_taper_pct=p["skirt_taper_pct"],
        )
        ext_surf = grid_to_closed_surface(ext_grid, X, Y, Z)

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
            floor_z=p["floor_z"],
            bogie_rear_x=p["bogie_rear_x"],
            bogie_front_margin=p["bogie_front_margin"],
            skirt_taper_pct=p["skirt_taper_pct"],
            X=X,
            Y=Y,
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