from dataclasses import dataclass


@dataclass
class PreviewBuildResult:
    objects: list["PreviewLayerObject"]  # 모든 레이어 통합
    missing: list[str]


