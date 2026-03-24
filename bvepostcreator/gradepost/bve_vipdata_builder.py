from gradepost.pitch_util import calculate_vertical_curve_radius, get_vertical_curve_type
from gradepost.vip_builder import VIPDATABuilder
from model.grade.vipdata import VIPdata


class BVEVIPDATABuilder(VIPDATABuilder):
    # 핵심로직(클래스화로 구조변경)
    def build(self, data,  broken_chain) -> list[VIPdata]:
        """
        주어진 종단 기울기 구간 데이터를 기반으로 VIP(Vertical Inflection Point) 정보를 생성합니다.

        각 구간은 시작점(BVC)과 끝점(EVC)을 기준으로 종곡선 제원을 계산하고,
        종곡선의 반경, 길이, 형태(오목/볼록)를 판별하여 VIPdata 객체로 반환합니다.

        Parameters:
            data: list[list[tuple[float, float]]]
                - 각 구간은 (station, slope) 튜플의 리스트로 구성되며,
                  station은 거리값(m), slope는 기울기(m/m)입니다.
                - 예: [[(1000.0, -0.025), (1100.0, 0.005)], [(1200.0, 0.005), (1300.0, -0.010)]]
            broken_chain: 파정값
        Returns:
            list[VIPdata]: VIPdata 객체들의 리스트
                - 각 VIPdata는 하나의 종곡선 구간에 대한 정보를 담고 있습니다.

        Notes:
            - 내부적으로 calculate_vertical_curve_radius() 및 get_vertical_curve_type()을 호출하여
              반지름과 곡선 유형을 결정합니다.
            - slope는 m/m 단위를 사용해야 하며, ‰ 단위일 경우 외부에서 변환이 필요합니다.
        """
        vipdatas: list[VIPdata] = []
        iscurve = False
        i = 1
        for section in data:
            if not section:
                continue
            # BVC, EVC 추출
            bvc_staion, prev_pitch = section[0]
            evc_staion, next_pitch = section[-1]
            vip_staion = (evc_staion + bvc_staion) / 2

            # 파정 적용
            bvc_staion += broken_chain
            evc_staion += broken_chain
            vip_staion += broken_chain

            # 종곡선 제원 계산
            vertical_length = evc_staion - bvc_staion  # 종곡선 길이
            # 종곡선 반경
            vertical_radius = calculate_vertical_curve_radius(vertical_length, prev_pitch, next_pitch)
            # 오목형 볼록형 판단
            seg = get_vertical_curve_type(prev_pitch, next_pitch)

            # 종곡선 여부 판단
            if len(section) < 3:
                isvcurve = False
            else:
                isvcurve = True
            vipdatas.append(VIPdata(
                VIPNO=i,
                isvcurve=isvcurve,
                seg=seg,
                vradius=vertical_radius,
                vlength=vertical_length,
                next_slope=next_pitch,
                prev_slope=prev_pitch,
                BVC_STA=bvc_staion,
                VIP_STA=vip_staion,
                EVC_STA=evc_staion
            )
            )
            i += 1

        return vipdatas