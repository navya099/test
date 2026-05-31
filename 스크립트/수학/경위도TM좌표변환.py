import pyproj

def calc_pl2xy(long, lat):
    p1_type = pyproj.CRS.from_epsg(4326)
    p2_type = pyproj.CRS.from_epsg(5186)
    transformer = pyproj.Transformer.from_crs(p1_type, p2_type, always_xy=True)
    x, y = transformer.transform(long, lat)
    print(x, y)
    return x, y  # [m]

long = float(input("Enter 경도: "))
lat = float(input("Enter 위도: "))

x, y = calc_pl2xy(long, lat)
print("토목좌표: XY", y,x)
print("수학좌표: XY", x, y)
