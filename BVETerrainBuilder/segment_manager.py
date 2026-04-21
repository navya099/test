from shapely.geometry import Point

def _create_buffered(xy_list, buffer_m: int):
    # 구간 분할 설정
    segments = []
    for idx, (x, y) in enumerate(xy_list, start=1):

        point = Point(x, y)  # 샘플링된 점 자체를 중심점으로 사용
        buffered = point.buffer(buffer_m)  # 좌우 1km 버퍼
        segments.append(buffered.bounds)

    # 마지막 점도 별도로 저장
    last_point = Point(xy_list[-1][0], xy_list[-1][1])
    buffered_last = last_point.buffer(buffer_m)
    last_segment = buffered_last.bounds

    return segments, last_segment