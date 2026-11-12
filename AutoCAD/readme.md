# cadgeom

Pure-Python CAD geometry primitives. No AutoCAD dependency.
Supports 2D/3D points, lines, arcs, polylines, and DXF bulge segments.

## Features
- `Point2d`, `Point3d`
- `Line2d`, `Line3d`
- `Arc` — counterclockwise arc with proper range-aware distance
- `BulgeSegment` — DXF bulge (`tan(θ/4)`) with clockwise support
- `Polyline` — mixed line/arc/bulge path
- `Geometry` — abstract base with uniform `move`/`moved`/`rotate`/`rotated`/`center` contract

## Install
pip install cadgeom

## Quick start
```python
from cadgeom import Point2d, Line2d, Polyline

pl = Polyline([
    Line2d(Point2d(0, 0), Point2d(4, 0)),
    Line2d(Point2d(4, 0), Point2d(4, 3)),
])
print(pl.length)         # 7.0
print(pl.distance_to(Point2d(2, 2)))  # 2.0