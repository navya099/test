def check_isairjoint(input_sta, airjoint_list):
    for data in airjoint_list:
        sta, tag = data
        if input_sta == sta:
            return tag