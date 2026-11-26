from shapely.geometry import Polygon

def setup_master_layers(doc):
    if "DASHED" not in doc.linetypes:
        doc.linetypes.add("DASHED", pattern=[1.5, 1.0, -0.5])
    if "HIDDEN" not in doc.linetypes:
        doc.linetypes.add("HIDDEN", pattern=[0.8, 0.4, -0.4])
    if "CENTER" not in doc.linetypes:
        doc.linetypes.add("CENTER", pattern=[3.0, 2.0, -0.25, 0.25, -0.25])

    layers = [
        ("0_GRID_AXIS", 8, "CONTINUOUS"),
        ("0_CENTERLINE", 1, "CENTER"),
        ("0_GROUND_STRATA", 40, "DASHED"),
        ("1_NEW_STR_CONCRETE", 7, "CONTINUOUS"),
        ("1_NEW_STR_COL", 30, "CONTINUOUS"),
        ("1_TUNNEL_LINING", 140, "CONTINUOUS"),
        ("2_NEW_FIN_WALL", 3, "CONTINUOUS"),
        ("2_NEW_FIN_CEIL_FL", 4, "CONTINUOUS"),
        ("3_ASSET_BODY", 6, "CONTINUOUS"),
        ("3_SLAB_OPENING", 2, "CONTINUOUS"),
        ("4_SHAFT_STRUCTURE", 30, "CONTINUOUS"),
        ("4_SHAFT_VENT_DUCT", 5, "CONTINUOUS"),
        ("PROJ_EX_CLASH", 1, "CONTINUOUS"),
        ("PROJ_EX_OVERHEAD", 4, "DASHED"),
        ("PROJ_EX_UNDERNEATH", 30, "HIDDEN"),
        ("PROJ_CLEARANCE_GAP", 2, "DASHED"),
        ("TRANSFER_LINK_GUIDE", 6, "CONTINUOUS"),
        ("TEXT_ANNO", 7, "CONTINUOUS")
    ]
    for name, color, ltype in layers:
        if name not in doc.layers:
            doc.layers.add(name, color=color, linetype=ltype)

def draw_shapely_geom(msp, geom, layer, bx=0.0, by=0.0, hatch_pattern=None):
    if geom.is_empty:
        return
    polys = [geom] if isinstance(geom, Polygon) else list(geom.geoms)
    for p in polys:
        if p.is_empty:
            continue
        ext_pts = [(x + bx, y + by) for x, y in p.exterior.coords]
        msp.add_lwpolyline(ext_pts, close=True, dxfattribs={"layer": layer})
        for interior in p.interiors:
            int_pts = [(x + bx, y + by) for x, y in interior.coords]
            msp.add_lwpolyline(int_pts, close=True, dxfattribs={"layer": layer})
        if hatch_pattern:
            h = msp.add_hatch(color=256, dxfattribs={"layer": layer})
            h.set_pattern_fill(hatch_pattern, scale=1.0)
            h.paths.add_polyline_path(ext_pts, is_closed=True)
