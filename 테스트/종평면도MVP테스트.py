import math
import ezdxf
from ifcopenshell.express.rules.IFC4X3_ADD2 import position


def rotate_point(x, y, cx, cy, angle_deg):
    """평면 좌표계 회전 변환 함수 (중심점 기준 회전)"""
    rad = math.radians(angle_deg)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)

    # 원점 기준으로 이동 후 회전
    dx = x - cx
    dy = y - cy
    rx = dx * cos_a - dy * sin_a
    ry = dx * sin_a + dy * cos_a

    # 원래 위치로 복원
    return rx + cx, ry + cy


def generate_plan_profile(
    plan_pts,
    profile_pts,
    output_filename="plan_profile.dxf",
):
    # ==========================================
    # DXF 생성
    # ==========================================

    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    doc.layers.new("PLAN", dxfattribs={"color": 3})
    doc.layers.new("PROFILE", dxfattribs={"color": 1})
    doc.layers.new("FRAME", dxfattribs={"color": 7})
    doc.layers.new("GRID", dxfattribs={"color": 8})

    # ==========================================
    # 축척 설정
    # ==========================================

    H_SCALE = 1000.0
    V_SCALE = 400.0
    scale_factor = 1.0
    y_scale_factor = H_SCALE / V_SCALE
    # ==========================================
    # 도곽
    # ==========================================

    SHEET_W = 841
    SHEET_H = 594

    msp.add_lwpolyline(
        [
            (0, 0),
            (SHEET_W, 0),
            (SHEET_W, SHEET_H),
            (0, SHEET_H),
            (0, 0),
        ],
        dxfattribs={"layer": "FRAME"},
    )
    #타이틀
    title = '종평면도 (1)'
    project_name = '사업명: 행복도시철도 1호선 건설공사'
    scale_text = '1:1000'

    msp.add_text(text=title,height=15, dxfattribs={
        "layer": "DOGAK",
        "color": 1,
        'insert' :(376,563)
    })
    msp.add_text(text=project_name, height=15, dxfattribs={
        "layer": "DOGAK",
        "color": 1,
        'insert': (25, 25)
    })
    #평면 뷰포트
    plan_vport_x = 810
    plan_vport_y = 350
    plan_vport_margin = 35
    plan_vport_top = 550
    msp.add_lwpolyline(
        [
            (plan_vport_margin, plan_vport_top),
            (plan_vport_x, plan_vport_top),
            (plan_vport_x, plan_vport_y),
            (plan_vport_margin, plan_vport_y),
            (plan_vport_margin, plan_vport_top),
        ],
        dxfattribs={"layer": "V_PLAN_FRAME"},
    )

    # 종단 뷰포트
    profile_vport_x = 810
    profile_vport_y = 50
    profile_vport_margin = 35
    profile_vport_top = 250
    msp.add_lwpolyline(
        [
            (profile_vport_margin, profile_vport_top),
            (profile_vport_x, profile_vport_top),
            (profile_vport_x, profile_vport_y),
            (profile_vport_margin, profile_vport_y),
            (profile_vport_margin, profile_vport_top),
        ],
        dxfattribs={"layer": "V_PLAN_FRAME"},
    )
    # ==========================================
    # 평면도
    # ==========================================

    PLAN_ORIGIN_X = plan_vport_margin
    PLAN_ORIGIN_Y = 450

    if plan_pts:

        start_x, start_y = plan_pts[0]
        end_x, end_y = plan_pts[-1]

        angle = math.degrees(
            math.atan2(
                end_y - start_y,
                end_x - start_x,
            )
        )

        rotation_angle = -angle

        cx = sum(x for x, _ in plan_pts) / len(plan_pts)
        cy = sum(y for _, y in plan_pts) / len(plan_pts)

        rotated_pts = []

        for x, y in plan_pts:

            rx, ry = rotate_point(
                x,
                y,
                cx,
                cy,
                rotation_angle,
            )

            rotated_pts.append((rx, ry))

        min_x = min(p[0] for p in rotated_pts)
        min_y = min(p[1] for p in rotated_pts)

        transformed_plan = []

        for rx, ry in rotated_pts:

            tx = (
                (rx - min_x)
                * scale_factor
                + PLAN_ORIGIN_X
            )

            ty = (
                (ry - min_y)
                * scale_factor
                + PLAN_ORIGIN_Y
            )

            transformed_plan.append((tx, ty))

        msp.add_lwpolyline(
            transformed_plan,
            dxfattribs={"layer": "PLAN"},
        )

    # ==========================================
    # 종단도
    # ==========================================

    PROFILE_ORIGIN_X = PLAN_ORIGIN_X
    PROFILE_ORIGIN_Y = 150

    min_sta = min(sta for sta, _ in profile_pts)
    max_sta = max(sta for sta, _ in profile_pts)

    min_el = min(el for _, el in profile_pts)

    # 종단도 기준고(DL)

    datum_el = (
        math.floor(min_el / 10.0)
        * 10.0
    )

    profile_draw_pts = []

    for sta, el in profile_pts:

        px = (
            PROFILE_ORIGIN_X
            + (sta - min_sta)
            * 1.0
        )

        py = (
            PROFILE_ORIGIN_Y
            + (el - datum_el)
            * y_scale_factor
        )

        profile_draw_pts.append((px, py))

    msp.add_lwpolyline(
        profile_draw_pts,
        dxfattribs={"layer": "PROFILE"},
    )

    # ==========================================
    # STA Grid
    # ==========================================

    STA_INTERVAL = 200

    sta = math.floor(min_sta / STA_INTERVAL) * STA_INTERVAL

    while sta <= max_sta:

        gx = (
            PROFILE_ORIGIN_X
            + (sta - min_sta)
            * scale_factor
        )

        msp.add_line(
            (gx, PROFILE_ORIGIN_Y),
            (gx, profile_vport_y),
            dxfattribs={"layer": "GRID"},
        )

        msp.add_text(
            f"{int(sta)}",
            height=2.5,
            dxfattribs={
                "layer": "GRID",
            },
        ).set_placement(
            (gx + 1, PROFILE_ORIGIN_Y - 5)
        )

        sta += STA_INTERVAL

    print(
        f"축척 H:{int(H_SCALE)}, V:{int(V_SCALE)}"
    )

    print(
        f"기준고 DL={datum_el:.3f}"
    )

    doc.saveas(output_filename)

    print(
        f"저장 완료 : {output_filename}"
    )

# ==========================================
# 실행 테스트
# ==========================================
if __name__ == "__main__":
    # 샘플 평면 선형 객체 (2D 좌표: x,y)
    sample_plan_linestring = [
        (252729.930,407621.060),
        (253356.383,403670.634),
        (251859.699,396839.281),
        (255562.242,368287.722),
        (252930.461,340078.738),
        (246535.906,329365.785),
        (241509.931,316253.765),
        (233279.348,311736.306),
    ]

    # 샘플 종단 선형 객체 (STA, EL)
    sample_profile_linestring = \
        [
            [0,107.609],
            [950,107.609],
            [1760,120.569],
            [4000,127.289],
            [6000,121.289],
            [7150,129.914],
        ]
    generate_plan_profile(sample_plan_linestring, sample_profile_linestring)