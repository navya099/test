"""BVE 곡선 파일 기반 곡선레일(5m) 설치 구문 생성 핵심 로직.

UI(Tkinter 등) 의존성이 없으며, 다른 프로젝트에서 import하여
메모리 기반 또는 파일 기반으로 재사용할 수 있습니다.
"""
from __future__ import annotations

import copy
import csv
import logging
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, Sequence

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------
INCREMENT = 5            # 계산 간격 (m)
BLOCK_LENGTH = 25        # BVE 블록 단위 (m)
GAUGE_MM = 1500          # 궤간 (mm)
M_TO_MM = 1000

ALIGNMENT_TYPES = ("일반철도", "도시철도", "고속철도", "준고속철도")

STRUCTURE_BRIDGE = "교량"
STRUCTURE_TUNNEL = "터널"
STRUCTURE_EARTHWORK = "토공"

TRACK_CONCRETE = "콘크리트도상"
TRACK_BALLAST = "자갈도상"

CURVE = "곡선"
STRAIGHT = "직선"

X_PATTERN = {0: "zero", 1: "o1", 2: "o2", 3: "o2", 4: "o1"}
Y_PATTERN = {0: "m1", 1: "m2", 2: "zero", 3: "m2_neg", 4: "m1_neg"}


# ---------------------------------------------------------------------------
# 데이터 모델
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CurvePoint:
    sta: float
    radius: float
    cant: float


@dataclass(frozen=True)
class StructureSegment:
    name: str
    start: float
    end: float


@dataclass
class StructureData:
    bridge: list[StructureSegment]
    tunnel: list[StructureSegment]


@dataclass(frozen=True)
class FreeObjPoint:
    sta: float
    x: float
    y: float
    z: float


@dataclass
class GenerationResult:
    freeobj_lines: list[str]
    railtype_lines: list[str]
    freeobj_points: list[FreeObjPoint]


# ---------------------------------------------------------------------------
# 기본 인덱스 설정 (노선별)
# ---------------------------------------------------------------------------
_BASE_GENERAL = {
    "freeobj": {
        CURVE: {
            STRUCTURE_TUNNEL: {TRACK_CONCRETE: 473, TRACK_BALLAST: 228},
            STRUCTURE_EARTHWORK: {TRACK_CONCRETE: 465, TRACK_BALLAST: 449},
            STRUCTURE_BRIDGE: {TRACK_CONCRETE: 465, TRACK_BALLAST: 449},
        },
        STRAIGHT: 499,
    },
    "railtype": {
        CURVE: 4,
        STRAIGHT: {
            STRUCTURE_TUNNEL: {TRACK_CONCRETE: 25, TRACK_BALLAST: 17},
            STRUCTURE_EARTHWORK: {TRACK_CONCRETE: 23, TRACK_BALLAST: 9},
            STRUCTURE_BRIDGE: {TRACK_CONCRETE: 23, TRACK_BALLAST: 9},
        },
    },
}

_URBAN = {
    "freeobj": {
        CURVE: {
            STRUCTURE_TUNNEL: {TRACK_CONCRETE: 473, TRACK_BALLAST: 228},
            STRUCTURE_EARTHWORK: {TRACK_CONCRETE: 465, TRACK_BALLAST: 228},
            STRUCTURE_BRIDGE: {TRACK_CONCRETE: 465, TRACK_BALLAST: 228},
        },
        STRAIGHT: 499,
    },
    "railtype": _BASE_GENERAL["railtype"],
}

_HIGH_SPEED = {
    "freeobj": {
        CURVE: {
            STRUCTURE_TUNNEL: {TRACK_CONCRETE: 658, TRACK_BALLAST: 659},
            STRUCTURE_BRIDGE: {TRACK_CONCRETE: 657, TRACK_BALLAST: 656},
            STRUCTURE_EARTHWORK: {TRACK_CONCRETE: 657, TRACK_BALLAST: 656},
        },
        STRAIGHT: 499,
    },
    "railtype": {
        CURVE: 4,
        STRAIGHT: {
            STRUCTURE_TUNNEL: {TRACK_CONCRETE: 114, TRACK_BALLAST: 115},
            STRUCTURE_EARTHWORK: {TRACK_CONCRETE: 12, TRACK_BALLAST: 7},
            STRUCTURE_BRIDGE: {TRACK_CONCRETE: 12, TRACK_BALLAST: 7},
        },
    },
}

