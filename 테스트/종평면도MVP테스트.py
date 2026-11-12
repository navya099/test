import math
import ezdxf


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


import math
import ezdxf


def rotate_point(x, y, cx, cy, angle_deg):
    """중심점 기준 회전"""
    rad = math.radians(angle_deg)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)

    dx = x - cx
    dy = y - cy

    rx = dx * cos_a - dy * sin_a
    ry = dx * sin_a + dy * cos_a

    return rx + cx, ry + cy


def generate_plan_profile_mvp(
    plan_pts,
    profile_pts,
    output_filename="plan_profile_mvp.dxf"
):
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()

    # -----------------------------------------
    # Layer
    # -----------------------------------------
    doc.layers.new("PLAN_LINE", dxfattribs={"color": 3})
    doc.layers.new("PROFILE_LINE", dxfattribs={"color": 1})
    doc.layers.new("SHEET_FRAME", dxfattribs={"color": 7})

    # -----------------------------------------
    # Sheet Frame
    # -----------------------------------------
    SHEET_WIDTH = 1000
    SHEET_HEIGHT = 800

    msp.add_lwpolyline(
        [
            (0, 0),
            (SHEET_WIDTH, 0),
            (SHEET_WIDTH, SHEET_HEIGHT),
            (0, SHEET_HEIGHT),
            (0, 0),
        ],
        dxfattribs={"layer": "SHEET_FRAME"}
    )

    # =========================================
    # 1. PLAN VIEW
    # =========================================

    if plan_pts:

        # -----------------------------------------
        # 주 방향 계산
        # -----------------------------------------
        start_x, start_y = plan_pts[0]
        end_x, end_y = plan_pts[-1]

        dx = end_x - start_x
        dy = end_y - start_y

        angle = math.degrees(math.atan2(dy, dx))
        rotation_angle = -angle

        # -----------------------------------------
        # 중심점
        # -----------------------------------------
        cx = sum(x for x, _ in plan_pts) / len(plan_pts)
        cy = sum(y for _, y in plan_pts) / len(plan_pts)

        # -----------------------------------------
        # 회전
        # -----------------------------------------
        rotated_pts = []

        for x, y in plan_pts:
            rx, ry = rotate_point(
                x,
                y,
                cx,
                cy,
                rotation_angle
            )
            rotated_pts.append((rx, ry))

        # -----------------------------------------
        # Bounding Box
        # -----------------------------------------
        min_x = min(x for x, _ in rotated_pts)
        max_x = max(x for x, _ in rotated_pts)

        min_y = min(y for _, y in rotated_pts)
        max_y = max(y for _, y in rotated_pts)

        width = max_x - min_x
        height = max_y - min_y

        # -----------------------------------------
        # 배치 영역
        # -----------------------------------------
        PLAN_BOX_X = 50
        PLAN_BOX_Y = 350

        PLAN_BOX_W = 900
        PLAN_BOX_H = 400

        # -----------------------------------------
        # 자동 축척
        # -----------------------------------------
        scale_x = PLAN_BOX_W / width if width > 0 else 1
        scale_y = PLAN_BOX_H / height if height > 0 else 1

        plan_scale = min(scale_x, scale_y)

        transformed_plan = []

        for rx, ry in rotated_pts:

            tx = (
                (rx - min_x) * plan_scale
                + PLAN_BOX_X
            )

            ty = (
                (ry - min_y) * plan_scale
                + PLAN_BOX_Y
            )

            transformed_plan.append((tx, ty))

        msp.add_lwpolyline(
            transformed_plan,
            dxfattribs={"layer": "PLAN_LINE"}
        )

    # =========================================
    # 2. PROFILE VIEW
    # =========================================

    if profile_pts:

        min_sta = min(sta for sta, _ in profile_pts)
        max_sta = max(sta for sta, _ in profile_pts)

        min_el = min(el for _, el in profile_pts)
        max_el = max(el for _, el in profile_pts)

        sta_range = max_sta - min_sta
        el_range = max_el - min_el

        PROFILE_BOX_X = 50
        PROFILE_BOX_Y = 50

        PROFILE_BOX_W = 900
        PROFILE_BOX_H = 200

        h_scale = (
            PROFILE_BOX_W / sta_range
            if sta_range > 0 else 1
        )

        v_scale = (
            PROFILE_BOX_H / el_range
            if el_range > 0 else 1
        )

        transformed_profile = []

        for sta, el in profile_pts:

            px = (
                PROFILE_BOX_X
                + (sta - min_sta) * h_scale
            )

            py = (
                PROFILE_BOX_Y
                + (el - min_el) * v_scale
            )

            transformed_profile.append((px, py))

        msp.add_lwpolyline(
            transformed_profile,
            dxfattribs={"layer": "PROFILE_LINE"}
        )

    doc.saveas(output_filename)

    print(f"생성 완료 : {output_filename}")


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
    generate_plan_profile_mvp(sample_plan_linestring, sample_profile_linestring)