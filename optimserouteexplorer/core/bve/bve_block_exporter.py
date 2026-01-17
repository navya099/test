from core.bve.curveblock import Curveblock
from core.bve.pitchblock import PitchBlock
from geometry.curvesegment import CurveSegment

class BVEBlcokExporter:
    @staticmethod
    def export_curve_info(curve_segments: list[CurveSegment],start_sta, end_sta, interval=25):
        """
        25m 간격으로 곡선반경 생성
        :param curve_segments: 곡선 세그먼트 리스트
        :param interval: 출력 간격 (기본 25m)

        Args:
            end_sta: 끝 측점
            start_sta: 시작 측점

        """
        start_sta = int(start_sta)
        end_sta = int(end_sta)

        blocks = []
        for sta in range(start_sta,end_sta + 1, interval):
            radius = 0
            cant = 0
            for seg in curve_segments:
                start = seg.bc_sta
                end = seg.ec_sta
                r = seg.radius
                c = 0.0

                if start <= sta <= end:
                    radius = r
                    cant = c
                    break
            blocks.append(Curveblock(sta=sta,radius=radius, cant=cant))
        return blocks

    @staticmethod
    def export_pitch_info(pitch_segments, start_sta, end_sta, interval=25):
        start_sta = int(start_sta)
        end_sta = int(end_sta)
        # STA 오름차순 정렬
        pitch_segments.sort(key=lambda x: x[0])

        blocks = []
        current_pitch = 0
        for sta in range(start_sta, end_sta + 1, interval):
            for start, p in reversed(pitch_segments):  # 역순 탐색
                if start <= sta:
                    current_pitch = p
                    break
            blocks.append(PitchBlock(sta=sta, pitch=current_pitch))

        return blocks