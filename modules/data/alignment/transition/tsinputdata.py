from dataclasses import dataclass, field

from AutoCAD.point2d import Point2d
from curvedirection import CurveDirection
from data.alignment.geometry.spiral.params import TransitionCurveParams


@dataclass
class TransitionDesignInput:
    """
    완화곡선 설계 입력정보
    segment group의 다음 정보를 받아서 저장
    Attributes:
        bp_coordinate: BP좌표
        ip_coordinate: IP좌표
        ep_coordinate: EP좌표
        radius: 곡선반경
        internal_angle: 교각
        bp_azimuth: 시작 방위각
        ep_azimuth: 끝 방위각
        direction: 곡선 방향
        entry_params: 시작 완화곡선 파라메터 정보
        exit_params: 끝 완화곡선 파라메터 정보
        issync: 비대칭 여부
    """

    # 입력 조건
    bp_coordinate: Point2d = field(default_factory=lambda: Point2d(0, 0))
    ip_coordinate: Point2d = field(default_factory=lambda: Point2d(0, 0))
    ep_coordinate: Point2d = field(default_factory=lambda: Point2d(0, 0))
    radius: float = 0.0
    internal_angle: float = 0.0
    bp_azimuth: float = 0.0
    ep_azimuth: float = 0.0
    direction: CurveDirection = CurveDirection.NULL

    # 진입 완화곡선
    entry_params: TransitionCurveParams = TransitionCurveParams
    # 진출 완화곡선
    exit_params: TransitionCurveParams = TransitionCurveParams

    #비대칭 여부
    issync: bool = False