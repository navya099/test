from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

import ezdxf


@dataclass
class RoomSpec:
    name: str
    area: float


@dataclass
class ZoneSpec:
    zone_key: str
    layer_name: str
    height: float
    rooms: List[RoomSpec] = field(default_factory=list)

    @property
    def total_area(self) -> float:
        return sum(r.area for r in self.rooms)


@dataclass
class RoofCurveParams:
    arch_rise: float = 2.4        # 곡선 지붕 중앙 상승고(m)
    overhang_x: float = 3.0       # X방향(횡단) 처마 돌출(m)
    overhang_y: float = 4.0       # Y방향(선로/연결통로 측) 처마 돌출(m)
    segments_u: int = 24          # 횡단 분절 수
    segments_v: int = 16          # 종단 분절 수


@dataclass
class BuseongProjectSpec:
    project_name: str = "수도권전철 부성역사 신축 설계공모"
    site_area: float = 22500.0
    target_gfa: float = 1091.11
    gfa_tolerance: float = 0.10
    platform_width: float = 7.5
    platform_length: float = 220.0
    platform_count: int = 2
    overpass_area: float = 450.0
    expansion_ratio: float = 0.35
    zones: Dict[str, ZoneSpec] = field(default_factory=dict)
    roof: RoofCurveParams = field(default_factory=RoofCurveParams)

    @classmethod
    def default_buseong(cls) -> "BuseongProjectSpec":
        zones = {
            "여객시설": ZoneSpec(
                zone_key="여객시설",
                layer_name="MASS_PASSENGER",
                height=6.2,
                rooms=[
                    RoomSpec("콘코스 및 대합실", 211.30),
                    RoomSpec("여객화장실", 139.47),
                    RoomSpec("수유실", 15.00),
                ],
            ),
            "역무시설": ZoneSpec(
                zone_key="역무시설",
                layer_name="MASS_STAFF",
                height=4.0,
                rooms=[
                    RoomSpec("역무실", 30.00),
                    RoomSpec("자동발매기실", 10.00),
                    RoomSpec("침실(3개)", 43.74),
                    RoomSpec("탕비실", 12.00),
                    RoomSpec("공익요원/환경관리원실", 18.00),
                    RoomSpec("창고", 20.00),
                    RoomSpec("쓰레기수거장", 12.00),
                ],
            ),
            "지원시설": ZoneSpec(
                zone_key="지원시설",
                layer_name="MASS_UTILITY",
                height=4.5,
                rooms=[
                    RoomSpec("통신기기실", 50.00),
                    RoomSpec("역무통신실", 35.00),
                    RoomSpec("통신전원실", 20.00),
                    RoomSpec("전기실", 170.00),
                    RoomSpec("기계실", 100.00),
                ],
            ),
            "교통면적": ZoneSpec(
                zone_key="교통면적",
                layer_name="MASS_CIRCULATION",
                height=4.5,
                rooms=[
                    RoomSpec("교통 및 공용", 204.60),
                ],
            ),
        }
        return cls(zones=zones)

    @property
    def planned_gfa(self) -> float:
        return sum(z.total_area for z in self.zones.values())

    @property
    def min_allowed_gfa(self) -> float:
        return self.target_gfa * (1.0 - self.gfa_tolerance)

    @property
    def max_allowed_gfa(self) -> float:
        return self.target_gfa * (1.0 + self.gfa_tolerance)

    @property
    def platform_total_area(self) -> float:
        return self.platform_width * self.platform_length * self.platform_count


def validate_areas(spec: BuseongProjectSpec) -> dict:
    gfa = spec.planned_gfa
    diff = gfa - spec.target_gfa
    diff_pct = (diff / spec.target_gfa) * 100.0 if spec.target_gfa else 0.0
    within_tol = spec.min_allowed_gfa <= gfa <= spec.max_allowed_gfa

    zone_breakdown = {
        k: {
            "area_m2": round(v.total_area, 2),
            "share_pct": round((v.total_area / gfa) * 100.0, 2) if gfa else 0.0,
            "rooms": {r.name: r.area for r in v.rooms},
        }
        for k, v in spec.zones.items()
    }

    report = {
        "project": spec.project_name,
        "site_area_m2": spec.site_area,
        "target_gfa_m2": spec.target_gfa,
        "allowed_gfa_range_m2": [
            round(spec.min_allowed_gfa, 2),
            round(spec.max_allowed_gfa, 2),
        ],
        "planned_gfa_m2": round(gfa, 2),
        "diff_m2": round(diff, 2),
        "diff_pct": round(diff_pct, 2),
        "within_10pct_tolerance": within_tol,
        "platform_total_area_m2": spec.platform_total_area,
        "overpass_area_m2": spec.overpass_area,
        "zones": zone_breakdown,
    }
    return report


