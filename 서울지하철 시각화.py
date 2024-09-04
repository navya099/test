import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Point
from geopandas import GeoDataFrame
import ezdxf
import pyproj
from matplotlib.widgets import CheckButtons
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

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
subway_level = subway_level[['호선', '역명', '층수', '형식', '레일면고']]
subway_crd = subway_crd[['호선', '역명', '위도', '경도']]
subway_chain = subway_chain[['호선', '역명', '호선별누계(km)']]

# 열 이름 변경
subway_crd.rename(columns={'위도': 'y', '경도': 'x'}, inplace=True)

# 호선 열의 데이터 타입을 문자열로 변환
subway_crd['호선'] = subway_crd['호선'].astype(str)
subway_level['호선'] = subway_level['호선'].astype(str)
subway_chain['호선'] = subway_chain['호선'].astype(str)

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
    '6': 'brown',
    '7': 'olive',
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
    selected_lines = [line for line in lines_available if check.get_status()[lines_available.index(line)]]
    if len(selected_lines) > 2:
        print("You can select up to 2 lines.")
        selected_lines = selected_lines[:2]  # 첫 2개의 라인만 사용
    plot_elevation(selected_lines)

# DXF 파일로 저장하기 위한 함수
#for line, group in subway_info_gdf.groupby('호선'):
def save_polylines_to_dxf(filename, lines, texts, solids):
    doc = ezdxf.new()
    msp = doc.modelspace()
    doc.styles.add("굴림체", font="gulim.ttc")
    # 레이어 추가
    
    line_layers = {
        '1': '1호선'',
        '2': '2호선',
        '3': '3호선',
        '4': '4호선',
        '5': '5호선',
        '6': '6호선',
        '7': '7호선',
        '8': '8호선'
    }

    for layer_name in line_layers.values():
        doc.layers.add(name=layer_name)
        
    # 폴리라인 추가
    for line in lines:
        msp.add_polyline3d(points=line[:, :3].tolist(), close=False, dxfattribs={'color': 7})  # 7대신 호선별로 레이어 지정
    
    # 텍스트 추가
    for text in texts:
        msp.add_text(text['text'],
                     dxfattribs={'insert': 
                     text['position'],
                     'height': 0.5,
                     'style': '굴림체'}
                     )
    # 3D SOLID 추가
    for solid in solids:
        for face in solid['faces']:
            points = [p[:3] for p in face]
            msp.add_3dface(points, dxfattribs={'color': 7})

    
    doc.saveas(filename)

# 폴리라인 및 텍스트 데이터 생성
def create_line_polylines_and_texts(gdf):
    lines = []
    texts = []
    for line_number, group in gdf.groupby('호선'):
        points = np.array(list(zip(group['x'], group['y'], group['z'])))
        lines.append(points)
        
        # 텍스트 데이터 생성
        for _, row in group.iterrows():
            texts.append({
                'text': row['역명'],
                'position': (row['x'], row['y'], row['z']),
                'rotation': 0  # 텍스트 회전 각도, 필요에 따라 수정 가능
            })
            
    return lines, texts

def create_3d_station_solid(center_x, center_y, base_z, levels, length=210, width=23):
    half_length = length / 2
    half_width = width / 2
    # 큐브의 base z 값 (음수, 지하)
    
    vertices = [
        (center_x - half_length, center_y - half_width, base_z),
        (center_x + half_length, center_y - half_width, base_z),
        (center_x + half_length, center_y + half_width, base_z),
        (center_x - half_length, center_y + half_width, base_z),
        (center_x - half_length, center_y - half_width, base_z + levels),
        (center_x + half_length, center_y - half_width, base_z + levels),
        (center_x + half_length, center_y + half_width, base_z + levels),
        (center_x - half_length, center_y + half_width, base_z + levels)
    ]
    
    faces = [
        [vertices[0], vertices[1], vertices[5], vertices[4]],  # Bottom
        [vertices[1], vertices[2], vertices[6], vertices[5]],  # Side 1
        [vertices[2], vertices[3], vertices[7], vertices[6]],  # Side 2
        [vertices[3], vertices[0], vertices[4], vertices[7]],  # Side 3
        [vertices[0], vertices[1], vertices[2], vertices[3]],  # Top
        [vertices[4], vertices[5], vertices[6], vertices[7]]   # Top
    ]
    
    color = 1  # 빨강색

    # 3D FACE 포맷을 위한 변환
    return vertices, faces  #점 리스트  반환



