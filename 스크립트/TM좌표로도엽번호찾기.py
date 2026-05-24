import geopandas as gpd
from shapely.geometry import box


def find_5k_sheets_by_tm_bbox(shp_path, min_x, min_y, max_x, max_y):
    """
    사용자가 입력한 TM 중부원점(EPSG:5186) 범위 내에 포함되는 1:5,000 도엽 정보를 조회합니다.
    디버그용으로 입력 좌표의 WGS84 위경도 변환값을 함께 화면에 표시합니다.
    """
    # 1. 입력받은 TM bounding box를 기반으로 임시 GeoDataFrame 생성 (EPSG:5186 지정)
    input_box = box(min_x, min_y, max_x, max_y)
    gdf_input = gpd.GeoDataFrame(geometry=[input_box], crs="EPSG:5186")

    # 2. 디버그를 위해 입력받은 TM 영역을 WGS84 위경도(EPSG:4326)로 변환
    gdf_input_wgs84 = gdf_input.to_crs(epsg=4326)
    bounds_wgs84 = gdf_input_wgs84.geometry.iloc[0].bounds  # (minx, miny, maxx, maxy)

    # 3. 위경도 디버그 메시지 출력
    print("\n" + "=" * 60)
    print("[디버그] 입력 좌표 정보 (WGS84 위경도 변환값)")
    print(f" - 좌하단 (최소 경도, 최소 위도): {bounds_wgs84[0]:.6f}, {bounds_wgs84[1]:.6f}")
    print(f" - 우상단 (최대 경도, 최대 위도): {bounds_wgs84[2]:.6f}, {bounds_wgs84[3]:.6f}")
    print("=" * 60)

    print("\n전국 인덱스 SHP 파일을 불러오는 중입니다. 잠시만 기다려주세요...")
    gdf = gpd.read_file(shp_path, encoding='cp949')

    # SHP 파일의 원래 기준 좌표계 설정
    gdf.crs = "EPSG:5174"

    # 4. 공간 연산을 위해 입력 영역(input_box)을 SHP 파일 좌표계(EPSG:5174)로 변환
    gdf_search_target = gdf_input.to_crs(gdf.crs)
    search_area_converted = gdf_search_target.geometry.iloc[0]

    # 5. 공간 교차(Intersects) 필터링 연산
    matched = gdf[gdf.geometry.intersects(search_area_converted)]

    if matched.empty:
        print("\n[안내] 입력하신 TM 좌표 영역 안에 포함되는 도엽이 없습니다.")
        print("💡 팁: 도엽이 나오지 않는다면 SHP 파일의 원본 좌표계가 다를 수 있습니다.")
        print("   현재 지정된 `gdf.crs = 'EPSG:5174'`를 'EPSG:5179'나 'EPSG:5186'으로 변경해 보세요.")
        return None

    # 6. 도엽코드 기준 정렬
    matched_sorted = matched.sort_values(by='MAP_NUM')

    print(f"\n[조회 완료] 검색 영역 내에 총 {len(matched_sorted)}개의 도엽이 발견되었습니다.")
    print("-" * 50)
    print(f"{'도엽코드 (MAP_NUM)':<18} | {'도엽명 (MAP_NAM)':<20}")
    print("-" * 50)

    for _, row in matched_sorted.iterrows():
        print(f"{row['MAP_NUM']:<18} | {row['MAP_NAM']:<20}")

    return matched_sorted


# --- 실행 영역 ---
if __name__ == "__main__":
    # 고정된 인덱스 파일 경로
    SHP_FILE_PATH = r"E:\백업\C\download230817\Compressed\indexmap\c5000.SHP"

    print("=== 1:5,000 수치지도 영역별 인덱스 검색 프로그램 ===")
    print("원하시는 관심 영역의 TM좌표(EPSG:5186)를 차례대로 입력해주세요.")
    print("(값을 입력하지 않고 엔터를 치면 예시 좌표로 자동 검색됩니다.)\n")

    try:
        # input()으로 받은 문자열을 float(실수) 형태로 변환합니다.
        try:
            min_x = float(input("1. 최소 X (예: 200000): "))
            min_y = float(input("2. 최소 Y (예: 500000): "))
            max_x = float(input("3. 최대 X (예: 210000): "))
            max_y = float(input("4. 최대 Y (예: 510000): "))
        except ValueError:
            # 사용자가 엔터를 쳤을 때 매핑될 예시 좌표
            print("\n[안내] 입력값이 없어 기본 예시 좌표로 검색을 진행합니다.")
            min_x = 207478
            min_y = 476116
            max_x = 207713
            max_y = 476448

        # 데이터 유효성 검사 (최소값이 최대값보다 크면 에러 처리)
        if min_x >= max_x or min_y >= max_y:
            print("\n[오류] 최소 좌표 값은 최대 좌표 값보다 작아야 합니다. 다시 확인해주세요.")
        else:
            # 함수 호출
            find_5k_sheets_by_tm_bbox(SHP_FILE_PATH, min_x, min_y, max_x, max_y)

    except FileNotFoundError:
        print(f"\n[오류] 지정한 경로에서 SHP 파일을 찾을 수 없습니다.\n경로를 확인하세요: {SHP_FILE_PATH}")
    except Exception as e:
        print(f"\n오류가 발생했습니다: {e}")
