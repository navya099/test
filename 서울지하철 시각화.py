import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Point
from geopandas import GeoDataFrame
import ezdxf
import pyproj
from matplotlib.widgets import CheckButtons

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 경위도 좌표를 TM 좌표로 변환하는 함수 (좌표배열)
def calc_latlon2TM_array(coords_array):
    # Define CRS
    p1_type = pyproj.CRS.from_epsg(4326)  # 위도경도 (WGS84)
    p2_type = pyproj.CRS.from_epsg(5186)  # TM 좌표계 (Korea 2000 / Unified CS)

    # Create transformer
    transformer = pyproj.Transformer.from_crs(p1_type, p2_type, always_xy=True)

    # Transform coordinates
    transformed_coords = [transformer.transform(x, y) for x, y in coords_array]
    return transformed_coords

# 경로 설정 및 데이터 불러오기
cur_path = 'C:/Users/KDB/Documents/'

subway_crd = pd.read_csv(cur_path + '서울교통공사_1_8호선 역사 좌표(위경도) 정보_20231031.csv', encoding='cp949')
subway_level = pd.read_csv(cur_path + '서울교통공사_역사심도정보_20240331.csv', encoding='cp949')
subway_chain = pd.read_csv(cur_path + '서울교통공사 역간거리 및 소요시간_240810.csv', encoding='cp949')

# 필요한 열 추출
subway_level = subway_level[['호선', '역명', '레일면고']]
subway_crd = subway_crd[['호선', '역명', '위도', '경도']]
subway_chain = subway_chain[['호선', '역명', '호선별누계(km)']]

# 열 이름 변경
subway_crd.rename(columns={'위도': 'y', '경도': 'x'}, inplace=True)

# 위도 경도 TM 좌표 변환
coords_array = subway_crd[['x', 'y']].values
transformed_coords = calc_latlon2TM_array(coords_array)
subway_crd[['x', 'y']] = np.array(transformed_coords)

# 데이터 병합
subway_info = pd.merge(subway_crd, subway_level, on=['호선', '역명'], how='inner')
subway_info = pd.merge(subway_info, subway_chain, on=['호선', '역명'], how='inner')

# GeoDataFrame으로 변환
subway_info['geometry'] = subway_info.apply(lambda row: Point(row['x'], row['y']), axis=1)
subway_info_gdf = GeoDataFrame(subway_info, crs='EPSG:4326', geometry='geometry')
subway_info_gdf['z'] = subway_info_gdf['레일면고']  # z값 추가

# 호선별 색상 지정
line_colors = {
    '1': 'blue',
    '2': 'green',
    '3': 'orange',
    '4': 'skyblue',
    '5': 'purple',
    '6': 'yellow',
    '7': 'magenta',
    '8': 'pink'
}

# 2D 시각화
# Initialize the plot
fig = plt.figure(figsize=(8,6))  # 가로 800픽셀, 세로 600픽셀 크기의 도표 생성
ax = fig.add_subplot(2,1,1)
ax2 = fig.add_subplot(2,1,2)

# 각 호선별로 시각화
for line, group in subway_info_gdf.groupby('호선'):
    color = line_colors.get(line, 'gray')  # 기본 색상은 회색
    ax.plot(group['x'], group['y'], marker='o', linestyle='-', label=f'Line {line}', color=color)
    scatter = ax.scatter(group['x'], group['y'], c=group['z'], cmap='viridis', s=50, edgecolor='k', alpha=0.75, zorder=5)

    for i in range(len(group)):
        ax.text(group.iloc[i]['x'], group.iloc[i]['y'], group.iloc[i]['역명'], fontsize=9, ha='right', va='bottom')


def plot_elevation(selected_lines):
    print(f"Selected lines: {selected_lines}")  # 선택된 호선 출력
    ax2.clear()  # 그래프 초기화
    for line in selected_lines:
        group = subway_info_gdf[subway_info_gdf['호선'].astype(str) == str(line)]  # 선택된 호선에 대해 데이터 필터링
        color = line_colors.get(line, 'gray')  # 해당 호선의 색상 가져오기

        if not group.empty:
            #print(group)  # 필터링된 데이터 출력

            # 종단면도 시각화
            ax2.plot(group['호선별누계(km)'], group['z'], marker='o', linestyle='-', label=f'Line {line}', color=color)
            scatter = ax2.scatter(group['호선별누계(km)'], group['z'], c=group['z'], cmap='viridis', s=50, edgecolor='k', alpha=0.75, zorder=5)

            # 각 역명 추가
            for i in range(len(group)):
                ax2.text(group.iloc[i]['호선별누계(km)'], group.iloc[i]['z'], group.iloc[i]['역명'], fontsize=9, ha='right', va='bottom')

    ax2.set_xlabel('Chainage (km)')
    ax2.set_ylabel('Elevation (m)')
    ax2.set_title('Elevation Profile of Selected Subway Lines')
    ax2.legend()
    ax2.grid(True)
    plt.draw()  # 그래프 업데이트

    

def on_check(label):
    selected_lines = [line for line in line_colors.keys() if check.get_status()[lines_available.index(line)]]
    if len(selected_lines) > 2:
        print("You can select up to 2 lines.")
        selected_lines = selected_lines[:2]  # 첫 2개의 라인만 사용
    plot_elevation(selected_lines)

# 체크박스 생성
lines_available = list(line_colors.keys())
initial_lines = lines_available[:1]  # 초기에는 첫 번째 호선 선택

# CheckButtons의 크기를 조절하기 위해 plt.axes 크기 수정
check = CheckButtons(plt.axes([0.05, 0.4, 0.15, 0.45]), lines_available, [line in initial_lines for line in lines_available])
# 이벤트 핸들러 연결
check.on_clicked(on_check)

# 레이블 및 제목 추가
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_title('2D Visualization of Seoul Subway Lines with Custom Colors')
ax.set_aspect('equal', adjustable='box')
ax.grid(True)
plt.show()
