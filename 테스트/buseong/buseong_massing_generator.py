"""
철도역사 설계공모(부성역사) JSON 입력 기반 3D 매스 볼륨 자동 생성 프로토타입
- Rhino 8 Python 3 / GhPython 환경에서는 Rhino.Geometry.Box 및 Brep으로 직접 변환 가능
- 일반 Python 환경에서는 3D 바운딩 박스 좌표 및 OBJ 파일로 내보내어 즉시 검증 가능
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import Rhino.Geometry as rg  # type: ignore
    HAS_RHINO = True
except ImportError:
    HAS_RHINO = False


@dataclass
class MassBox:
    name: str
    category: str
    role: str  # "fixed_platform" | "clearance_envelope" | "bridge_spine" | "program_zone" | "expansion_bay"
    x: float   # 중심 또는 최소 X (m, 선로 직교 방향)
    y: float   # 최소 Y (m, 선로 진행 방향)
    z: float   # 바닥 레벨 Z (m)
    dx: float  # 폭 (m)
    dy: float  # 길이 (m)
    dz: float  # 높이 (m)
    area_m2: float
    immutable: bool = False

    def to_rhino_box(self) -> Any:
        if not HAS_RHINO:
            return None
        interval_x = rg.Interval(self.x, self.x + self.dx)
        interval_y = rg.Interval(self.y, self.y + self.dy)
        interval_z = rg.Interval(self.z, self.z + self.dz)
        return rg.Box(rg.Plane.WorldXY, interval_x, interval_y, interval_z)


def generate_buseong_massing(
    data: Dict[str, Any],
    track_corridor_width: float = 10.0,
    track_clearance_height: float = 6.5,
    slab_thickness: float = 0.7,
    station_floor_height: float = 4.5,
    bridge_width_x: float = 28.0,
) -> Dict[str, Any]:
    """
    buseong_station_input.json 데이터를 받아 고정 승강장 제약 및 조닝별 3D 매스 생성.
    좌표계:
      - X축: 선로 직교 방향 (동측 부성지구 = +X, 서측 = -X)
      - Y축: 선로 진행 방향 (승강장 길이 방향, 중앙 Y=0 기준)
      - Z축: 높이 (레일면 EL = 0.0m 기준)
    """
    boxes: List[MassBox] = []

    # 1. 고정 하부 제약: 상대식 승강장(2홈 2선) 및 선로 건축한계
    plat = data["fixed_structures"]["platforms"]
    p_len = float(plat["length_m"])
    p_wid = float(plat["width_m"])
    p_area = float(plat["total_area_m2"])
    p_immutable = bool(plat["immutable"])
    y_start = -p_len / 2.0

    # 선로 건축한계 제외 영역 (상부 매스 침범 불가 볼륨)
    boxes.append(
        MassBox(
            name="Track_Clearance_Envelope",
            category="fixed_constraint",
            role="clearance_envelope",
            x=-track_corridor_width / 2.0,
            y=y_start,
            z=0.0,
            dx=track_corridor_width,
            dy=p_len,
            dz=track_clearance_height,
            area_m2=track_corridor_width * p_len,
            immutable=True,
        )
    )

    # 서측(-X) / 동측(+X) 상대식 승강장
    west_x = -(track_corridor_width / 2.0 + p_wid)
    east_x = track_corridor_width / 2.0
    for idx, px in enumerate([west_x, east_x], start=1):
        boxes.append(
            MassBox(
                name=f"Platform_{idx}_{'West' if idx == 1 else 'East'}",
                category="fixed_platform",
                role="fixed_platform",
                x=px,
                y=y_start,
                z=0.0,
                dx=p_wid,
                dy=p_len,
                dz=1.1,
                area_m2=p_area / 2.0,
                immutable=p_immutable,
            )
        )

    # 2. 선상 데크 기준 레벨 및 코어(연결통로) 배치
    deck_z = track_clearance_height + slab_thickness  # 7.2m
    corridor_area = float(data["fixed_structures"]["overpass_corridor"]["area_m2"])
    total_span_x = track_corridor_width + 2 * p_wid + 6.0  # 양측 승강장 + 외측 진입부 포함
    corridor_depth_y = corridor_area / total_span_x

    boxes.append(
        MassBox(
            name="Overpass_Corridor_Spine",
            category="circulation_bridge",
            role="bridge_spine",
            x=-total_span_x / 2.0,
            y=-corridor_depth_y / 2.0,
            z=deck_z,
            dx=total_span_x,
            dy=corridor_depth_y,
            dz=station_floor_height,
            area_m2=round(corridor_area, 2),
            immutable=False,
        )
    )

    # 3. 역사 연면적 조닝별 3D 매스 할당 (1,091.11㎡)
    categories = {c["category_id"]: c for c in data["space_program"]["categories"]}

    # (a) 여객시설 (365.77㎡) + 교통면적(204.60㎡) -> 동측(부성지구) 전면 중앙 콘코스 배치
    passenger_area = float(categories["passenger"]["subtotal_m2"])
    circulation_area = float(categories["circulation"]["subtotal_m2"])
    concourse_total = passenger_area + circulation_area

    concourse_dy = concourse_total / bridge_width_x
    concourse_x = -bridge_width_x / 2.0
    concourse_y = corridor_depth_y / 2.0  # 연결통로 북측(+Y) 인접

    boxes.append(
        MassBox(
            name="Zone_Passenger_Concourse",
            category="passenger",
            role="program_zone",
            x=concourse_x,
            y=concourse_y,
            z=deck_z,
            dx=bridge_width_x,
            dy=passenger_area / bridge_width_x,
            dz=station_floor_height,
            area_m2=passenger_area,
        )
    )

    boxes.append(
        MassBox(
            name="Zone_Circulation_Core",
            category="circulation",
            role="program_zone",
            x=concourse_x,
            y=concourse_y + (passenger_area / bridge_width_x),
            z=deck_z,
            dx=bridge_width_x,
            dy=circulation_area / bridge_width_x,
            dz=station_floor_height,
            area_m2=circulation_area,
        )
    )

    # (b) 역무시설 (145.74㎡) -> 보안·관리 효율을 위해 여객 존과 인접한 동측(+X) 클러스터 배치
    ops_area = float(categories["operations"]["subtotal_m2"])
    ops_dx = 12.0
    ops_dy = ops_area / ops_dx
    boxes.append(
        MassBox(
            name="Zone_Operations_Cluster",
            category="operations",
            role="program_zone",
            x=concourse_x + bridge_width_x,
            y=concourse_y,
            z=deck_z,
            dx=ops_dx,
            dy=ops_dy,
            dz=station_floor_height,
            area_m2=ops_area,
        )
    )

    # (c) 지원시설 MEP (375.00㎡) -> 소음·하중 분리를 위해 서측(-X) 설비 존 배치
    mep_area = float(categories["support_mep"]["subtotal_m2"])
    mep_dx = 15.0
    mep_dy = mep_area / mep_dx
    boxes.append(
        MassBox(
            name="Zone_Support_MEP",
            category="support_mep",
            role="program_zone",
            x=concourse_x - mep_dx,
            y=-mep_dy / 2.0,
            z=deck_z,
            dx=mep_dx,
            dy=mep_dy,
            dz=station_floor_height,
            area_m2=mep_area,
        )
    )

    # 4. 장래 확장(증축) 고려 예비 그리드 (Bay)
    if data["design_and_performance_rules"]["expandability"]["future_extension_required"]:
        exp_dx = bridge_width_x
        exp_dy = 8.0  # 1 스팬(8m) 확장 예비 영역
        boxes.append(
            MassBox(
                name="Future_Expansion_Bay",
                category="expandability",
                role="expansion_bay",
                x=concourse_x,
                y=concourse_y + concourse_dy,
                z=deck_z,
                dx=exp_dx,
                dy=exp_dy,
                dz=station_floor_height,
                area_m2=exp_dx * exp_dy,
            )
        )

    # 5. 면적 허용 오차 검증 (±10%)
    target = float(data["space_program"]["total_target_area_m2"])
    tol = float(data["space_program"]["area_tolerance_ratio"])
    generated_station_area = sum(
        b.area_m2 for b in boxes if b.role == "program_zone"
    )
    min_allowed = target * (1.0 - tol)
    max_allowed = target * (1.0 + tol)
    is_valid = min_allowed <= generated_station_area <= max_allowed

    return {
        "project": data["project_meta"]["title"],
        "station_type": data["project_meta"]["station_type"],
        "validation": {
            "target_area_m2": target,
            "generated_area_m2": round(generated_station_area, 2),
            "allowed_range_m2": [round(min_allowed, 2), round(max_allowed, 2)],
            "within_tolerance": is_valid,
        },
        "boxes": [asdict(b) for b in boxes],
        "rhino_geometries": [b.to_rhino_box() for b in boxes] if HAS_RHINO else None,
    }


def export_obj(boxes: List[Dict[str, Any]], output_path: Path) -> None:
    """Rhino/Blender/웹 뷰어에서 바로 열 수 있는 간단한 3D OBJ 파일 내보내기."""
    lines = ["# Buseong Station Parametric Massing Prototype"]
    v_offset = 1
    for b in boxes:
        x0, y0, z0 = b["x"], b["y"], b["z"]
        x1, y1, z1 = x0 + b["dx"], y0 + b["dy"], z0 + b["dz"]
        lines.append(f"o {b['name']}")
        verts = [
            (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
            (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
        ]
        for vx, vy, vz in verts:
            lines.append(f"v {vx:.3f} {vy:.3f} {vz:.3f}")
        faces = [
            (0, 3, 2, 1), (4, 5, 6, 7),
            (0, 1, 5, 4), (1, 2, 6, 5),
            (2, 3, 7, 6), (3, 0, 4, 7),
        ]
        for f0, f1, f2, f3 in faces:
            lines.append(
                f"f {v_offset+f0} {v_offset+f1} {v_offset+f2} {v_offset+f3}"
            )
        v_offset += 8
    output_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    input_path = Path("buseong_station_input.json")
    with input_path.open("r", encoding="utf-8") as f:
        station_data = json.load(f)

    result = generate_buseong_massing(station_data)
    print(json.dumps(result["validation"], ensure_ascii=False, indent=2))
    print(f"Generated {len(result['boxes'])} 3D massing volumes.")

    export_obj(result["boxes"], Path("buseong_massing_preview.obj"))