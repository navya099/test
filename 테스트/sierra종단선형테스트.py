
import argparse
import json
from pathlib import Path

import ezdxf


def validate_points(points, name):
    """측점 및 표고 데이터 검증"""
    if not isinstance(points, list) or len(points) < 2:
        raise ValueError(f"{name}: 좌표가 최소 2개 필요합니다.")

    result = []

    for i, point in enumerate(points):
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise ValueError(
                f"{name}: {i + 1}번째 좌표는 [측점, 표고] 형식이어야 합니다."
            )

        sta = float(point[0])
        elev = float(point[1])
        result.append((sta, elev))

    for i in range(1, len(result)):
        if result[i][0] <= result[i - 1][0]:
            raise ValueError(
                f"{name}: 측점은 중복 없이 오름차순이어야 합니다."
            )

    return result


def create_profile_dxf(
    plan_points,
    ground_points,
    filename="c:/temp/test_profile.dxf"
):
    """외부 좌표 데이터를 이용한 종단선형 DXF 생성"""

    plan_points = validate_points(plan_points, "PLAN_PROFILE")
    ground_points = validate_points(ground_points, "GROUND_PROFILE")

    doc = ezdxf.new("R2000")
    msp = doc.modelspace()

    plan_layer = "PLAN_PROFILE"
    ground_layer = "GROUND_PROFILE"

    doc.layers.new(
        name=plan_layer,
        dxfattribs={"color": 1}
    )

    doc.layers.new(
        name=ground_layer,
        dxfattribs={"color": 3}
    )

    # 계획선: X=측점(m), Y=표고(m)
    msp.add_lwpolyline(
        [(sta, elev, 0.0) for sta, elev in plan_points],
        format="xyb",
        dxfattribs={
            "layer": plan_layer,
            "elevation": 0.0,
            "extrusion": (0, 0, 1)
        }
    )

    # 지반선: X=측점(m), Y=표고(m)
    msp.add_lwpolyline(
        [(sta, elev, 0.0) for sta, elev in ground_points],
        format="xyb",
        dxfattribs={
            "layer": ground_layer,
            "elevation": 0.0,
            "extrusion": (0, 0, 1)
        }
    )

    output = Path(filename)
    output.parent.mkdir(parents=True, exist_ok=True)

    doc.saveas(str(output))

    print("=" * 55)
    print("[종단선형 테스트 DXF 생성 완료]")
    print(f"출력 파일: {output.resolve()}")
    print(
        f"계획선 범위: "
        f"{plan_points[0][0]:.2f} ~ "
        f"{plan_points[-1][0]:.2f}m"
    )
    print(
        f"지반선 범위: "
        f"{ground_points[0][0]:.2f} ~ "
        f"{ground_points[-1][0]:.2f}m"
    )
    print(f"계획선 좌표: {len(plan_points)}개")
    print(f"지반선 좌표: {len(ground_points)}개")
    print("=" * 55)

    return output


def main():
    parser = argparse.ArgumentParser(
        description="JSON 외부 주입형 종단선형 DXF 생성기"
    )

    parser.add_argument(
        "--config",
        default="profile_test_config.json",
        help="종단선형 조건 JSON 파일"
    )

    parser.add_argument(
        "--output",
        default="test_profile.dxf",
        help="출력 DXF 파일 경로"
    )

    args = parser.parse_args()

    config_path = Path(args.config)

    if not config_path.exists():
        raise FileNotFoundError(
            f"설정 파일을 찾을 수 없습니다: {config_path}"
        )

    with open(config_path, "r", encoding="utf-8-sig") as f:
        config = json.load(f)

    create_profile_dxf(
        plan_points=config["plan_points"],
        ground_points=config["ground_points"],
        filename=args.output
    )


if __name__ == "__main__":
    main()
