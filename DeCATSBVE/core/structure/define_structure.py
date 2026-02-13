def isbridge_tunnel(sta, structure_list):
    """sta가 교량/터널/토공 구간에 해당하는지 구분하는 함수"""
    for name, start, end in structure_list['bridge']:
        if start <= sta <= end:
            return '교량'

    for name, start, end in structure_list['tunnel']:
        if start <= sta <= end:
            return '터널'

    return '토공'