def _add_box_3d(
    msp,
    layer: str,
    x0: float,
    y0: float,
    z0: float,
    dx: float,
    dy: float,
    dz: float,
) -> None:
    """직육면체 6면을 3DFACE로 생성하여 3D 뷰어/CAD에서 입체 확인 가능하게 함."""
    x1, y1, z1 = x0 + dx, y0 + dy, z0 + dz
    p000 = (x0, y0, z0)
    p100 = (x1, y0, z0)
    p110 = (x1, y1, z0)
    p010 = (x0, y1, z0)

    p001 = (x0, y0, z1)
    p101 = (x1, y0, z1)
    p111 = (x1, y1, z1)
    p011 = (x0, y1, z1)

    faces = [
        (p000, p010, p110, p100),  # 바닥
        (p001, p101, p111, p011),  # 천장
        (p000, p100, p101, p001),  # 전면(-Y)
        (p100, p110, p111, p101),  # 우측(+X)
        (p110, p010, p011, p111),  # 후면(+Y)
        (p010, p000, p001, p011),  # 좌측(-X)
    ]
    for f in faces:
        msp.add_3dface(f, dxfattribs={"layer": layer})


def _add_curved_roof_3d(
    msp,
    layer: str,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    z_base: float,
    rise: float,
    nu: int,
    nv: int,
) -> None:
    """포물선 아치형 곡선 지붕 메쉬(3DFACE 그리드) 생성."""
    cx = 0.5 * (x_min + x_max)
    half_w = max(0.5 * (x_max - x_min), 1e-6)

    grid: List[List[Tuple[float, float, float]]] = []
    for i in range(nu + 1):
        u = i / nu
        x = x_min + u * (x_max - x_min)
        norm_x = (x - cx) / half_w  # -1 ~ +1
        # 중앙(norm_x=0)에서 rise만큼 솟는 부드러운 아치 곡선
        arch_z = z_base + rise * max(0.0, 1.0 - norm_x**2)
        row = []
        for j in range(nv + 1):
            v = j / nv
            y = y_min + v * (y_max - y_min)
            row.append((x, y, arch_z))
        grid.append(row)

    for i in range(nu):
        for j in range(nv):
            p1 = grid[i][j]
            p2 = grid[i + 1][j]
            p3 = grid[i + 1][j + 1]
            p4 = grid[i][j + 1]
            msp.add_3dface([p1, p2, p3, p4], dxfattribs={"layer": layer})


