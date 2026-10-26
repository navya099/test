from Profile.profile import Profile

def test_profile():
    # 1. Profile 생성
    profile = Profile("Test Route")

    # 2. PVI 데이터 추가 (예: 단순 종단 구배)
    # station 0.0 = 고도 100.0
    # station 500.0 = 고도 102.5
    # station 1000.0 = 고도 105.0
    profile.pvis.add_pvi(station=0.0, elevation=106.9)
    profile.pvis.add_pvi(station=925, elevation=102.5)
    profile.pvis.add_pvi(station=1567, elevation=115)

    # 3. 기본 속성 출력
    print(f"Profile name: {profile.name}")
    print(f"Start station: {profile.start_station}")
    print(f"End station: {profile.end_station}")
    print(f"Length: {profile.length}")
    print(f"Max elevation: {profile.max_elevation}")
    print(f"Min elevation: {profile.min_elevation}")

    # 4. 구배 정보 확인
    print(f"Max slope: {profile.max_slope}")
    print(f"Min slope: {profile.min_slope}")

    # 5. 임의 station에서 고도 확인 (보간 테스트)
    for sta in [0, 250, 500, 750, 1000]:
        elev = profile.elevation_at_station(sta)
        print(f"Station {sta:.1f} → Elevation {elev:.2f}")

if __name__ == "__main__":
    test_profile()
