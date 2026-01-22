from dataclasses import dataclass


@dataclass
class PreviewBuildResult:
    objects: list
    missing: list[str]
