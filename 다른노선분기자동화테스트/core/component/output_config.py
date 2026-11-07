# core/component/output_config.py (신규)
from dataclasses import dataclass

@dataclass(frozen=True)
class OutputConfig:
    """출력 옵션을 담는 컴포넌트"""
    format: str            # 'console', 'csv', 'txt'
    file_path: str = ""    # csv/txt일 경우 저장 경로