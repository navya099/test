def create_base_txt() -> str:
    lines = [
        "Options.ObjectVisibility 1",
        "With Route",
        ".comment 랜덤루트",
        ".Elevation 0",
        "With Train",
        "With Structure",
        "$Include(오브젝트.txt)",
        "$Include(프리오브젝트.txt)",
        "$Include(km_index.txt)",
        "$Include(curve_index.txt)",
        "$Include(pitch_index.txt)",
        "With Track",
        "$Include(전주.txt)",
        "$Include(전차선.txt)",
        "$Include(km_post.txt)",
        "$Include(curve_post.txt)",
        "$Include(pitch_post.txt)",
        "$Include(신호.txt)",
        "$Include(통신.txt)",
        "0,.back 0;,.ground 0;,.dike 0;0;32;,.railtype 0;9;",
        "0,.sta START STATION;",
        "100,.stop 0;"
    ]
    return "\n".join(lines)