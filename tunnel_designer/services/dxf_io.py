"""DXF 캐시 + 쓰기 (HATCH 포함)."""
from __future__ import annotations
from typing import Optional

from tkinter import messagebox
import ezdxf
from matplotlib.patches import Circle, Arc, Rectangle as MplRect
from shapely.geometry import Polygon

from core.constants import (
    TunnelType, OVERLAP_LAYER,
    HATCH_STYLE_SOLID, HATCH_STYLE_PATTERN, HATCH_STYLE_BOTH,
)
from core.geometry import compute_multi_arch, check_multi_arch_overlap
from core.models import TunnelParams


class DxfCache:
    def __init__(self):
        self.path: Optional[str] = None
        self.entities: Optional[list] = None

    def load(self, path: str, force: bool = False):
        if not force and path == self.path and self.entities is not None:
            return self.entities
        try:
            doc = ezdxf.readfile(path)
        except (FileNotFoundError, IOError) as e:
            messagebox.showwarning("DXF 로드 실패", f"{path}\n{e}")
            self.path, self.entities = None, None
            return None
        self.path = path
        self.entities = list(doc.modelspace())
        return self.entities


def add_hatch_for_polygon(msp, poly: Polygon, *, color: int = 1,
                          solid: bool = True,
                          pattern: str = HATCH_STYLE_PATTERN,
                          scale: float = 0.3, alpha: int = 70,
                          layer: str = OVERLAP_LAYER):
    if poly.is_empty:
        return
    if poly.geom_type != "Polygon":
        for g in getattr(poly, "geoms", []):
            add_hatch_for_polygon(msp, g, color=color, solid=solid,
                                  pattern=pattern, scale=scale,
                                  alpha=alpha, layer=layer)
        return
    hatch = msp.add_hatch(color=color, dxfattribs={"layer": layer})
    if solid:
        hatch.set_solid_fill(color=color)
    else:
        try:
            hatch.set_pattern_fill(pattern, color=color, scale=scale)
        except Exception:
            hatch.set_solid_fill(color=color)
    ext = [(x, y) for x, y in poly.exterior.coords]
    if ext and ext[0] != ext[-1]:
        ext.append(ext[0])
    if ext:
        hatch.paths.add_polyline_path(ext, is_closed=True)
    for interior in poly.interiors:
        hole = [(x, y) for x, y in interior.coords]
        if hole and hole[0] != hole[-1]:
            hole.append(hole[0])
        if hole:
            hatch.paths.add_polyline_path(hole, is_closed=True)
    try:
        hatch.transparency = alpha / 100.0
    except AttributeError:
        pass


def write_dxf(path: str, ax, params: TunnelParams, hatch_style: str):
    doc = ezdxf.new(dxfversion="R2018")
    msp = doc.modelspace()
    if OVERLAP_LAYER not in doc.layers:
        doc.layers.add(OVERLAP_LAYER, color=1)

    # 선
    for line in ax.lines:
        xs, ys = line.get_data()
        for i in range(len(xs) - 1):
            msp.add_line(start=(xs[i], ys[i]), end=(xs[i + 1], ys[i + 1]))

    # 패치
    for patch in ax.patches:
        if isinstance(patch, Circle):
            msp.add_circle(center=patch.center, radius=patch.radius)
        elif isinstance(patch, Arc):
            r = patch.width / 2
            s, e = patch.theta1 % 360, patch.theta2 % 360
            if e <= s:
                e += 360
            msp.add_arc(center=patch.center, radius=r,
                        start_angle=s, end_angle=e)
        elif isinstance(patch, MplRect):
            x, y = patch.get_xy()
            w, h = patch.get_width(), patch.get_height()
            pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
            msp.add_lwpolyline(pts, close=True)

    # 겹침 HATCH
    if params.kind in (TunnelType.NATM_2ARCH, TunnelType.NATM_3ARCH):
        mg = compute_multi_arch(params)
        info = check_multi_arch_overlap(mg)
        if info.has_overlap:
            geoms = [g.polygon for g in mg.arches]
            for (i, j) in info.pairs:
                inter = geoms[i].intersection(geoms[j])
                if inter.is_empty:
                    continue
                if hatch_style in (HATCH_STYLE_SOLID, HATCH_STYLE_BOTH):
                    add_hatch_for_polygon(msp, inter, color=1, solid=True,
                                          alpha=70, layer=OVERLAP_LAYER)
                if hatch_style in (HATCH_STYLE_PATTERN, HATCH_STYLE_BOTH):
                    add_hatch_for_polygon(msp, inter, color=1, solid=False,
                                          pattern=HATCH_STYLE_PATTERN,
                                          scale=0.3, alpha=70,
                                          layer=OVERLAP_LAYER)
                polys = ([inter] if inter.geom_type == "Polygon"
                         else list(getattr(inter, "geoms", [])))
                for poly in polys:
                    if poly.is_empty:
                        continue
                    pts = [(x, y) for x, y in poly.exterior.coords]
                    if pts and pts[0] != pts[-1]:
                        pts.append(pts[0])
                    msp.add_lwpolyline(pts, close=True,
                                       dxfattribs={"layer": OVERLAP_LAYER})

    doc.saveas(path)