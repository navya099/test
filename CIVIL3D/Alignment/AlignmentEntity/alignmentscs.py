from dataclasses import dataclass
from Alignment.AlignmentEntity.alignmentcurve import AlignmentCurve
from Alignment.AlignmentSubEntity.alignmentsubentityarc import AlignmentSubEntityArc
from Alignment.AlignmentSubEntity.alignmentsubentityspiral import AlignmentSubEntitySpiral


@dataclass
class AlignmentSCS(AlignmentCurve):
    """
    Alignment SpiralCurveSpiral 클래스. 이 클래스는 내부 나선형 하위 엔터티, 호 하위 엔터티, 외부 나선형 하위 엔터티로 구성된 AlignmentEntity를 나타냅니다.
    Attributes:
        arc: SCS 그룹의 호를 가져옵니다.
        greater_than_180: Arc 솔루션 각도가 180도보다 큰지 여부를 나타내는 bool 값을 가져오거나 설정합니다.
        spiral_in: SCS 그룹의 나선형을 얻습니다.
        spiral_out: SCS 그룹의 나선형을 얻습니다.
    """
    arc: AlignmentSubEntityArc = AlignmentSubEntityArc()
    greater_than_180: bool = False
    spiral_in: AlignmentSubEntitySpiral  = AlignmentSubEntitySpiral()
    spiral_out: AlignmentSubEntitySpiral = AlignmentSubEntitySpiral()