solids = []

# 모든 역에 대해 SOLID 추가
for _, row in subway_info_gdf.iterrows():
    x, y, z = row['x'], row['y'], row['z']
    floor = row['층수']
    # 각 역마다 SOLID 생성
    #print(type(floor))
    # 층수에 따른 레벨 설정
    levels = {
        'B1': 5, 'B2': 10, 'B3': 15, 'B4': 20, 'B5': 25,
        'B6': 30, 'B7': 35, 'B8': 40, '고가': -5, '지상': 1
    }.get(floor, 0)
    
    vertices, faces = create_3d_station_solid(x, y, z, levels)
    solids.append({
        'vertices': vertices,
        'faces': faces
    })

# GeoDataFrame에서 폴리라인 및 텍스트 데이터 생성
lines, texts = create_line_polylines_and_texts(subway_info_gdf)

# DXF 파일로 저장
save_polylines_to_dxf(cur_path + 'subway_lines.dxf', lines,  texts, solids)

# 호선 목록 생성 (중복 제거)
lines_available = subway_info_gdf['호선'].unique().tolist()

# 체크박스의 초기 상태를 설정 (기본적으로 첫 번째 호선만 선택)
initial_lines = lines_available[:1]  # 초기에는 첫 번째 호선 선택
initial_status = [line in initial_lines for line in lines_available]

# 체크박스 생성
check = CheckButtons(plt.axes([0.05, 0.4, 0.15, 0.45]), lines_available, initial_status)

# 이벤트 핸들러 연결
check.on_clicked(on_check)

#큐브 검사코드#####
def calculate_normal(v1, v2, v3):
    # 두 벡터의 외적을 이용하여 법선 벡터 계산
    u = np.array(v2) - np.array(v1)
    v = np.array(v3) - np.array(v1)
    normal = np.cross(u, v)
    return normal / np.linalg.norm(normal)

def is_rectangle(vertices):
    # 벡터 계산
    edges = [np.array(vertices[i]) - np.array(vertices[j]) for i in range(4) for j in range(i + 1, 4)]
    # 벡터의 내적을 사용하여 직각인지 확인
    dot_products = [np.dot(edges[i], edges[j]) for i in range(len(edges)) for j in range(i + 1, len(edges))]
    return all(np.isclose(dp, 0) for dp in dot_products)

def validate_cube(vertices, faces):
    # 1. 정점 수 검증
    if len(vertices) != 8:
        return False, "큐브는 8개의 정점을 가져야 합니다."

    # 2. 면 수 검증
    if len(faces) != 6:
        return False, "큐브는 6개의 면을 가져야 합니다."

    # 3. 면이 직사각형인지 검증
    for face in faces:
        if len(face) != 4:
            return False, "각 면은 4개의 정점으로 구성되어야 합니다."
        if not is_rectangle(face):
            return False, "모든 면은 직사각형이어야 합니다."

    # 4. 법선 벡터 확인
    normals = []
    for face in faces:
        normal = calculate_normal(face[0], face[1], face[2])
        normals.append(normal)
    
    # 모든 법선 벡터가 유사한 방향을 가지는지 확인
    for i in range(len(normals)):
        for j in range(i + 1, len(normals)):
            if not np.isclose(np.dot(normals[i], normals[j]), 0):
                return False, "면이 올바르게 연결되어 있지 않거나 평행하지 않습니다."

    return True, "큐브가 올바르게 생성되었습니다."
    
valid, message = validate_cube(vertices, faces)

print(message)
# 레이블 및 제목 추가
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_title('2D Visualization of Seoul Subway Lines with Custom Colors')
ax.set_aspect('equal', adjustable='box')
ax.grid(True)
plt.show()
