from dataclasses import dataclass


@dataclass
class SubassemblyLink:
    """
    표준횡단 서브어셈블리 링크 (차선, 길어깨, 측구, 법면 등)
    - use_superelevation=True 이면 편경사 테이블의 좌/우 경사를 자동 적용
    - use_superelevation=False 이면 고정 경사(fixed_slope) 적용
    """
    code_name: str              # 형상선(Feature Line) 포인트 코드 (예: "ETW", "EPS", "Hinge", "Daylight")
    width: float                # 수평 폭원 (m, 양수)
    fixed_slope: float = -0.02  # 고정 횡단경사 (예: -0.04 = -4%)
    use_superelevation: bool = False