from core.wire.singlewire import SingleWire
from utils.math_util import calculate_curve_angle, calculate_slope


class CommonWireProcessor:
    def __init__(self):
        pass
    def run(self, polyline_with_sta, index ,
            pos, next_pos ,current_z, next_z, start: tuple[float, float], end: tuple[float, float], pitch_angle, label):
        """공통 전선 생성기
        Args:
            polyline_with_sta: 폴리선
            index: 인덱스
            pos: 시작 측점
            next_pos: 끝 측점
            current_z: 현재 z
            next_z: 다음 z
            start: 시작 좌표
            end: 끝 좌표
            pitch_angle: 구배 각도
            label: 라벨
        Returns:
            SingleWire: 전선 객체
        """

        x1, y1 = start
        x2, y2 = end
        currentspan = next_pos - pos
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos,
                                               x1, x2)
        topdown_angle = calculate_slope(current_z + y1,next_z + y2, currentspan) - pitch_angle

        return SingleWire(index=index, offset=start,adjusted_angle=adjusted_angle,topdown_angle=topdown_angle, label=label)