def build_buseong_dxf(
    spec: BuseongProjectSpec,
    output_dxf: Path,
    concourse_z0: float = 12.0,
    concourse_width_y: float = 16.0,
) -> Tuple[Path, dict]:
    """
    부성역 선상역사 기준 매스 및 지붕/승강장/연결통로/장래확장 매스를 DXF로 생성.
    좌표계 관례:
      - Y축: 선로 진행 방향(길이 220m 승강장 기준 -110 ~ +110)
      - X축: 선로 횡단 방향(상대식 2홈 2선 및 선상역사 폭)
      - Z축: 표고(m), 선상역사 바닥은 concourse_z0부터 시작
    """
    report = validate_areas(spec)

    doc = ezdxf.new(setup=True)
    msp = doc.modelspace()

    layer_colors = {
        "MASS_PASSENGER": 3,     # 녹색
        "MASS_STAFF": 5,         # 청색
        "MASS_UTILITY": 1,       # 적색
        "MASS_CIRCULATION": 4,   # 청록색
        "ROOF_CURVE": 2,         # 황색
        "INFRA_PLATFORM": 8,     # 회색
        "INFRA_OVERPASS": 6,     # 자주색
        "EXPANSION_GHOST": 7,    # 백/흑색
    }
    for lname, col in layer_colors.items():
        if lname not in doc.layers:
            doc.layers.add(name=lname, color=col)

    # 1. 고정 인프라: 상대식 승강장 2개소(좌/우) 및 선상연결통로
    plat_z0 = concourse_z0 - 5.5
    plat_thickness = 1.1
    plat_y0 = -0.5 * spec.platform_length
    # 선로 폭 여유(예: 12m)를 두고 좌·우 승강장 배치
    left_plat_x0 = -6.0 - spec.platform_width
    right_plat_x0 = 6.0

    _add_box_3d(
        msp,
        "INFRA_PLATFORM",
        left_plat_x0,
        plat_y0,
        plat_z0,
        spec.platform_width,
        spec.platform_length,
        plat_thickness,
    )
    _add_box_3d(
        msp,
        "INFRA_PLATFORM",
        right_plat_x0,
        plat_y0,
        plat_z0,
        spec.platform_width,
        spec.platform_length,
        plat_thickness,
    )

    # 선상연결통로 (450 m2 기준, 콘코스 측변에 길게 연결)
    overpass_w = 6.0
    overpass_len = spec.overpass_area / overpass_w
    _add_box_3d(
        msp,
        "INFRA_OVERPASS",
        left_plat_x0,
        -0.5 * overpass_len,
        concourse_z0 - 0.6,
        overpass_w,
        overpass_len,
        0.6,
    )

    # 2. 역사 기능 클러스터별 매스 배치 (선상역사 상부 기준)
    # 여객시설(365.77 m2)을 중심으로 좌측에 역무시설(145.74 m2), 우측에 지원시설(375.00 m2) 배치
    pass_zone = spec.zones["여객시설"]
    staff_zone = spec.zones["역무시설"]
    util_zone = spec.zones["지원시설"]
    circ_zone = spec.zones["교통면적"]

    pass_dx = pass_zone.total_area / concourse_width_y
    pass_x0 = -0.5 * pass_dx
    pass_y0 = -0.5 * concourse_width_y

    _add_box_3d(
        msp,
        pass_zone.layer_name,
        pass_x0,
        pass_y0,
        concourse_z0,
        pass_dx,
        concourse_width_y,
        pass_zone.height,
    )

    # 역무시설(인접 클러스터): 여객 블록 좌측(-X)에 연접 배치
    staff_dx = staff_zone.total_area / concourse_width_y
    staff_x0 = pass_x0 - staff_dx
    _add_box_3d(
        msp,
        staff_zone.layer_name,
        staff_x0,
        pass_y0,
        concourse_z0,
        staff_dx,
        concourse_width_y,
        staff_zone.height,
    )

    # 지원시설(전기·기계·통신 375 m2): 여객 블록 우측(+X)에 분절 매스로 배치
    util_dx = util_zone.total_area / concourse_width_y
    util_x0 = pass_x0 + pass_dx
    _add_box_3d(
        msp,
        util_zone.layer_name,
        util_x0,
        pass_y0,
        concourse_z0,
        util_dx,
        concourse_width_y,
        util_zone.height,
    )

    # 교통 및 공용(204.60 m2): 콘코스 후면(+Y)에 코어/동선 버퍼 블록으로 배치
    circ_dy = circ_zone.total_area / max(pass_dx, 1.0)
    circ_y0 = pass_y0 + concourse_width_y
    _add_box_3d(
        msp,
        circ_zone.layer_name,
        pass_x0,
        circ_y0,
        concourse_z0,
        pass_dx,
        circ_dy,
        circ_zone.height,
    )

    # 3. 곡선 지붕(ROOF_CURVE) 생성
    max_top_z = concourse_z0 + max(
        pass_zone.height,
        staff_zone.height,
        util_zone.height,
        circ_zone.height,
    )
    roof_x_min = min(staff_x0, pass_x0) - spec.roof.overhang_x
    roof_x_max = max(pass_x0 + pass_dx, util_x0 + util_dx) + spec.roof.overhang_x
    roof_y_min = pass_y0 - spec.roof.overhang_y
    roof_y_max = max(pass_y0 + concourse_width_y, circ_y0 + circ_dy) + spec.roof.overhang_y

    _add_curved_roof_3d(
        msp,
        "ROOF_CURVE",
        x_min=roof_x_min,
        x_max=roof_x_max,
        y_min=roof_y_min,
        y_max=roof_y_max,
        z_base=max_top_z + 0.5,
        rise=spec.roof.arch_rise,
        nu=spec.roof.segments_u,
        nv=spec.roof.segments_v,
    )

    # 4. 장래 확장(증축) 예약 볼륨(EXPANSION_GHOST)
    exp_area = spec.planned_gfa * spec.expansion_ratio
    exp_dx = exp_area / concourse_width_y
    exp_x0 = util_x0 + util_dx + 2.0
    _add_box_3d(
        msp,
        "EXPANSION_GHOST",
        exp_x0,
        pass_y0,
        concourse_z0,
        exp_dx,
        concourse_width_y,
        pass_zone.height,
    )

    output_dxf.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(output_dxf)
    return output_dxf, report


if __name__ == "__main__":
    spec = BuseongProjectSpec.default_buseong()
    dxf_path, summary = build_buseong_dxf(
        spec=spec,
        output_dxf=Path("output/buseong_station_mass_3d.dxf"),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nDXF 생성 완료: {dxf_path.resolve()}")