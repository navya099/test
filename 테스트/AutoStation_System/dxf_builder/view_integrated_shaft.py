def draw_integrated_shaft_sections(msp, cfg, base_offset=(240.0, 120.0)):
    if "integrated_shaft" not in cfg:
        return
    bx, by = base_offset
    gl = cfg["ground_level_el"]
    sh = cfg["integrated_shaft"]
    adit = sh["adit"]

    hl = sh["outer_length_x"] / 2.0
    wt = sh["wall_t"]
    ihl = hl - wt
    el_bot = sh["el_bottom"]
    el_str_bot = el_bot + sh["bot_slab_t"]

    # 1) 수직구 종단면 (출입구 존 + 내화격벽 + 환기풍도 존)
    msp.add_line((bx - hl - 5.0, by + gl), (bx + hl + 5.0, by + gl), dxfattribs={"layer": "0_CENTERLINE"})
    msp.add_lwpolyline([(bx - hl, by + el_bot), (bx + hl, by + el_bot), (bx + hl, by + gl), (bx + ihl, by + gl),
                        (bx + ihl, by + el_str_bot), (bx - ihl, by + el_str_bot), (bx - ihl, by + gl), (bx - hl, by + gl)],
                       close=True, dxfattribs={"layer": "4_SHAFT_STRUCTURE"})

    div_x = bx + ihl - sh["vent_shaft_length_x"] - sh["divider_wall_t"] / 2.0
    dt = sh["divider_wall_t"]
    msp.add_lwpolyline([(div_x - dt/2, by + el_str_bot), (div_x + dt/2, by + el_str_bot),
                        (div_x + dt/2, by + sh["el_top_vent_tower"]), (div_x - dt/2, by + sh["el_top_vent_tower"])],
                       close=True, dxfattribs={"layer": "4_SHAFT_STRUCTURE"})

    # 지상 환기탑 및 출입구 캐노피
    msp.add_lwpolyline([(div_x - dt/2, by + gl), (bx + hl, by + gl),
                        (bx + hl, by + sh["el_top_vent_tower"]), (div_x - dt/2, by + sh["el_top_vent_tower"])],
                       close=True, dxfattribs={"layer": "4_SHAFT_VENT_DUCT"})
    msp.add_lwpolyline([(bx - hl - 1.5, by + gl), (div_x - dt/2, by + gl),
                        (div_x - dt/2, by + sh["el_top_canopy"]), (bx - hl - 1.5, by + sh["el_top_canopy"] - 0.6)],
                       close=True, dxfattribs={"layer": "3_ASSET_BODY"})

    msp.add_text("INTEGRATED SHAFT LONGITUDINAL SECTION (ENTRANCE + VENT TOWER)",
                 dxfattribs={"layer": "TEXT_ANNO", "height": 0.55}).set_placement((bx - hl, by + el_bot - 3.0))

    # 2) 수직구 <-> 본선 연결통로(ADIT) 이층 구조 횡단면
    cx = bx + 55.0
    sh_hw = sh["outer_width_y"] / 2.0
    msp.add_line((cx - sh_hw - 3.0, by + gl), (cx + 35.0, by + gl), dxfattribs={"layer": "0_CENTERLINE"})
    msp.add_lwpolyline([(cx - sh_hw, by + el_bot), (cx + sh_hw, by + el_bot),
                        (cx + sh_hw, by + sh["el_top_vent_tower"]), (cx - sh_hw, by + sh["el_top_vent_tower"])],
                       close=True, dxfattribs={"layer": "4_SHAFT_STRUCTURE"})

    fl_el = adit["floor_el"]
    p_top = fl_el + adit["passenger_h"]
    d_bot = p_top + 0.4
    d_top = d_bot + adit["duct_h"]
    msp.add_lwpolyline([(cx + sh_hw, by + fl_el - 1.2), (cx + 22.0, by + fl_el - 1.2),
                        (cx + 22.0, by + d_top + 1.0), (cx + sh_hw, by + d_top + 1.0)],
                       close=True, dxfattribs={"layer": "4_SHAFT_STRUCTURE"})
    msp.add_lwpolyline([(cx + sh_hw - wt, by + fl_el), (cx + 23.0, by + fl_el),
                        (cx + 23.0, by + p_top), (cx + sh_hw - wt, by + p_top)],
                       close=True, dxfattribs={"layer": "3_ASSET_BODY"})
    msp.add_lwpolyline([(cx + sh_hw - wt, by + d_bot), (cx + 23.0, by + d_bot),
                        (cx + 23.0, by + d_top), (cx + sh_hw - wt, by + d_top)],
                       close=True, dxfattribs={"layer": "4_SHAFT_VENT_DUCT"})

    msp.add_text("SHAFT + DOUBLE-DECK ADIT (PASSENGER + VENT DUCT)",
                 dxfattribs={"layer": "TEXT_ANNO", "height": 0.55}).set_placement((cx - sh_hw, by + el_bot - 3.0))
