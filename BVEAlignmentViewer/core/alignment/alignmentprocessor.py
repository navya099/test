from core.alignment.alginmentcalculator import AlignmentCalculator
from curvedirection import CurveDirection
from curvetype import CurveType
from model.bveroutedata import BVERouteData
from model.bvetrack import Curve
from model.ipdata import EndPoint, IPdata
from model.segment import CurveSegment, SpiralSegment
from vector3 import to2d
import math

class AlignmentProcessor:
    """
    BVERouteData 선형 생성을 stateless 처리하는 클래스
    """
    @staticmethod
    def process_endpoint(bvedata: BVERouteData, bp: bool) -> EndPoint:
        """BP 또는 EP 처리 메소드
        Args:
            bvedata: BVERouteData
            bp: bool
        Returns:
            EndPoint
        """
        coord3d = bvedata.coords[0] if bp else bvedata.coords[-1]
        dir3d = bvedata.directions[0] if bp else bvedata.directions[-1]
        coord2d = to2d(coord3d)
        azimuth = to2d(dir3d).toradian()

        return EndPoint(
            coord=coord2d,
            direction=azimuth,
        )
    def process_curve_section(self, calculator: AlignmentCalculator, section: list[Curve], ipno: int) -> list[IPdata]:
        """곡선 구간 처리 메소드"""
        curvetype = AlignmentCalculator.define_iscurve(section)
        if curvetype in (CurveType.Simple, CurveType.Reverse):
            return self._process_simple_curve(calculator, section, ipno)
        elif curvetype == CurveType.Compound:
            return self._process_complex_curve(calculator, section, ipno)
        elif curvetype == CurveType.Spiral:
            return self._process_spiral_curve(section, ipno)
        else:
            raise ValueError(f"Unknown CurveType: {curvetype}")

    # ---------------------
    # 단곡선 처리
    def _process_simple_curve(self, calculator: AlignmentCalculator,section: list[Curve], ipno: int | str) -> list[IPdata]:
        bc_curve, ec_curve = section[0], section[-1]
        bc_sta, ec_sta = bc_curve.station, ec_curve.station
        cl = ec_sta - bc_sta
        r, _ = AlignmentCalculator.define_section_radius(section, CurveType.Simple)

        curve_direction = CurveDirection.RIGHT if r > 0 else CurveDirection.LEFT

        r, ia, tl, m, sl = AlignmentCalculator.calculate_curve_geometry(r, cl)

        # ia가 180° 이상이면 분할메소드 처리

        if ia > math.pi:
            # 재귀호출
            pcc_curve = calculator.split_simplecurve_section(bc_curve, ec_curve, r, curve_direction)
            section1 = [bc_curve, pcc_curve]
            section2 = [pcc_curve, ec_curve]
            ipdata_list = []
            ipdata_list.extend(self._process_simple_curve(calculator, section1, f"{ipno}-1"))
            ipdata_list.extend(self._process_simple_curve(calculator, section2, f"{ipno}-2"))
            return ipdata_list

        bc_coord, ec_coord = bc_curve.coord, ec_curve.coord
        bc_azimuth, ec_azimuth = bc_curve.direction, ec_curve.direction
        center_coord = AlignmentCalculator.calculate_curve_center(bc_coord, ec_coord, r, curve_direction)
        ip_coord = AlignmentCalculator.calculate_intersection_point(bc_coord, ec_coord, bc_azimuth, ec_azimuth)

        curve_segment = self.create_curve_segment(r, bc_sta, ec_sta,
                                                   bc_coord, ec_coord, center_coord,
                                                   tl, cl, sl, m,
                                                   bc_azimuth, ec_azimuth)
        ipdata = IPdata(ipno=ipno,
                        curvetype=CurveType.Simple,
                        curve_direction=curve_direction,
                        radius=r,
                        ia=ia,
                        coord=ip_coord,
                        segment=[curve_segment])

        return [ipdata]

    # ---------------------
    # 복심곡선 처리
    def _process_complex_curve(self, calculator: AlignmentCalculator, section: list[Curve], ipno: int) -> list[IPdata]:
        """
        복심곡선 처리 메소드
        Args:
            section: 구간
            ipno: ip번호

        Returns:
            IPdata
        """
        # BC,PCC,EC 언팩
        bc_curve, pcc_curve, ec_curve = section[0], section[1], section[-1]
        bc_sta, pcc_sta, ec_sta = bc_curve.station, pcc_curve.station, ec_curve.station
        # 전체 cl
        cl = ec_sta - bc_sta
        # 개별 cl
        cl1, cl2 = pcc_sta - bc_sta, ec_sta - pcc_sta
        cl_list = cl1, cl2
        radii = AlignmentCalculator.define_section_radius(section, CurveType.Compound)
        # 복심곡선 반경1, 반경2
        r1, r2 = radii
        curve_direction = CurveDirection.RIGHT if r1 > 0 else CurveDirection.LEFT
        curve_segment_list = []

        # ----- 1) total IA 빠른 계산 -----
        ia_list = []
        for r, cl in zip(radii, cl_list):
            _, ia, _, _, _ = AlignmentCalculator.calculate_curve_geometry(r, cl)
            ia_list.append(ia)

        total_ia = sum(ia_list)

        # ----- 2) IA > 180° 이면 즉시 분할 후 SimpleCurve로 위임 -----
        if total_ia > math.pi:
            ipdata_list = []
            for (r, cl, bc_seg, ec_seg, ia) in [
                (r1, cl1, bc_curve, pcc_curve, ia_list[0]),
                (r2, cl2, pcc_curve, ec_curve, ia_list[1]),
            ]:
                # IA가 90° 넘는 반경만 분할
                if ia > math.pi / 2:
                    pcc_curve2 = calculator.split_simplecurve_section(bc_seg, ec_seg, r, curve_direction)
                    section1 = [bc_seg, pcc_curve2]
                    section2 = [pcc_curve2, ec_seg]
                    for i, sec in enumerate([section1, section2], start=1):
                        ipdata_list.extend(self._process_simple_curve(calculator, sec, f'{ipno}-{i + 1}'))
                else:
                    ipdata_list.extend(self._process_simple_curve(calculator,[bc_seg, ec_seg], f'{ipno}-{1}'))
            return ipdata_list

        # 정상로직
        ia_list = []
        for i, (r, cl) in enumerate(zip(radii, cl_list)):
            # 각 구간 BC, EC 설정
            if i == 0:
                bc_curve_seg, ec_curve_seg = bc_curve, pcc_curve
            else:
                bc_curve_seg, ec_curve_seg = pcc_curve, ec_curve
            r, ia, tl, m, sl = AlignmentCalculator.calculate_curve_geometry(r, cl)
            ia_list.append(ia)
            bc_coord, ec_coord = bc_curve_seg.coord, ec_curve_seg.coord
            bc_azimuth, ec_azimuth = bc_curve_seg.direction, ec_curve_seg.direction
            center_coord = AlignmentCalculator.calculate_curve_center(bc_coord, ec_coord, r, curve_direction)
            curve_segment_list.append(
                self.create_curve_segment(r, bc_sta, ec_sta,
                                           bc_coord, ec_coord, center_coord,
                                           tl, cl, sl, m,
                                           bc_azimuth, ec_azimuth)
            )
        # 대표 IP제원 다시계산
        ia = sum(ia_list)
        ip_coord = AlignmentCalculator.calculate_intersection_point(bc_curve.coord, ec_curve.coord, bc_curve.direction, ec_curve.direction)
        return [IPdata(ipno=ipno,
                       curvetype=CurveType.Compound,
                       curve_direction=curve_direction,
                       radius=radii,
                       ia=ia,
                       coord=ip_coord,
                       segment=curve_segment_list)]

    # ---------------------
    # 완화곡선 처리
    def _process_spiral_curve(self, section: list[Curve], ipno: int) -> list[IPdata]:
        #원곡선 반경
        r, _ = AlignmentCalculator.define_section_radius(section, CurveType.Spiral)
        curve_direction = CurveDirection.RIGHT if r > 0 else CurveDirection.LEFT

        # 완화곡선 인덱스 찾기
        pc_idx, cp_idx = AlignmentCalculator.define_spiral_spec(section, direction=curve_direction)
        sp_curve, ps_curve = section[0], section[-1]
        pc_curve, cp_curve = section[pc_idx], section[cp_idx]

        #언팩
        sp_sta, pc_sta, cp_sta, ps_sta = sp_curve.station, pc_curve.station, cp_curve.station, ps_curve.station
        sp_coord, pc_coord, cp_coord, ps_coord = sp_curve.coord, pc_curve.coord, cp_curve.coord, ps_curve.coord
        sp_direction, pc_direction, cp_direction, ps_direction = sp_curve.direction, pc_curve.direction, cp_curve.direction, ps_curve.direction

        cl = ps_sta - sp_sta #전체 cl
        l1 = pc_sta - sp_sta #시점 완화곡선 길이
        l2 = ps_sta - cp_sta #종점 완화곡선 길이
        lc = cp_sta - pc_sta #원곡선 길이
        ia = ps_curve.direction - sp_curve.direction #교각
        #ip좌표
        ip_coord = AlignmentCalculator.calculate_intersection_point(sp_curve.coord, ps_curve.coord, sp_curve.direction, ps_curve.direction)

        # 세그먼트 계산
        segment_list = []
        # 시점 완화곡선 여부
        if l1 > 0:
            spiral_parameter = AlignmentCalculator.calculate_spiralcurve_geometry(r, l1, ia)
            segment_list.append(self.create_spiral_segment(spiral_parameter, sp_sta, pc_sta, l1, sp_curve,pc_curve, isstart=True)
            )

        # 중간 원곡선
        if lc > 0:
            r, ia2, tl, m, sl = AlignmentCalculator.calculate_curve_geometry(r, lc)
            center_coord = AlignmentCalculator.calculate_curve_center(pc_coord, cp_coord, r, curve_direction)
            segment_list.append(
                self.create_curve_segment(
                    r, pc_sta, cp_sta,
                    pc_coord, cp_coord, center_coord,
                    tl, lc, sl, m,
                    pc_direction, cp_direction
                )
            )

        # 종점 완화곡선 여부
        if l2 > 0:
            start = False
            spiral_parameter = AlignmentCalculator.calculate_spiralcurve_geometry(r, l2, ia)
            segment_list.append(self.create_spiral_segment(spiral_parameter, cp_sta, ps_sta, l2, cp_curve, ps_curve, isstart=False)
                                )
        return [IPdata(ipno=ipno,
                      curvetype=CurveType.Spiral,
                      curve_direction=curve_direction,
                      radius=r,
                      ia=ia,
                      coord=ip_coord,
                      segment=segment_list
                      )]
    @staticmethod
    def create_curve_segment(r, bc_sta, ec_sta, bc_coord, ec_coord, center_coord,
                              tl,cl,sl,m, bc_azimuth, ec_azimuth) -> CurveSegment:
        """
        Private 메소드: CurveSegment객체 생성
        Args:
            r (float): 곡선 반경
            bc_sta (float): BC 측점
            ec_sta (float): EC 측점
            bc_coord (Vector2): BC 좌표
            ec_coord (Vector2): EC 좌표
            center_coord (Vector2): 곡선 중심 좌표
            tl (float): 접선장
            cl (float): 곡선장
            sl (float): 외할장
            m (float): 중앙종거
            bc_azimuth (float): 시작 방위각 라디안
            ec_azimuth (float): 종료 방위각 라디안
        Returns:
            CurveSegment
        """
        return CurveSegment(
            radius=r,
            start_sta=bc_sta,
            end_sta=ec_sta,
            start_coord=bc_coord,
            end_coord=ec_coord,
            center_coord=center_coord,
            tl=tl,
            length=cl,
            sl=sl,
            m=m,
            start_azimuth=bc_azimuth,
            end_azimuth=ec_azimuth,
        )

    @staticmethod
    def create_spiral_segment(parameter: tuple, start_sta: float, end_sta: float, length: float, start: Curve, end: Curve, isstart=True) -> SpiralSegment:
        """
        Private 메소드: SpiralSegment객체 생성
        Args:
            parameter(tuple): 완화곡선 파라메터 튜플 create_curve_segment
            start_sta(float): 시작 측점
            end_sta(float): 끝 측점
            length(float): 길이
            start(Curve): 시작 Curve객체
            end(Curve): 끝 Curve객체
            isstart(bool): 시작 완화곡선 여부
        Returns:
            SpiralSegment
        """

        x1, x2, w13, y1, w15, f, s, k, w, tl, lc, cl, sl, ia2, c, xb, b = parameter
        return SpiralSegment(
            start_sta=start_sta,
            end_sta=end_sta,
            length=length,
            start_coord=start.coord,
            end_coord=end.coord,
            start_azimuth=start.direction,
            end_azimuth=end.direction,
            x1=x1,
            x2=x2,
            w13=w13,
            y1=y1,
            w15=w15,
            f=f,
            s=s,
            k=k,
            w=w,
            tl=tl,
            lc=lc,
            total_length=cl,
            sl=sl,
            ria=ia2,
            c=c,
            xb=xb,
            b=b,
            isstarted=isstart,
        )