from shapely import box
import geopandas as gpd

class OutputExporter:
    @staticmethod
    def save_shapefile(segments):
        """구간별 SHP로 저장"""
        for idx, (minx, miny, maxx, maxy) in enumerate(segments, start=1):

            poly = box(minx, miny, maxx, maxy)
            gdf = gpd.GeoDataFrame([{"id": idx, "geometry": poly}], crs="EPSG:5186")
            out_shp = f"C:/temp/shp/segment_{idx}.shp"
            gdf.to_file(out_shp)

    @staticmethod
    def save_qml(segments):
        #템플릿
        qml_template = """<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
            <qgis version="3.16" styleCategories="Symbology">
              <renderer-v2 type="singleSymbol">
                <symbols>
                  <symbol name="0" type="fill" alpha="1">
                    <layer pass="0" class="SimpleFill" locked="0">
                      <prop k="color" v="255,255,255,0"/> <!-- 채우기 없음 -->
                      <prop k="outline_color" v="0,0,0,255"/> <!-- 외곽선 검정 -->
                      <prop k="outline_width" v="0.1"/> <!-- 외곽선 두께 -->
                      <prop k="style" v="no"/> <!-- 내부 채움 없음 -->
                    </layer>
                  </symbol>
                </symbols>
              </renderer-v2>
            </qgis>
            """
        # 구간별 QML 생성
        for idx in range(1, len(segments) + 1):
            qml_path = f"C:/temp/shp/segment_{idx}.qml"
            with open(qml_path, "w", encoding="utf-8") as f:
                f.write(qml_template)
            # print("QML 저장 완료:", qml_path)

    @staticmethod
    def save_obj_with_groups(filename,
                             terrain_vertices, terrain_faces,
                             track_vertices, track_faces,
                             slope_left=None, slope_right=None):
        """OBJ를 그룹화 하여 저장"""
        with open(filename, "w") as f:
            # Terrain 그룹
            f.write("o Terrain\n")
            for v in terrain_vertices:
                f.write(f"v {v[0]} {v[1]} {v[2]}\n")
            for face in terrain_faces:
                f.write(f"f {face[0] + 1} {face[1] + 1} {face[2] + 1}\n")

            # Track 그룹
            f.write("o Track\n")
            offset = len(terrain_vertices)
            for v in track_vertices:
                f.write(f"v {v[0]} {v[1]} {v[2]}\n")
            for face in track_faces:
                f.write(f"f {face[0] + 1 + offset} {face[1] + 1 + offset} {face[2] + 1 + offset}\n")

            # 좌측 slope 그룹
            if slope_left is not None:
                f.write("o SlopeLeft\n")
                offset2 = offset + len(track_vertices)
                for v in slope_left.points:
                    f.write(f"v {v[0]} {v[1]} {v[2]}\n")
                for face in slope_left.cells[0].data:
                    f.write(f"f {face[0] + 1 + offset2} {face[1] + 1 + offset2} {face[2] + 1 + offset2}\n")

            # 우측 slope 그룹
            if slope_right is not None:
                f.write("o SlopeRight\n")
                offset3 = offset + len(track_vertices) + len(slope_left.points if slope_left else [])
                for v in slope_right.points:
                    f.write(f"v {v[0]} {v[1]} {v[2]}\n")
                for face in slope_right.cells[0].data:
                    f.write(f"f {face[0] + 1 + offset3} {face[1] + 1 + offset3} {face[2] + 1 + offset3}\n")