_DEFAULT_VALUES = {
    "일반철도": _BASE_GENERAL,
    "준고속철도": _BASE_GENERAL,
    "도시철도": _URBAN,
    "고속철도": _HIGH_SPEED,
}


def get_default_values(alignment_type: str) -> dict:
    """노선 유형별 기본 인덱스 딕셔너리(깊은 복사)를 반환."""
    if alignment_type not in _DEFAULT_VALUES:
        raise ValueError(f"알 수 없는 노선 유형: {alignment_type}")
    return copy.deepcopy(_DEFAULT_VALUES[alignment_type])


# ---------------------------------------------------------------------------
# 파일 입출력 (순수 경로 기반)
# ---------------------------------------------------------------------------
def read_curve_csv(
    path: str | Path,
    encodings: Sequence[str] = ("utf-8", "euc-kr"),
) -> list[list[str]]:
    """CURVE_INFO 파일을 읽어 2차원 문자열 리스트로 반환."""
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"곡선 파일을 찾을 수 없습니다: {file_path}")

    last_error: UnicodeDecodeError | None = None
    for encoding in encodings:
        try:
            with file_path.open("r", encoding=encoding) as f:
                return list(csv.reader(f))
        except UnicodeDecodeError as e:
            logger.debug("%s 디코딩 실패 (%s): %s", encoding, file_path, e)
            last_error = e

    raise UnicodeDecodeError(
        last_error.encoding if last_error else "unknown",
        last_error.object if last_error else b"",
        last_error.start if last_error else 0,
        last_error.end if last_error else 0,
        f"지원 인코딩({', '.join(encodings)})으로 파일을 읽을 수 없습니다: {file_path}",
    )


