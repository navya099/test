def isbridge_tunnel(sta, structure_list):
    """sta가 교량/터널/토공 구간에 해당하는지 구분하는 함수"""
    for name, start, end in structure_list['bridge']:
        if start <= sta <= end:
            return '교량'

    for name, start, end in structure_list['tunnel']:
        if start <= sta <= end:
            return '터널'

    return '토공'


def apply_brokenchain_to_structure(structure_list, brokenchain):
    """
    structure_list의 각 구간(start, end)에 brokenchain 값을 더해서
    같은 구조로 반환하는 함수.

    :param structure_list: {'bridge': [(start, end), ...], 'tunnel': [(start, end), ...]}
    :param brokenchain: float, 오프셋 값 (예: 0.0 또는 양수/음수)
    :return: 수정된 structure_list (같은 구조, 값은 offset 적용)
    """
    if brokenchain == 0.0:
        # 오프셋이 없으면 원본 그대로 반환
        return structure_list

    updated_structure = {'bridge': [], 'tunnel': []}

    for key in ['bridge', 'tunnel']:
        for name, start, end in structure_list.get(key, []):
            new_start = start + brokenchain
            new_end = end + brokenchain
            updated_structure[key].append((name, new_start, new_end))

    return updated_structure