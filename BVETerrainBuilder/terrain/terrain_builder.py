from dem.dem_exporter import DEMExporter

class TerrainBuilder:
    """지형 빌더"""
    def __init__(self, dem_processor, seg_coords):
        self.dem_processor = dem_processor
        self.seg_coords = seg_coords

    def build(self):
        """메쉬 빌드"""
        dem_mosaic, dem_out_transform = self.dem_processor.extract_segment(self.seg_coords)
        terrain_mesh = DEMExporter.export_as_mesh(dem_mosaic[0] + 100, dem_out_transform)

        return terrain_mesh