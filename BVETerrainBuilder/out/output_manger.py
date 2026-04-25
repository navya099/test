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
    def save_obj_with_groups(filename, groups):
        """OBJ를 그룹화 하여 저장 (여러 메쉬 지원)"""
        with open(filename, "w") as f:
            vertex_offset = 0
            for points, faces, color, label in groups:
                f.write(f"o {label}\n")
                # vertices
                for v in points:
                    f.write(f"v {v[0]} {v[1]} {v[2]}\n")
                # faces (인덱스는 OBJ에서 1부터 시작)
                for face in faces:
                    f.write(f"f {face[0] + 1 + vertex_offset} "
                            f"{face[1] + 1 + vertex_offset} "
                            f"{face[2] + 1 + vertex_offset}\n")
                vertex_offset += len(points)
