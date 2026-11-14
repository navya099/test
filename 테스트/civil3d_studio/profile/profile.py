from typing import List

from profile.profile_engine import Civil3DProfileEngine
from profile.profile_entity import ProfileEntity
from profile.pvi import PVIPoint


class Profile:
    """전체 종단 선형 컨테이너 및 조회 순수 객체"""
    def __init__(self, name: str, entities: List[ProfileEntity], pvi_report: List[dict], pvi_list: List[PVIPoint]):
        self.name = name
        self.entities = entities
        self.pvi_report = pvi_report
        self.pvi_list = pvi_list  # <--- 이 부분이 추가되어야 합니다!

    @property
    def start_station(self) -> float:
        return self.entities[0].start_sta if self.entities else 0.0

    @property
    def end_station(self) -> float:
        return self.entities[-1].end_sta if self.entities else 0.0

    @classmethod
    def create(
            cls,
            name: str,
            pvi_list: list[PVIPoint]
    ) -> "Profile":

        return Civil3DProfileEngine.build(
            name=name,
            pvi_list=pvi_list,
        )

    def elevation_and_grade_at(self, station: float):
        """
        특정 측점에서의 계획고(EL) 및 경사(Grade) 조회
        :return: (elevation_m, grade_decimal)
        """
        if station < self.start_station - 1e-9 or station > self.end_station + 1e-9:
            raise ValueError(f"측점({station})이 종단 선형 범위({self.start_station} ~ {self.end_station})를 벗어났습니다.")

        for ent in self.entities:
            if ent.start_sta - 1e-9 <= station <= ent.end_sta + 1e-9:
                return ent.elevation_and_grade_at(station)

        raise RuntimeError("측점에 해당하는 종단 세그먼트를 찾지 못했습니다.")

    def print_profile_report(self):
        """Civil 3D 종단 계산서(PVI Report) 출력"""
        print(f"\n======================= [{self.name}] Civil 3D 종단 계산서 (PVI Report) =======================")
        print(f"시점(BVP) STA: {self.start_station:.3f}m | 종점(EVP) STA: {self.end_station:.3f}m")
        print("-" * 115)
        print(f"{'PVI':<6} | {'유형':<13} | {'PVI 측점':<10} | {'PVI EL':<9} | {'g1(%)':<8} | {'g2(%)':<8} | {'L1/L2(m)':<11} | {'K값':<7} | {'극점(High/Low)'}")
        print("-" * 115)
        for r in self.pvi_report:
            pvi = r["pvi"]
            l_str = f"{r['l1']:.0f}/{r['l2']:.0f}"
            ext_str = f"STA {r['extrema_sta']:.2f} (EL {r['extrema_el']:.3f})" if r["extrema_sta"] else "-"
            print(
                f"{pvi.name:<6} | {r['curve_type']:<13} | {pvi.station:<10.3f} | {pvi.elevation:<9.3f} | "
                f"{r['g1']*100:<+8.3f} | {r['g2']*100:<+8.3f} | {l_str:<11} | {r['k_val']:<7.2f} | {ext_str}"
            )
        print("=" * 115)