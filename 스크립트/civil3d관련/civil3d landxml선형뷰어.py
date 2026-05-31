import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET

def parse_landxml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    ns = {'landxml': 'http://www.landxml.org/schema/LandXML-1.2'}
    
    line_data = []
    profile_data = []

    alignments = root.findall('.//landxml:Alignment', ns)
    for alignment in alignments:
        coord_geom = alignment.find('.//landxml:CoordGeom', ns)
        if coord_geom is not None:
            linestrings = coord_geom.findall('.//landxml:Line', ns)
            for linestring in linestrings:
                start = linestring.find('.//landxml:Start', ns)
                end = linestring.find('.//landxml:End', ns)
                if start is not None and end is not None:
                    x1, y1 = map(float, start.text.split())
                    x2, y2 = map(float, end.text.split())
                    line_data.append(((x1, y1), (x2, y2)))

            curves = coord_geom.findall('.//landxml:Curve', ns)
            for curve in curves:
                start = curve.find('.//landxml:Start', ns)
                end = curve.find('.//landxml:End', ns)
                if start is not None and end is not None:
                    x1, y1 = map(float, start.text.split())
                    x2, y2 = map(float, end.text.split())
                    line_data.append(((x1, y1), (x2, y2)))

            spirals = coord_geom.findall('.//landxml:Spiral', ns)
            for spiral in spirals:
                start = spiral.find('.//landxml:Start', ns)
                end = spiral.find('.//landxml:End', ns)
                if start is not None and end is not None:
                    x1, y1 = map(float, start.text.split())
                    x2, y2 = map(float, end.text.split())
                    line_data.append(((x1, y1), (x2, y2)))
    
    profiles = root.findall('.//landxml:Profile', ns)
    for profile in profiles:
        prof_align = profile.find('.//landxml:ProfAlign', ns)
        if prof_align is not None:
            pvi_points = prof_align.findall('.//landxml:PVI', ns)
            for pvi in pvi_points:
                station, elevation = map(float, pvi.text.split())
                profile_data.append((station, elevation))
    
    return line_data, profile_data

def plot_alignment(line_data, profile_data):
    fig, axs = plt.subplots(2, 1, figsize=(12, 12))

    # 첫 번째 서브플롯: 선형 데이터
    for (x1, y1), (x2, y2) in line_data:
        axs[0].plot([y1, y2], [x1, x2], marker='o')
    axs[0].set_xlabel('Y')
    axs[0].set_ylabel('X')
    axs[0].set_title('Road Alignment')
    axs[0].grid(True)

    # 두 번째 서브플롯: 프로파일 데이터
    if profile_data:
        stations, elevations = zip(*profile_data)
        axs[1].plot(stations, elevations, marker='o')
        axs[1].set_xlabel('Station')
        axs[1].set_ylabel('Elevation')
        axs[1].set_title('Profile')
        axs[1].grid(True)

    plt.tight_layout()
    plt.show()

# LandXML 파일 경로
file_path = 'C:/Users/Administrator/Documents/임시/merge테스트_modified.xml'

# LandXML 파일 파싱 및 데이터 추출
line_data, profile_data = parse_landxml(file_path)

print(f"Number of lines extracted: {len(line_data)}")
print(f"Number of profile points extracted: {len(profile_data)}")

# 데이터 시각화
plot_alignment(line_data, profile_data)