def save_lines(lines: Iterable[str], save_path: str | Path) -> Path:
    """문자열 라인을 UTF-8 파일로 저장하고 저장된 Path를 반환."""
    target = Path(save_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        f.writelines(lines)
    logger.info("파일 저장 완료: %s", target)
    return target


def load_structure_section(filepath: str | Path) -> StructureData:
    """구조물 측점 엑셀(.xlsx)에서 교량/터널 구간을 로드."""
    excel_path = Path(filepath)
    if not excel_path.is_file():
        raise FileNotFoundError(f"구조물 엑셀 파일을 찾을 수 없습니다: {excel_path}")

    bridge_list: list[StructureSegment] = []
    tunnel_list: list[StructureSegment] = []

    df_bridge = pd.read_excel(excel_path, sheet_name="교량", header=None)
    if not df_bridge.empty:
        df_bridge.columns = ["br_NAME", "br_START_STA", "br_END_STA", "br_LENGTH"]
        for _, row in df_bridge.iterrows():
            bridge_list.append(
                StructureSegment(
                    name=str(row["br_NAME"]),
                    start=float(row["br_START_STA"]),
                    end=float(row["br_END_STA"]),
                )
            )

    df_tunnel = pd.read_excel(excel_path, sheet_name="터널", header=None)
    if not df_tunnel.empty:
        df_tunnel.columns = ["tn_NAME", "tn_START_STA", "tn_END_STA", "tn_LENGTH"]
        for _, row in df_tunnel.iterrows():
            tunnel_list.append(
                StructureSegment(
                    name=str(row["tn_NAME"]),
                    start=float(row["tn_START_STA"]),
                    end=float(row["tn_END_STA"]),
                )
            )

    return StructureData(bridge=bridge_list, tunnel=tunnel_list)


# ---------------------------------------------------------------------------
# 곡선 정보 파싱
# ---------------------------------------------------------------------------
def parsing_curveinfo(lines: Sequence[Sequence[str]]) -> list[CurvePoint]:
    """CSV 행 목록을 CurvePoint 리스트로 파싱."""
    curveinfo: list[CurvePoint] = []
    for line in lines:
        if not line:
            continue
        try:
            sta = float(line[0])
            radius = float(line[1])
        except (ValueError, IndexError) as e:
            logger.warning("곡선 정보 파싱 건너뜀 (line=%s): %s", line, e)
            continue
        try:
            cant = float(line[2])
        except (ValueError, IndexError):
            cant = 0.0
        curveinfo.append(CurvePoint(sta=sta, radius=radius, cant=cant))
    return curveinfo


def load_curveinfo(path: str | Path) -> list[CurvePoint]:
    """곡선 파일을 읽어 CurvePoint 리스트로 반환."""
    return parsing_curveinfo(read_curve_csv(path))


# ---------------------------------------------------------------------------
# 기하 계산
# ---------------------------------------------------------------------------
def cal_direction(radius: float) -> int:
    return -1 if radius < 0 else 1


def cal_ordinate(radius: float, length: float, divisor: float) -> float:
    """원호 상 두 점의 종거 계산 (divisor로 분할점 지정)."""
    if radius == 0:
        return 0.0
    half = length / divisor
    return math.sqrt(radius**2 - half**2) - math.sqrt(radius**2 - length**2)


def cal_ordinate1(radius: float, length: float) -> float:
    return cal_ordinate(radius, length, 5) if radius else 0.0


def cal_ordinate2(radius: float, length: float) -> float:
    return cal_ordinate(radius, length, 1) if radius else 0.0


def cal_M1(ordinate1: float) -> float:
    return math.degrees(ordinate1 / INCREMENT)


def cal_M2(ordinate1: float, ordinate2: float) -> float:
    return math.degrees((ordinate2 - ordinate1) / INCREMENT)


def cal_X(direction: int, ordinate1: float, ordinate2: float) -> list[float]:
    values = {
        "zero": 0.0,
        "o1": ordinate1 if direction == -1 else -ordinate1,
        "o2": ordinate2 if direction == -1 else -ordinate2,
    }
    return [values[X_PATTERN[i]] for i in range(INCREMENT)]


def cal_Y(direction: int, m1: float, m2: float) -> list[float]:
    values = {
        "zero": 0.0,
        "m1": m1 if direction == -1 else -m1,
        "m2": m2 if direction == -1 else -m2,
        "m1_neg": -m1 if direction == -1 else m1,
        "m2_neg": -m2 if direction == -1 else m2,
    }
    return [values[Y_PATTERN[i]] for i in range(INCREMENT)]


# ---------------------------------------------------------------------------
# 캔트 보간
# ---------------------------------------------------------------------------
def _classify_curvetype(current_r: float, next_r: float, direction_sign: int) -> str:
    """곡선 유형 판단 (direction_sign: +1 우향, -1 좌향)."""
    if direction_sign > 0:
        if current_r > next_r and next_r != 0:
            return "SP-PC"
        return "CP-PS"
    if current_r < next_r and next_r != 0:
        return "SP-PC"
    return "CP-PS"


def cal_cant_5m(
    c_list: Sequence[CurvePoint], sta: float, direction_sign: int
) -> float:
    """sta 위치에서의 5m 캔트 증분 (mm) 반환."""
    eps = 1e-6
    for i in range(len(c_list) - 1):
        cur, nxt = c_list[i], c_list[i + 1]
        if abs(cur.sta - sta) < eps:
            cant_difference = abs(nxt.cant - cur.cant)
            cant_increment = cant_difference / INCREMENT
            curvetype = _classify_curvetype(cur.radius, nxt.radius, direction_sign)
            sign = direction_sign if curvetype == "SP-PC" else -direction_sign
            return cant_increment * M_TO_MM * sign
    return 0.0


def cal_Z(first_cant: float, cant_increment: float) -> list[float]:
    first_cant_mm = first_cant * M_TO_MM
    return [
        math.degrees((first_cant_mm + i * cant_increment) / GAUGE_MM)
        for i in range(INCREMENT)
    ]


# ---------------------------------------------------------------------------
# 메인 계산 및 구문 생성
# ---------------------------------------------------------------------------
def cal_mainlogic(curveinfo: Sequence[CurvePoint]) -> list[FreeObjPoint]:
    """곡선 정보로부터 5m 간격 FreeObj 좌표/각도 리스트를 계산."""
    freeobj: list[FreeObjPoint] = []
    for info in curveinfo:
        radius = info.radius
        direction = cal_direction(radius)

        if radius != 0:
            ia = BLOCK_LENGTH / radius
            tl = radius * math.tan(ia) / 2
            o1 = cal_ordinate1(radius, tl)
            o2 = cal_ordinate2(radius, tl)
            m1 = cal_M1(o1)
            m2 = cal_M2(o1, o2)
            xs = cal_X(direction, o1, o2)
            ys = cal_Y(direction, m1, m2)
        else:
            xs = [0.0] * INCREMENT
            ys = [0.0] * INCREMENT

        cant_increment = cal_cant_5m(curveinfo, info.sta, direction)
        zs = cal_Z(info.cant, cant_increment)

        for i in range(INCREMENT):
            freeobj.append(
                FreeObjPoint(
                    sta=info.sta + i * INCREMENT,
                    x=xs[i],
                    y=ys[i],
                    z=zs[i],
                )
            )
    return freeobj


def isbridge_tunnel(sta: float, structure_data: StructureData) -> str:
    """측점(sta)이 교량/터널/토공 중 어디에 속하는지 판정."""
    for seg in structure_data.bridge:
        if seg.start <= sta <= seg.end:
            return STRUCTURE_BRIDGE
    for seg in structure_data.tunnel:
        if seg.start <= sta <= seg.end:
            return STRUCTURE_TUNNEL
    return STRUCTURE_EARTHWORK


def check_sta_is_curve(current_sta: float, curveinfo: Sequence[CurvePoint]) -> str:
    """측점(current_sta)이 곡선/직선 구간인지 판정."""
    for i in range(len(curveinfo) - 1):
        cur, nxt = curveinfo[i], curveinfo[i + 1]
        if cur.sta <= current_sta < nxt.sta:
            return CURVE if cur.radius != 0 else STRAIGHT
    if curveinfo:
        last = curveinfo[-1]
        return CURVE if last.radius != 0 else STRAIGHT
    return STRAIGHT


def create_freeobj(
    freeobj: Sequence[FreeObjPoint],
    structure_data: StructureData,
    curve_info: Sequence[CurvePoint],
    index_dict: dict,
) -> list[str]:
    """FreeObj BVE 구문 리스트 생성."""
    content: list[str] = []
    for pt in freeobj:
        structure = isbridge_tunnel(pt.sta, structure_data)
        curve_type = check_sta_is_curve(pt.sta, curve_info)

        if curve_type == CURVE:
            if structure == STRUCTURE_TUNNEL:
                idx = index_dict["freeobj"][CURVE][STRUCTURE_TUNNEL][TRACK_CONCRETE]
            else:
                idx = index_dict["freeobj"][CURVE][structure][TRACK_BALLAST]
        else:
            idx = index_dict["freeobj"][STRAIGHT]

        content.append(f"{pt.sta},.freeobj 0;{idx};{pt.x};0;{pt.y};0;{pt.z}\n")
    return content


def create_railtype(
    curveinfo: Sequence[CurvePoint],
    structure_data: StructureData,
    index_dict: dict,
) -> list[str]:
    """RailType BVE 구문 리스트 생성."""
    railtype_list: list[str] = []
    for info in curveinfo:
        structure = isbridge_tunnel(info.sta, structure_data)
        if info.radius == 0:
            if structure == STRUCTURE_TUNNEL:
                railtype = index_dict["railtype"][STRAIGHT][STRUCTURE_TUNNEL][TRACK_CONCRETE]
            else:
                # 교량/토공 각각 자신의 인덱스를 참조하도록 수정
                railtype = index_dict["railtype"][STRAIGHT][structure][TRACK_BALLAST]
        else:
            railtype = index_dict["railtype"][CURVE]
        railtype_list.append(f"{info.sta},.railtype 0;{railtype};\n")
    return railtype_list


def modify_content(contents: Sequence[str]) -> list[str]:
    """오프셋이 모두 0인 구문을 제외.

    참고: 원본 동작 유지를 위해 문자열 "0" 비교를 유지합니다.
    (float "0.0"까지 제외하려면 float(v) == 0.0 조건으로 변경 검토 필요)
    """
    modified: list[str] = []
    for content in contents:
        parts = content.split(";")
        if len(parts) > 6:
            value1, value2, value3 = parts[2].strip(), parts[4].strip(), parts[6].strip()
            if not (value1 == "0" and value2 == "0" and value3 == "0"):
                modified.append(content)
    return modified


# ---------------------------------------------------------------------------
# 외부 프로젝트용 통합 실행 API (메모리 기반 / 파일 기반)
# ---------------------------------------------------------------------------
def generate_bve_texts(
    curveinfo: Sequence[CurvePoint],
    structure_data: StructureData,
    index_dict: dict | None = None,
    alignment_type: str = "도시철도",
    filter_zero_offsets: bool = True,
) -> GenerationResult:
    """이미 파싱된 데이터를 받아 FreeObj / RailType 구문을 생성 (파일 I/O 없음)."""
    resolved_index = index_dict if index_dict is not None else get_default_values(alignment_type)

    freeobj_points = cal_mainlogic(curveinfo)
    freeobj_lines = create_freeobj(
        freeobj_points, structure_data, curveinfo, resolved_index
    )
    if filter_zero_offsets:
        freeobj_lines = modify_content(freeobj_lines)

    railtype_lines = create_railtype(curveinfo, structure_data, resolved_index)
    return GenerationResult(
        freeobj_lines=freeobj_lines,
        railtype_lines=railtype_lines,
        freeobj_points=freeobj_points,
    )


def generate_bve_files(
    curve_path: str | Path,
    structure_path: str | Path,
    output_dir: str | Path | None = None,
    index_dict: dict | None = None,
    alignment_type: str = "도시철도",
    filter_zero_offsets: bool = True,
    on_progress: Callable[[str], None] | None = None,
) -> tuple[Path, Path]:
    """곡선 파일과 구조물 엑셀을 읽어 FreeObj / RailType 파일을 생성하고 경로 반환."""

    def notify(msg: str) -> None:
        logger.info(msg)
        if on_progress is not None:
            on_progress(msg)

    curve_file = Path(curve_path)
    out_path = Path(output_dir) if output_dir else curve_file.parent

    notify("곡선 파일 읽는 중...")
    lines = read_curve_csv(curve_file)

    notify("구조물 정보 로드 중...")
    structure_data = load_structure_section(structure_path)
    notify("구조물 정보 로드 완료.")

    notify("곡선 정보 파싱 중...")
    curveinfo = parsing_curveinfo(lines)

    notify("FreeObj / RailType 계산 및 구문 생성 중...")
    result = generate_bve_texts(
        curveinfo=curveinfo,
        structure_data=structure_data,
        index_dict=index_dict,
        alignment_type=alignment_type,
        filter_zero_offsets=filter_zero_offsets,
    )

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    freeobj_path = save_lines(result.freeobj_lines, out_path / f"freeobj_{stamp}.txt")
    notify(f"FreeObj 저장: {freeobj_path}")

    railtype_path = save_lines(result.railtype_lines, out_path / f"railtype_{stamp}.txt")
    notify(f"RailType 저장: {railtype_path}")

    return freeobj_path, railtype_path