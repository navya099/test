import json
import trimesh
from shapely.geometry import Polygon
import numpy as np

# ==========================================
# 1. 입력 데이터 (지침서 기반 JSON)
# ==========================================
station_data = {
    "site": {"width": 150, "depth": 100},  # 대지 가로, 세로 (가정)
    "platform": {"count": 2, "width": 7.5, "length": 220.0},  # 승강장 지침서 (p.9)
    "station_building": {
        "target_area": 1091.11,  # 역사 연면적 지침서 (p.11)
        "floor_height": 4.5,  # 층고 (가정)
        "floors": 2
    }
}


# ==========================================
# 2. 3D 매스 생성 엔진 (부성역 형태 모사)
# ==========================================
def generate_buseong_station_mass(data):
    meshes = []

    # 2-1. 승강장 매스 생성 (상대식 2개)
    p_len = data["platform"]["length"]
    p_wid = data["platform"]["width"]
    p_h = 7.5  # 승강장 높이 (지면으로부터)

    # 승강장 1 (하행), 승강장 2 (상행) - 선로 폭 4m 간격으로 배치
    platform1 = trimesh.creation.box(extents=[p_len, p_wid, p_h])
    platform1.apply_translation([p_len / 2, - (p_wid / 2 + 2), p_h / 2])

    platform2 = trimesh.creation.box(extents=[p_len, p_wid, p_h])
    platform2.apply_translation([p_len / 2, (p_wid / 2 + 2), p_h / 2])

    meshes.extend([platform1, platform2])

    # 2-2. 역사 건물 매스 생성 (경사진 윙과 중앙 포털)
    # 부성역의 상징적인 삼각형/사다리꼴 단면 정의 (측면 프로파일)
    profile_coords = [
        (0, p_h),  # 승강장 위에서 시작
        (10, p_h + 10),  # 경사 상승 (지붕)
        (35, p_h + 10),  # 지붕 유지
        (45, p_h + 2),  # 오른쪽 경사 하강
        (45, p_h)  # 다시 승강장 높이로
    ]
    profile_poly = Polygon(profile_coords)

    # 단면을 선로 방향으로 압출 (역사 건물 길이 60m 가정)
    station_wing = trimesh.creation.extrude_polygon(profile_poly, height=60)
    station_wing.apply_translation([p_len / 2 - 30, -15, 0])  # 중앙에 배치

    # 중앙 포털 (삼각형 형태의 볼륨 추가)
    portal_profile = Polygon([(0, 0), (15, 25), (30, 0)])
    portal_mass = trimesh.creation.extrude_polygon(portal_profile, height=20)
    portal_mass.apply_translation([p_len / 2 - 10, -10, 0])

    # 윙과 포털 결합 (Boolean Union)
    # *참고: trimesh의 boolean 연산은 환경에 따라 에러가 날 수 있어 try-except 처리
    try:
        station_mass = station_wing.union(portal_mass)
    except Exception as e:
        print("Boolean 연산 오류, 단순 결합으로 대체:", e)
        station_mass = trimesh.util.concatenate([station_wing, portal_mass])

    meshes.append(station_mass)

    # 전체 씬(Scene) 결합 및 반환
    return trimesh.Scene(meshes), station_mass


# ==========================================
# 3. 회귀 검증 (Regression Validation) 모듈
# ==========================================
def validate_massing(scene, station_mass, data):
    print("\n--- [회귀 검증 시작] ---")

    # 검증 1: 승강장 치수 및 개수 검증
    platform_components = [m for m in scene.geometry.values() if m.extents[0] > 200]  # 길이가 200m 이상인 것
    assert len(platform_components) == 2, f"오류: 승강장은 2개여야 합니다. (현재: {len(platform_components)}개)"

    for p in platform_components:
        assert np.isclose(p.extents[0], data["platform"]["length"]), "오류: 승강장 길이가 지침서(220m)와 다릅니다."
        assert np.isclose(p.extents[1], data["platform"]["width"]), "오류: 승강장 폭이 지침서(7.5m)와 다릅니다."
    print("✅ 검증 1 통과: 승강장 규격(220m x 7.5m) 및 개수(2개) 일치")

    # 검증 2: 역사 건물의 위치 및 기하학적 관계 검증
    # 승강장의 Z축 최상단(p_h=7.5)보다 역사 건물이 더 높이 솟아있는지 확인
    station_max_z = station_mass.bounds[1][2]
    assert station_max_z > 7.5, f"오류: 역사 건물이 승강장 높이보다 높지 않습니다. (현재: {station_max_z}m)"
    print(f"✅ 검증 2 통과: 역사 건물이 승강장 상부에 적절히 배치됨 (최대 높이: {station_max_z:.1f}m)")

    # 검증 3: 대략적인 연면적(Volume) 기반 검증
    # 매스의 부피를 계산하여 타겟 연면적과 대략적으로 일치하는지 확인
    # (정확한 면적은 아니지만, 매스가 터무니없이 크거나 작은 것을 방지)
    volume = station_mass.volume
    target_area = data["station_building"]["target_area"] * data["station_building"]["floor_height"]

    # 부피 오차 범위 30% 허용 (형태적 특성 고려)
    assert 0.7 * target_area <= volume <= 1.3 * target_area, \
        f"오류: 역사 건물의 부피가 예상 범위를 벗어났습니다. (매스 부피: {volume:.1f}, 타겟: {target_area:.1f})"
    print(f"✅ 검증 3 통과: 건물 부피가 목표 연면적 대비 허용 오차 범위 내에 있음")

    print("--- [회귀 검증 성공: 모든 조건 만족] ---\n")


# ==========================================
# 4. 메인 실행부
# ==========================================
if __name__ == "__main__":
    # 1) 매스 생성
    scene, final_station_mass = generate_buseong_station_mass(station_data)

    # 2) 회귀 검증 실행
    validate_massing(scene, final_station_mass, station_data)

    # 3) 결과물 저장 (GLB 파일 - 웹 브라우저나 3D 뷰어에서 확인 가능)
    scene.export("buseong_station_validated.glb")
    print("💾 결과물이 'buseong_station_validated.glb'로 저장되었습니다. (3D 뷰어로 열어보세요)")