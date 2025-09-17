from core.alignment.alginmentcalculator import AlignmentCalculator
from core.alignment.alignmentprocessor import AlignmentProcessor
from model.bveroutedata import BVERouteData
from model.ipdata import IPdata

class AlignmentBuilder:
    """
    BVERouteData로 IPdata를 생성하는 stateless클래스
    """
    @staticmethod
    def build_ipdata_from_sections(bvedata: BVERouteData) -> list[IPdata]:
        """
        BVERouteData 속성으로 IPdata 리스트 생성 스태틱 메소드.
        BP -> 곡선 -> EP 순서 처리
        Args:
            bvedata(BVERouteData): BVERouteData
        Returns:
            list[IPdata]
        """
        ipdata_list = []
        #계산클래스 생성
        calculator = AlignmentCalculator()
        #처리 프로세서 생성
        processor = AlignmentProcessor()
        #구간 구분
        sections = AlignmentCalculator.split_by_curve_sections(bvedata.curves)

        for i, section in enumerate(sections):
            if i == 0:
                # BP
                ipdata_list.append(processor.process_endpoint(bvedata, bp=True))
            else:  # 곡선구간 처리
                curvesection_ipdata_list = processor.process_curve_section(calculator, section, ipno=i)
                ipdata_list.extend(curvesection_ipdata_list)

        # EP 추가
        ipdata_list.append(processor.process_endpoint(bvedata, bp=False))

        return ipdata_list