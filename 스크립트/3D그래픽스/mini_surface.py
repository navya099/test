import numpy as np
from scipy.spatial import Delaunay


class TinSurface:

    def __init__(self):
        self.points = None
        self.tri = None

    def build(self, elevation_points):

        self.points = np.array([
            [p["x"], p["y"], p["z"]]
            for p in elevation_points
        ])

        self.tri = Delaunay(
            self.points[:, :2]
        )

    def get_elevation(
        self,
        x,
        y
    ):

        simplex = self.tri.find_simplex(
            [[x, y]]
        )[0]

        if simplex < 0:
            return None

        vertices = self.tri.simplices[
            simplex
        ]

        return barycentric_interpolate(
            x,
            y,
            self.points[vertices]
        )

def barycentric_interpolate(
    x,
    y,
    triangle_points
):
    x1, y1, z1 = triangle_points[0]
    x2, y2, z2 = triangle_points[1]
    x3, y3, z3 = triangle_points[2]

    det = (
        (y2 - y3) * (x1 - x3)
        + (x3 - x2) * (y1 - y3)
    )

    if abs(det) < 1e-10:
        return None

    l1 = (
        (y2 - y3) * (x - x3)
        + (x3 - x2) * (y - y3)
    ) / det

    l2 = (
        (y3 - y1) * (x - x3)
        + (x1 - x3) * (y - y3)
    ) / det

    l3 = 1.0 - l1 - l2

    return (
        l1 * z1 +
        l2 * z2 +
        l3 * z3
    )

def get_elevation(
    self,
    x,
    y
):

    simplex = self.tri.find_simplex(
        [[x, y]]
    )[0]

    if simplex < 0:
        return None

    vertices = self.tri.simplices[simplex]

    triangle_points = self.points[
        vertices
    ]

    return barycentric_interpolate(
        x,
        y,
        triangle_points
    )

import ezdxf
from shapely.geometry import LineString, Point

doc = ezdxf.readfile(r"C:/TEMP/35702008.dxf")
msp = doc.modelspace()

# 표고점 읽기
elevation_points = []

for insert in msp.query('INSERT[layer=="F0027217"]'):
    p = insert.dxf.insert

    elevation_points.append({
        "x": p.x,
        "y": p.y,
        "z": p.z
    })

# 도로 중심선 읽기
roads = []

for pl in msp.query('LWPOLYLINE[layer=="A0023210"]'):

    coords = [(p[0], p[1]) for p in pl]

    roads.append(
        LineString(coords)
    )

print(f"표고점 : {len(elevation_points)}")
print(f"도로중심선 : {len(roads)}")

surface = TinSurface()

surface.build(
    elevation_points
)

for p in elevation_points[:10]:

    z = surface.get_elevation(
        p["x"],
        p["y"]
    )

    print(
        f"원본={p['z']:.3f} "
        f"조회={z:.3f}"
    )


p1 = elevation_points[0]
p2 = elevation_points[1]

x = (p1["x"] + p2["x"]) / 2
y = (p1["y"] + p2["y"]) / 2

z = surface.get_elevation(x, y)

print(f' 표고점 사이"를 조회 테스트 {z}')

print(
    f"삼각형 개수 : "
    f"{len(surface.tri.simplices)}"
)

road = roads[50]

for sta in np.arange(0, road.length, 10):

    pt = road.interpolate(sta)

    z = surface.get_elevation(
        pt.x,
        pt.y
    )

    print(
        f"STA={sta} "
        f"EL={z}"
    )

    import matplotlib.pyplot as plt

    pts = surface.points

    plt.triplot(
        pts[:, 0],
        pts[:, 1],
        surface.tri.simplices,
        lw=0.3
    )

    x, y = road.xy

    plt.plot(
        x,
        y,
        color='red',
        linewidth=2
    )

    plt.axis("equal")
    plt.show()