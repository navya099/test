"""프로젝트 저장/불러오기 (JSON)"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

from src.railway_alignment.core.constants import Config

logger = logging.getLogger(__name__)


PROJECT_VERSION = "1.0"
PROJECT_EXTENSION = ".rwp"
PROJECT_FILETYPES = [
    ("Railway Project", "*.rwp"),
    ("JSON", "*.json"),
    ("All files", "*.*"),
]
RECENT_PROJECTS_MAX = 10


class ProjectIOError(Exception):
    """프로젝트 I/O 예외"""


@dataclass
class ProjectData:
    """프로젝트 전체 상태"""
    version: str = PROJECT_VERSION
    saved_at: str = ""
    app: str = "railway_alignment_v10"

    # 입력
    raw_lines: list[list[str]] = field(default_factory=list)
    source_file: str = ""

    # 계산 파라미터
    unit: int = Config.DEFAULT_UNIT
    start_sta: float = Config.DEFAULT_START_STA
    design_speed: int = Config.DEFAULT_DESIGN_SPEED
    ballast: str = "자갈도상"

    # 오버라이드 (ip_no → 값)
    auto_flags: dict[int, bool] = field(default_factory=dict)
    type_overrides: dict[int, str] = field(default_factory=dict)
    parameter_overrides: dict[int, dict[str, float]] = field(default_factory=dict)

    # 도면 설정
    dxf_config: dict = field(default_factory=dict)


def save_project(path: Path | str, data: ProjectData) -> Path:
    """프로젝트 저장"""
    path = Path(path)
    data.version = PROJECT_VERSION
    data.saved_at = datetime.now().isoformat(timespec="seconds")

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(asdict(data), ensure_ascii=False, indent=2)
        path.write_text(payload, encoding="utf-8")
        logger.info("프로젝트 저장: %s", path)
        return path
    except Exception as e:
        logger.exception("프로젝트 저장 실패")
        raise ProjectIOError(f"프로젝트 저장 실패: {e}") from e


def load_project(path: Path | str) -> ProjectData:
    """프로젝트 로드 + 검증"""
    path = Path(path)
    if not path.exists():
        raise ProjectIOError(f"프로젝트 파일이 없습니다: {path}")

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ProjectIOError(f"JSON 파싱 실패: {e}") from e
    except Exception as e:
        raise ProjectIOError(f"프로젝트 로드 실패: {e}") from e

    version = raw.get("version", "0.0")
    if version.split(".")[0] != PROJECT_VERSION.split(".")[0]:
        raise ProjectIOError(
            f"지원하지 않는 프로젝트 버전: {version} (지원: {PROJECT_VERSION})"
        )

    if not raw.get("raw_lines"):
        raise ProjectIOError("유효하지 않은 프로젝트: raw_lines 없음")

    try:
        return ProjectData(
            version=raw.get("version", PROJECT_VERSION),
            saved_at=raw.get("saved_at", ""),
            app=raw.get("app", ""),
            raw_lines=raw["raw_lines"],
            source_file=raw.get("source_file", ""),
            unit=int(raw.get("unit", Config.DEFAULT_UNIT)),
            start_sta=float(raw.get("start_sta", Config.DEFAULT_START_STA)),
            design_speed=int(raw.get("design_speed", Config.DEFAULT_DESIGN_SPEED)),
            ballast=raw.get("ballast", "자갈도상"),
            auto_flags={
                int(k): bool(v) for k, v in (raw.get("auto_flags") or {}).items()
            },
            type_overrides={
                int(k): str(v) for k, v in (raw.get("type_overrides") or {}).items()
            },
            parameter_overrides={
                int(k): {
                    "m": float(vv["m"]),
                    "v": float(vv["v"]),
                    "z": float(vv["z"]),
                }
                for k, vv in (raw.get("parameter_overrides") or {}).items()
            },
            dxf_config=raw.get("dxf_config") or {},
        )
    except (KeyError, ValueError, TypeError) as e:
        raise ProjectIOError(f"프로젝트 스키마 오류: {e}") from e


# ============================================================
# 최근 프로젝트 목록
# ============================================================
def _recent_path() -> Path:
    return Path.home() / ".railway_alignment" / "recent_projects.json"


def load_recent_projects() -> list[str]:
    """최근 프로젝트 경로 목록 (존재하는 것만)"""
    path = _recent_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else []
    except Exception:
        return []
    # 존재하는 파일만 필터
    return [p for p in items if isinstance(p, str) and Path(p).exists()]


def add_recent_project(project_path: Path | str) -> None:
    """최근 프로젝트 목록에 추가 (중복 제거, 최대 10개)"""
    project_path = str(Path(project_path).resolve())
    recent = load_recent_projects()
    if project_path in recent:
        recent.remove(project_path)
    recent.insert(0, project_path)
    recent = recent[:RECENT_PROJECTS_MAX]

    path = _recent_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(recent, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        logger.exception("최근 프로젝트 목록 저장 실패")


def clear_recent_projects() -> None:
    """최근 프로젝트 목록 초기화"""
    path = _recent_path()
    try:
        if path.exists():
            path.unlink()
    except Exception:
        logger.exception("최근 프로젝트 목록 삭제 실패")