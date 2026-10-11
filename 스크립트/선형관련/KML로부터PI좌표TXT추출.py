from tkinter.filedialog import askopenfilename

from lxml import etree

def read_kml(file_paths):
    # KML 파일 읽기
    tree = etree.parse(file_paths)

    # KML 파일에서 모든 Placemark 요소 찾기
    placemarks = tree.findall('.//{http://www.opengis.net/kml/2.2}Placemark')

    # 각 Placemark에서 LineString 좌표 읽기
    coordinates = []
    for placemark in placemarks:
        # LineString 요소 찾기
        linestring_element = placemark.find('.//{http://www.opengis.net/kml/2.2}LineString')
        if linestring_element is not None:
            # 좌표 찾기
            coordinates_text = linestring_element.findtext('.//{http://www.opengis.net/kml/2.2}coordinates')
            if coordinates_text:
                # 좌표를 파싱하여 리스트로 변환
                coordinates = [tuple(map(float, coord.split(','))) for coord in coordinates_text.split()]

    return coordinates

def main():
    #파일 읽기
    file_path = None
    file_path = askopenfilename(title='kml파일 선택', filetypes=[("kml 파일", "*.kml")])
    if not file_path:
        raise FileNotFoundError('파일을 찾을수없습니다.')
    #좌표읽기
    coordinates = read_kml(file_path)
    #z 제거
    # Z 제거
    coordinates = [
        (x, y)
        for x, y, *_ in coordinates
    ]
    # 변환함수 실행
    from modules.coordinate_utils import convert_coordinates
    tm_coord = convert_coordinates(coordinates, src=4326, target=5186)
    # 결과를 파일에 저장
    # 결과 저장
    from pathlib import Path
    output_path = Path(file_path).with_suffix(".txt")

    # TXT 저장
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for x, y in tm_coord:
                f.write(f"{x:.3f},{y:.3f}\n")

        print(f"파일이 성공적으로 저장되었습니다: {output_path}")

    except Exception as e:
        print(f"파일 저장 실패: {e}")

if __name__ == '__main__':
    main()
