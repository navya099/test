class OutputExporter:
    @staticmethod
    def save_shapefile(segments):
        save_shp(segments)

    @staticmethod
    def save_qml(segments):
        save_qml(segments)