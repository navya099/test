import re
import random
import math
from enums.airjoint_section import AirJoint
from utils.math_util import return_new_point


def find_last_block(data):
    """
    데이터 리스트에서 마지막 블록 번호(첫 번째 숫자)를 반환.
    예: ['45676,500,0','4646,366,35'] → 4646
    """
    last_block = None

    for line in data:
        if isinstance(line, str):
            # 문자열 맨 앞의 숫자만 추출 (콤마 앞까지)
            match = re.match(r'(\d+)', line)
            if match:
                last_block = int(match.group(1))

    return last_block

def distribute_pole_spacing_flexible(start_km, end_km, spans=(45, 50, 55, 60)):
    """
    45, 50, 55, 60m 범위에서 전주 간격을 균형 있게 배분하여 전체 구간을 채우는 함수
    마지막 전주는 종점보다 약간 앞에 위치할 수도 있음.

    :param start_km: 시작점 (km 단위)
    :param end_km: 끝점 (km 단위)
    :param spans: 사용 가능한 전주 간격 리스트 (기본값: 45, 50, 55, 60)
    :return: 전주 간격 리스트, 전주 위치 리스트
    """
    start_m = int(start_km * 1000)  # km → m 변환
    end_m = int(end_km * 1000)

    positions = [start_m]
    selected_spans = []
    current_pos = start_m

    while current_pos < end_m:
        possible_spans = list(spans)  # 사용 가능한 간격 리스트 (45, 50, 55, 60)
        random.shuffle(possible_spans)  # 랜덤 배치

        for span in possible_spans:
            if current_pos + span > end_m:
                continue  # 종점을 넘어서면 다른 간격을 선택

            positions.append(current_pos + span)
            selected_spans.append(span)
            current_pos += span
            break  # 하나 선택하면 다음으로 이동

        # 더 이상 배치할 간격이 없으면 종료
        if current_pos + min(spans) > end_m:
            break

    return selected_spans, positions

def define_airjoint_section(positions, airjoint_span):
    airjoint_list = []  # 결과 리스트

    def is_near_multiple_of_DIG(number, tolerance=100):
        """주어진 수가 1200의 배수에 근사하는지 판별하는 함수"""
        remainder = number % airjoint_span
        return number > airjoint_span and (remainder <= tolerance or remainder >= (airjoint_span - tolerance))

    i = 0  # 인덱스 변수
    while i < len(positions) - 1:  # 마지막 전주는 제외
        pos = positions[i]  # 현재 전주 위치

        if is_near_multiple_of_DIG(pos):  # 조건 충족 시
            next_values = positions[i + 1:min(i + 6, len(positions))]  # 다음 5개 값 가져오기
            tags = [
                AirJoint.START.value,
                AirJoint.POINT_2.value,
                AirJoint.MIDDLE.value,
                AirJoint.POINT_4.value,
                AirJoint.END.value
            ]

            # (전주 위치, 태그) 쌍을 리스트에 추가 (최대 5개까지만)
            airjoint_list.extend(list(zip(next_values, tags[:len(next_values)])))

            # 다음 5개의 값을 가져왔으므로 인덱스를 건너뛰기
            i += 5
        else:
            i += 1  # 조건이 맞지 않으면 한 칸씩 이동

    return airjoint_list

def generate_postnumbers(lst):
    postnumbers = []
    prev_km = -1
    count = 0

    for number in lst:
        km = number // 1000  # 1000으로 나눈 몫이 같은 구간
        if km == prev_km:
            count += 1  # 같은 구간에서 숫자 증가
        else:
            prev_km = km
            count = 1  # 새로운 구간이므로 count를 0으로 초기화

        postnumbers.append((number, f'{km}-{count}'))

    return postnumbers

def casting_key_str_to_int(dic):
    return {int(k): v for k, v in dic.items()}

def get_block_index(current_track_position, block_interval=25):
    """현재 트랙 위치를 블록 인덱스로 변환"""
    return math.floor(current_track_position / block_interval + 0.001) * block_interval

def find_post_number(lst, pos):
    for arg in lst:
        if arg[0] == pos:
            return arg[1]

def initialrize_tenstion_device(pos, gauge, currentspan, contact_height, system_heigh, y=0):
    """장력장치구간 전차선과 조가선 각도 높이를 반환
    Arguments:
        pos: 현재 측점
        gauge: 현재 건식게이지
        currentspan: 현재 스판
        contact_height: 전차선 높이
        system_heigh: 가고
        y: 보정 높이
    Returns:
        slope_degree1: 전차선 종단각도
        slope_degree2: 조가선 종단각도
        h1: 장력장치 전차선 높이
        h2: 장력장치 조가선 높이
        pererall_d: 보정 거리
        sta2: 보정된 전선 측점
    """
    # 장력장치 치수
    tension_device_length = 7.28

    # 전선 각도
    new_length = currentspan - tension_device_length  # 현재 span에서 장력장치까지의 거리
    pererall_d, vertical_offset = return_new_point(gauge, currentspan, tension_device_length)  # 선형 시작점에서 전선까지의 거리

    sta2 = pos + vertical_offset  # 전선 시작 측점
    h1 = 5.563936  # 장력장치 전차선 높이
    h2 = 6.04784  # 장력장치 조가선 높이

    slope_radian1 = math.atan((h1 - (contact_height + y)) / currentspan)  # 전차선 각도(라디안)
    slope_radian2 = math.atan((h2 - (contact_height + system_heigh)) / currentspan)  # 조가선 각도(라디안)

    slope_degree1 = math.degrees(slope_radian1)  # 전차선 각도(도)
    slope_degree2 = math.degrees(slope_radian2)  # 조가선 각도(도)

    return slope_degree1, slope_degree2, h1, h2, pererall_d, sta2

def offsets(n, s):
    if n == 1:
        return [0.0]
    if n == 2:
        return [-s * 0.5, s * 0.5]
    return [(i - (n - 1) / 2) * s * 0.5 for i in range(n)]