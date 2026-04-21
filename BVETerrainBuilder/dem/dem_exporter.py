import meshio
import numpy as np
import rasterio
from rasterio.crs import CRS
from coordinate_utils import convert_coordinates

class DEMExporter:
    """DEM 출력 모듈"""
    @staticmethod
    def export_as_geotiff(mosaic, out_transform, filename):
        # mosaic은 (bands, rows, cols) 형태
        band = mosaic[0]
        rows, cols = band.shape


        with rasterio.open(
                filename,
                'w',
                driver='GTiff',
                height=rows,
                width=cols,
                count=1,
                dtype=band.dtype,
                crs=CRS.from_epsg(4326),  # 좌표계 WGS84 (EPSG:4326)
                transform=out_transform,
        ) as dst:
            dst.write(band, 1)

    @staticmethod
    def export_as_mesh(band, transform):
        rows, cols = band.shape
        jj, ii = np.meshgrid(np.arange(cols), np.arange(rows))
        lon, lat = rasterio.transform.xy(transform, ii, jj, offset='center')
        lon = np.array(lon).flatten()
        lat = np.array(lat).flatten()
        coords = list(zip(lon, lat))
        xy = np.array(convert_coordinates(coords, 4326, 5186))
        z = band.flatten()
        vertices = np.column_stack((xy[:, 0], xy[:, 1], z))
        faces = []
        for i in range(rows - 1):
            for j in range(cols - 1):
                v1 = i * cols + j
                v2 = v1 + 1
                v3 = v1 + cols
                v4 = v3 + 1
                faces.append([v1, v2, v3])
                faces.append([v2, v4, v3])
        mesh = meshio.Mesh(points=vertices, cells=[("triangle", np.array(faces))])
        return mesh