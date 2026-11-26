import json
import os

DEFAULT_MASTER_CONFIG = {
    "project_name": "AUTO_STATION_V1_TO_V17_MASTER",
    "ground_level_el": 12.0,
    "ground_profile": [
        {"sta": 0.0, "GL": 12.0, "weathered_rock": 2.5, "soft_rock": -6.0},
        {"sta": 90.0, "GL": 13.2, "weathered_rock": 2.8, "soft_rock": -5.8},
        {"sta": 180.0, "GL": 12.0, "weathered_rock": 2.0, "soft_rock": -6.5}
    ],
    "alignments": {
        "MAIN_LINE": {
            "start_xy": [0.0, 0.0],
            "start_azimuth_deg": 0.0,
            "length": 180.0,
            "curve_radius": 480.0
        },
        "SPLIT_DOWN_LINE": {
            "start_xy": [35.0, -24.0],
            "start_azimuth_deg": -2.0,
            "length": 140.0,
            "curve_radius": 620.0
        }
    },
    "proposed_station": {
        "id": "NEW_TRANSFER_HUB",
        "structure_type": "BOX",
        "alignment_ref": "MAIN_LINE",
        "vertical_profile_rl": [
            {"sta": 0.0, "rl_el": -11.0},
            {"sta": 90.0, "rl_el": -12.4},
            {"sta": 180.0, "rl_el": -11.2}
        ],
        "section_stations": [
            {"sta": 0.0, "inner_left_w": 6.0, "inner_right_w": 6.0, "active_levels": ["B3_Platform"]},
            {"sta": 30.0, "inner_left_w": 9.8, "inner_right_w": 9.8, "active_levels": ["B3_Platform", "B2_TransferHall", "B1_Concourse"]},
            {"sta": 90.0, "inner_left_w": 9.8, "inner_right_w": 12.2, "active_levels": ["B3_Platform", "B2_TransferHall", "B1_Concourse"]},
            {"sta": 145.0, "inner_left_w": 9.8, "inner_right_w": 9.8, "active_levels": ["B3_Platform", "B2_TransferHall", "B1_Concourse"]},
            {"sta": 180.0, "inner_left_w": 6.0, "inner_right_w": 6.0, "active_levels": ["B3_Platform"]}
        ],
        "levels_definition": [
            {
                "level_name": "B3_Platform",
                "is_void": False,
                "bot_slab_t": 1.45,
                "top_slab_t": 0.65,
                "wall_t": 1.30,
                "clear_height": 6.20,
                "haunch_size": 0.45,
                "columns": {"shape": "CIRCLE", "diameter": 0.90, "offsets_y": [-4.8, 4.8], "sta_start": 32.0, "sta_end": 142.0, "sta_spacing": 8.0},
                "finishes": {"floor_t": 0.12, "ceiling_drop": 0.90, "wall_t": 0.18}
            },
            {
                "level_name": "B2_TransferHall",
                "is_void": False,
                "bot_slab_t": 0.0,
                "top_slab_t": 0.60,
                "wall_t": 1.10,
                "clear_height": 5.00,
                "haunch_size": 0.35,
                "columns": {"shape": "RECT", "width_y": 0.80, "depth_x": 1.00, "offsets_y": [-5.2, 0.0, 5.2], "sta_start": 32.0, "sta_end": 142.0, "sta_spacing": 8.0},
                "finishes": {"floor_t": 0.10, "ceiling_drop": 0.65, "wall_t": 0.15}
            },
            {
                "level_name": "B1_Concourse",
                "is_void": False,
                "bot_slab_t": 0.0,
                "top_slab_t": 1.20,
                "wall_t": 0.95,
                "clear_height": 5.50,
                "haunch_size": 0.40,
                "columns": {"shape": "RECT", "width_y": 1.10, "depth_x": 1.30, "offsets_y": [0.0], "sta_start": 35.0, "sta_end": 140.0, "sta_spacing": 10.0},
                "finishes": {"floor_t": 0.15, "ceiling_drop": 1.10, "wall_t": 0.20}
            }
        ],
        "assets": [
            {"id": "ES-01", "type": "ESCALATOR", "from_level": "B3_Platform", "to_level": "B1_Concourse", "sta": 55.0, "offset_y": 2.4, "length": 22.0, "width": 1.6, "cut_opening": True},
            {"id": "EV-01", "type": "ELEVATOR", "from_level": "B3_Platform", "to_level": "B1_Concourse", "sta": 105.0, "offset_y": -3.5, "length": 3.2, "width": 3.0, "cut_opening": True}
        ]
    },
    "tunnel_station_sample": {
        "inner_half_width": 9.80,
        "springline_el": 3.20,
        "crown_el": 11.40,
        "sidewall_bottom_el": -1.80,
        "invert_bottom_el": -3.10,
        "lining_thickness": 0.65,
        "shotcrete_thickness": 0.25,
        "platform_top_el": 1.15,
        "track_bed_half_w": 3.60,
        "upper_deck_bot_el": 6.20,
        "upper_deck_t": 0.55
    },
    "existing_stations": [
        {
            "id": "EX-01_LINE_2_BOX",
            "structure_type": "BOX",
            "clearance_gap": 1.0,
            "el_bottom": -3.5,
            "el_top": 8.5,
            "alignment": {"start_xy": [20.0, 42.0], "start_azimuth_deg": -22.0, "length": 140.0, "curve_radius": 320.0, "left_w": 10.5, "right_w": 10.5}
        },
        {
            "id": "EX-02_LINE_7_BOX",
            "structure_type": "BOX",
            "clearance_gap": 1.2,
            "el_bottom": -12.0,
            "el_top": 5.0,
            "alignment": {"start_xy": [115.0, -45.0], "start_azimuth_deg": 78.0, "length": 130.0, "curve_radius": -500.0, "left_w": 11.0, "right_w": 11.0}
        },
        {
            "id": "EX-03_GTX_ARCH_TUNNEL",
            "structure_type": "TUNNEL_ARCH",
            "clearance_gap": 2.5,
            "el_bottom": -24.5,
            "el_top": -11.0,
            "tunnel_profile": {"springline_el": -18.5, "sidewall_bot_el": -22.8, "lining_t": 0.85},
            "alignment": {"start_xy": [10.0, -18.0], "start_azimuth_deg": 8.0, "length": 170.0, "curve_radius": 580.0, "left_w": 10.2, "right_w": 10.2}
        }
    ],
    "shallow_existing_structures": [
        {
            "id": "EX-UNDERPASS_01",
            "category": "UNDERPASS",
            "clearance_gap": 1.5,
            "box_total_height": 6.8,
            "alignment": {"start_xy": [55.0, -45.0], "start_azimuth_deg": 82.0, "length": 110.0, "curve_radius": 0.0, "left_w": 9.0, "right_w": 9.0},
            "el_top_profile": [
                {"s": 0.0, "el_top": 11.5},
                {"s": 35.0, "el_top": 9.2},
                {"s": 75.0, "el_top": 9.2},
                {"s": 110.0, "el_top": 11.5}
            ]
        },
        {
            "id": "EX-WALKWAY_01",
            "category": "PEDESTRIAN_WALKWAY",
            "clearance_gap": 0.8,
            "box_total_height": 4.2,
            "alignment": {"start_xy": [125.0, -30.0], "start_azimuth_deg": 90.0, "length": 75.0, "curve_radius": 0.0, "left_w": 3.5, "right_w": 3.5},
            "el_top_profile": [
                {"s": 0.0, "el_top": 10.2},
                {"s": 75.0, "el_top": 10.2}
            ]
        }
    ],
    "integrated_shaft": {
        "id": "SHAFT-01_COMBINED",
        "center_xy": [75.0, 26.5],
        "outer_length_x": 24.0,
        "outer_width_y": 13.5,
        "wall_t": 1.20,
        "bot_slab_t": 1.60,
        "el_bottom": -14.5,
        "el_top_vent_tower": 16.5,
        "el_top_canopy": 15.8,
        "vent_shaft_length_x": 7.5,
        "divider_wall_t": 0.45,
        "adit": {"width_x": 8.5, "wall_t": 1.00, "passenger_h": 3.60, "duct_h": 2.40, "floor_el": -12.4}
    },
    "target_cross_sections": [
        {"sta": 62.0, "proj_window_m": 12.0, "title": "SEC A-A (STA.0+062) - UNDERPASS & SHAFT LINK"},
        {"sta": 115.0, "proj_window_m": 15.0, "title": "SEC B-B (STA.0+115) - EXISTING STATIONS & WALKWAY"}
    ]
}

def load_or_create_config(config_path):
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    if not os.path.exists(config_path):
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_MASTER_CONFIG, f, indent=2, ensure_ascii=False)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)
