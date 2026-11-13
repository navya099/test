# ==============================================================================
# 2. Civil 3D 스타일 종단 연산 엔진 (Profile Engine / Builder)
# ==============================================================================
from typing import List, Any

from profile.parabola import ProfileParabola
from profile.profile import CompositeProfile
from profile.tangent import ProfileTangent


class Civil3DProfileEngine:
    """
    PVI 리스트를 분석하여 대칭/비대칭 포물선 및 직선 세그먼트를 계산하고,
    순수 도메인 객체(CompositeProfile)로 조립해주는 빌더/엔진 클래스
    """

    @staticmethod
    def build(name: str, pvi_list: List[Any]) -> CompositeProfile:
        if len(pvi_list) < 2:
            raise ValueError("종단을 생성하려면 최소 2개 이상의 PVI(시점, 종점)가 필요합니다.")

        sorted_pvis = sorted(pvi_list, key=lambda p: p.station)
        n = len(sorted_pvis)

        # 1. 각 PVI 구간의 직선 경사(g) 계산
        grades = []
        for i in range(n - 1):
            d_sta = sorted_pvis[i + 1].station - sorted_pvis[i].station
            if d_sta <= 1e-9:
                raise ValueError(f"{sorted_pvis[i].name}와 {sorted_pvis[i + 1].name}의 측점이 중복되거나 역전되었습니다.")
            d_el = sorted_pvis[i + 1].elevation - sorted_pvis[i].elevation
            grades.append(d_el / d_sta)

        # 2. 중간 PVI별 종단곡선 제원(BVC, EVC, e, K값, 변곡점) 산출
        pvi_report = []
        curves = []
        for i in range(1, n - 1):
            pvi = sorted_pvis[i]
            g1 = grades[i - 1]
            g2 = grades[i]
            A = g2 - g1  # 대수적 경사 차

            if pvi.L1 is not None or pvi.L2 is not None:
                l1 = float(pvi.L1 or 0.0)
                l2 = float(pvi.L2 or 0.0)
            elif pvi.L is not None:
                l1 = float(pvi.L) * 0.5
                l2 = float(pvi.L) * 0.5
            else:
                l1 = l2 = 0.0

            total_L = l1 + l2
            bvc_sta = pvi.station - l1
            evc_sta = pvi.station + l2
            bvc_el = pvi.elevation - g1 * l1
            evc_el = pvi.elevation + g2 * l2

            # 종단곡선 유형 및 K값
            if total_L > 1e-9 and abs(A) > 1e-12:
                curve_type = "Crest (볼록)" if A < 0 else "Sag (오목)"
                k_val = total_L / abs(A * 100.0)
                e_offset = (A * l1 * l2) / (2.0 * total_L)

                extrema_sta = None
                extrema_el = None
                if g1 * g2 < 0:
                    if l1 > 0 and abs(e_offset) > 1e-12:
                        x1_zero = -g1 * (l1 ** 2) / (2.0 * e_offset)
                        if 0.0 <= x1_zero <= l1:
                            extrema_sta = bvc_sta + x1_zero
                            extrema_el = bvc_el + g1 * x1_zero + e_offset * ((x1_zero / l1) ** 2)
                    if extrema_sta is None and l2 > 0 and abs(e_offset) > 1e-12:
                        x2_zero = g2 * (l2 ** 2) / (2.0 * e_offset)
                        if 0.0 <= x2_zero <= l2:
                            extrema_sta = evc_sta - x2_zero
                            extrema_el = evc_el - g2 * x2_zero + e_offset * ((x2_zero / l2) ** 2)
            else:
                curve_type = "Tangent (꺾임)"
                k_val = 0.0
                e_offset = 0.0
                extrema_sta = None
                extrema_el = None

            c_info = {
                "pvi": pvi, "g1": g1, "g2": g2, "A": A,
                "l1": l1, "l2": l2, "total_L": total_L,
                "bvc_sta": bvc_sta, "bvc_el": bvc_el,
                "evc_sta": evc_sta, "evc_el": evc_el,
                "e_offset": e_offset, "k_val": k_val,
                "curve_type": curve_type,
                "extrema_sta": extrema_sta, "extrema_el": extrema_el
            }
            curves.append(c_info)
            pvi_report.append(c_info)

        # 3. 순수 엔티티 객체(ProfileEntity) 조립
        entities = []
        curr_sta = sorted_pvis[0].station
        curr_el = sorted_pvis[0].elevation

        for i in range(len(curves)):
            c = curves[i]
            if c["bvc_sta"] < curr_sta - 1e-7:
                raise ValueError(f"[{c['pvi'].name}] 종단곡선 시점(BVC={c['bvc_sta']:.2f})이 이전 곡선 종점({curr_sta:.2f})과 겹칩니다.")

            # 직선 경사 구간 추가
            if c["bvc_sta"] > curr_sta + 1e-9:
                entities.append(ProfileTangent(curr_sta, c["bvc_sta"], curr_el, c["g1"]))

            # 종단곡선 구간 추가
            if c["total_L"] > 1e-9:
                entities.append(ProfileParabola(
                    start_sta=c["bvc_sta"], end_sta=c["evc_sta"],
                    pvi_sta=c["pvi"].station,
                    bvc_el=c["bvc_el"], evc_el=c["evc_el"],
                    g1=c["g1"], g2=c["g2"],
                    l1=c["l1"], l2=c["l2"],
                    e_offset=c["e_offset"]
                ))

            curr_sta = c["evc_sta"]
            curr_el = c["evc_el"]

        # 마지막 종점까지의 직선 경사 구간 추가
        end_pvi = sorted_pvis[-1]
        if end_pvi.station < curr_sta - 1e-7:
            raise ValueError("마지막 종단곡선 종점(EVC)이 전체 선형 종점(EVP)을 초과합니다.")
        if end_pvi.station > curr_sta + 1e-9:
            entities.append(ProfileTangent(curr_sta, end_pvi.station, curr_el, grades[-1]))

        return CompositeProfile(name, entities, pvi_report)