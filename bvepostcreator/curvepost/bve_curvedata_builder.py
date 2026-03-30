from common.file_io import try_read_file
from curvepost.base_builder import CurveDATABuilder
from curvepost.curve_util import CurveDirection
from curvepost.preprocessor import CurvePreprocessor
from model.curve.ipdata import IPdata
from model.grade.vipdata import VIPdata


class BVECurveDATABuilder(CurveDATABuilder):
    """BVE용 CURVE데이터빌더"""
    def preprocess(self, data, brokenchain):
        """전처리 메서드"""
        lines = try_read_file(data)
        lines = CurvePreprocessor.remove_duplicate_radius(lines)
        return CurvePreprocessor.process_sections(lines)

    # 핵심로직(클래스화로 구조변경)
    def build(self, data,  broken_chain):
        ipdatas: list[IPdata] = []
        i = 1
        for section in data:
            if not section:
                continue

            # 조건에 맞게 구간 종료 판단 (예: radius == 0)
            # 곡선 방향 판단
            direction = CurveDirection.LEFT if section[0][1] < 0 else CurveDirection.RIGHT

            # 완화곡선/원곡선 타입 판단
            if len(section) == 1:
                curvetype = '직선'
            elif len(section) == 2:
                curvetype = '원곡선'
            else:
                curvetype = '완화곡선'

            # 좌향일 때 완화곡선은 가장 큰 값, 원곡선은 가장 작은 값
            # 우향일 때 완화곡선은 가장 작은 값, 원곡선은 가장 큰 값
            # 0 제외한 필터링된 리스트 생성
            filtered_section = [row for row in section if row[1] != 0]
            if not filtered_section:
                # 모두 반경 0이면 무시
                continue

            # 가장 작은/큰 곡률반경 값
            min_value = min(filtered_section, key=lambda x: x[1])[1]
            max_value = max(filtered_section, key=lambda x: x[1])[1]

            # 원래 section에서 해당 값의 첫 인덱스 찾기
            min_index = next(i for i, row in enumerate(section) if row[1] == min_value)
            max_index = next(i for i, row in enumerate(section) if row[1] == max_value)
            pc_sta = 0.0
            cp_sta = 0.0
            if curvetype == '완화곡선':
                if direction == CurveDirection.LEFT:
                    selected_radius = max_value
                    selected_cant = section[max_index][2]
                    pc_sta = section[max_index][0]
                    cp_sta = section[max_index + 1][0]
                else:
                    selected_radius = min_value
                    selected_cant = section[min_index][2]
                    pc_sta = section[min_index][0]
                    cp_sta = section[min_index + 1][0]

            else:  # 원곡선
                if direction == CurveDirection.LEFT:
                    selected_radius = min_value
                    selected_cant = section[min_index][2]
                else:
                    selected_radius = max_value
                    selected_cant = section[max_index][2]

            if curvetype == '원곡선':
                # STA 결정 직후
                BC_STA = section[0][0]
                EC_STA = section[-1][0]
                BC_STA += broken_chain
                EC_STA += broken_chain

                # IPdata 생성 (예시, 필요에 따라 STA값 할당 조정)
                ipdata = IPdata(
                    IPNO=i,
                    curvetype=curvetype,
                    curve_direction=direction,
                    radius=abs(selected_radius),
                    cant=abs(selected_cant),
                    BC_STA=BC_STA,
                    EC_STA=EC_STA
                )
                ipdatas.append(ipdata)
                i += 1
            if curvetype == '완화곡선':
                sp_sta = section[0][0]
                pc_sta = pc_sta
                cp_sta = cp_sta
                ps_sta = section[-1][0]

                sp_sta += broken_chain
                pc_sta += broken_chain
                cp_sta += broken_chain
                ps_sta += broken_chain
                ipdata = IPdata(
                    IPNO=i,
                    curvetype=curvetype,
                    curve_direction=direction,
                    radius=abs(selected_radius),
                    cant=abs(selected_cant),
                    SP_STA=sp_sta,
                    PC_STA=pc_sta,
                    CP_STA=cp_sta,
                    PS_STA=ps_sta
                )
                ipdatas.append(ipdata)
                i += 1

        return ipdatas