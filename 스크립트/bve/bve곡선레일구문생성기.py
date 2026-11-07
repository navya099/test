"""BVE 곡선 파일 기반 곡선레일(5m) 설치 구문 생성기.

입력: BVE에서 추출한 CURVE_INFO.TXT, 구조물 측점 XLSX
출력: FREEOBJ 구문 파일, RAILTYPE 구문 파일
"""
from __future__ import annotations

import csv
import math
import tkinter as tk
from dataclasses import dataclass
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Iterable

import pandas as pd

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


# ---------------------------------------------------------------------------
# 파일 입출력
# ---------------------------------------------------------------------------
def read_file() -> list[list[str]]:
    """CURVE_INFO 파일을 읽어 2차원 리스트로 반환. 취소/실패 시 빈 리스트."""
    path = filedialog.askopenfilename(
        defaultextension=".txt",
        filetypes=[("txt files", "curve_info.txt"), ("All files", "*.*")],
    )
    if not path:
        return []

    print("현재파일:", path)
    for encoding in ("utf-8", "euc-kr"):
        try:
            with open(path, "r", encoding=encoding) as f:
                return list(csv.reader(f))
        except UnicodeDecodeError:
            print(f"{encoding} 디코딩 실패. 다음 인코딩 시도.")
        except OSError as e:
            print(f"파일 열기 실패: {e}")
            return []
    print("지원 인코딩으로 파일을 읽을 수 없습니다.")
    return []


def save_lines(lines: Iterable[str], save_path: str) -> None:
    if not save_path:
        print("저장 경로가 지정되지 않았습니다.")
        return
    try:
        with open(save_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"{save_path} 파일이 성공적으로 저장되었습니다.")
    except OSError as e:
        print(f"파일 저장에 실패하였습니다: {e}")


# ---------------------------------------------------------------------------
# 곡선 정보 파싱
# ---------------------------------------------------------------------------
@dataclass
class CurvePoint:
    sta: float
    radius: float
    cant: float


def parsing_curveinfo(lines: list[list[str]]) -> list[CurvePoint]:
    curveinfo: list[CurvePoint] = []
    for line in lines:
        if not line:
            continue
        try:
            sta = float(line[0])
            radius = float(line[1])
        except (ValueError, IndexError) as e:
            print(f"곡선 정보 파싱 오류 (line={line}): {e}")
            continue
        try:
            cant = float(line[2])
        except (ValueError, IndexError):
            cant = 0.0
        curveinfo.append(CurvePoint(sta, radius, cant))
    return curveinfo


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


# 5m 구간 내 i번째 점의 x 오프셋 (원본 로직 유지: increment=5 전제)
X_PATTERN = {0: "zero", 1: "o1", 2: "o2", 3: "o2", 4: "o1"}
Y_PATTERN = {0: "m1", 1: "m2", 2: "zero", 3: "m2_neg", 4: "m1_neg"}


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
    """곡선 유형 판단. 원본 로직을 정리한 버전.

    direction_sign: +1(우향), -1(좌향)
    """
    if direction_sign > 0:  # 우향: R이 감소하면 SP-PC, 증가하면 CP-PS
        if current_r > next_r and next_r != 0:
            return "SP-PC"
        return "CP-PS"
    # 좌향: R이 증가하면 SP-PC
    if current_r < next_r and next_r != 0:
        return "SP-PC"
    return "CP-PS"


def cal_cant_5m(c_list: list[CurvePoint], sta: float, direction_sign: int) -> float:
    """sta 위치에서의 5m 캔트 증분 (mm) 반환. 부동소수점 근사 비교."""
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
# 메인 로직
# ---------------------------------------------------------------------------
def cal_mainlogic(curveinfo: list[CurvePoint]) -> list[list[float]]:
    freeobj: list[list[float]] = []
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
        stations = [info.sta + i * INCREMENT for i in range(INCREMENT)]

        for i in range(INCREMENT):
            freeobj.append([stations[i], xs[i], ys[i], zs[i]])
    return freeobj


# ---------------------------------------------------------------------------
# 구조물 / 곡선 판정
# ---------------------------------------------------------------------------
def isbridge_tunnel(sta: float, structure_list: dict) -> str:
    for _, start, end in structure_list["bridge"]:
        if start <= sta <= end:
            return STRUCTURE_BRIDGE
    for _, start, end in structure_list["tunnel"]:
        if start <= sta <= end:
            return STRUCTURE_TUNNEL
    return STRUCTURE_EARTHWORK


def check_sta_is_curve(current_sta: float, curveinfo: list[CurvePoint]) -> str:
    for i in range(len(curveinfo) - 1):
        cur, nxt = curveinfo[i], curveinfo[i + 1]
        if cur.sta <= current_sta < nxt.sta:
            return CURVE if cur.radius != 0 else STRAIGHT
    # 마지막 측점 이후는 마지막 곡선 정보로 판정 (경계 안전)
    if curveinfo:
        last = curveinfo[-1]
        return CURVE if last.radius != 0 else STRAIGHT
    return STRAIGHT


# ---------------------------------------------------------------------------
# FreeObj / RailType 생성
# ---------------------------------------------------------------------------
def create_freeobj(
    freeobj: list[list[float]],
    structure_list: dict,
    curve_info: list[CurvePoint],
    index_dict: dict,
) -> list[str]:
    content = []
    for sta, x, y, z in freeobj:
        structure = isbridge_tunnel(sta, structure_list)
        curve_type = check_sta_is_curve(sta, curve_info)

        if curve_type == CURVE:
            if structure == STRUCTURE_TUNNEL:
                # NOTE: 원본은 콘크리트도상 고정이었음. 도상 종류 판단 로직 필요 시 확장.
                idx = index_dict["freeobj"][CURVE][STRUCTURE_TUNNEL][TRACK_CONCRETE]
            else:  # 토공 / 교량
                # [버그 수정] 원본은 교량도 '토공' 인덱스를 사용했음 → 교량 분기 추가
                idx = index_dict["freeobj"][CURVE][structure][TRACK_BALLAST]
        else:
            idx = index_dict["freeobj"][STRAIGHT]

        content.append(f"{sta},.freeobj 0;{idx};{x};0;{y};0;{z}\n")
    return content


def create_railtype(
    curveinfo: list[CurvePoint], structure_list: dict, index_dict: dict
) -> list[str]:
    railtype_list = []
    for info in curveinfo:
        structure = isbridge_tunnel(info.sta, structure_list)
        if info.radius == 0:
            if structure == STRUCTURE_TUNNEL:
                railtype = index_dict["railtype"][STRAIGHT][STRUCTURE_TUNNEL][TRACK_CONCRETE]
            else:
                railtype = index_dict["railtype"][STRAIGHT][STRUCTURE_EARTHWORK][TRACK_BALLAST]
        else:
            railtype = index_dict["railtype"][CURVE]
        railtype_list.append(f"{info.sta},.railtype 0;{railtype};\n")
    return railtype_list


def modify_content(contents: list[str]) -> list[str]:
    modified = []
    for content in contents:
        parts = content.split(";")
        if len(parts) > 6:
            value1, value2, value3 = parts[2].strip(), parts[4].strip(), parts[6].strip()
            if not (value1 == "0" and value2 == "0" and value3 == "0"):
                modified.append(content)
    return modified


# ---------------------------------------------------------------------------
# 구조물 데이터 로드
# ---------------------------------------------------------------------------
def load_structure_data() -> dict | None:
    path = open_excel_file()
    if not path:
        print("엑셀 파일을 선택하지 않았습니다.")
        return None
    return find_structure_section(path)


def open_excel_file() -> str:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        return filedialog.askopenfilename(
            title="엑셀 파일 선택", filetypes=[("Excel Files", "*.xlsx")]
        )
    finally:
        root.destroy()


def find_structure_section(filepath: str) -> dict:
    structure_list = {
        "bridge": [],
        "tunnel": []
    }

    df_bridge = pd.read_excel(filepath, sheet_name="교량", header=None)
    df_tunnel = pd.read_excel(filepath, sheet_name="터널", header=None)

    if not df_bridge.empty:
        df_bridge.columns = [
            "br_NAME",
            "br_START_STA",
            "br_END_STA",
            "br_LENGTH"
        ]

        for _, row in df_bridge.iterrows():
            structure_list["bridge"].append(
                (row["br_NAME"], row["br_START_STA"], row["br_END_STA"])
            )

    if not df_tunnel.empty:
        df_tunnel.columns = [
            "tn_NAME",
            "tn_START_STA",
            "tn_END_STA",
            "tn_LENGTH"
        ]

        for _, row in df_tunnel.iterrows():
            structure_list["tunnel"].append(
                (row["tn_NAME"], row["tn_START_STA"], row["tn_END_STA"])
            )

    return structure_list


# ---------------------------------------------------------------------------
# 기본값 (노선별)
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
    "준고속철도": _BASE_GENERAL,   # 값 동일 → 동일 참조
    "도시철도": _URBAN,
    "고속철도": _HIGH_SPEED,
}


def get_default_values(alignment_type: str) -> dict:
    if alignment_type not in _DEFAULT_VALUES:
        raise ValueError(f"알 수 없는 노선 유형: {alignment_type}")
    return _DEFAULT_VALUES[alignment_type]


# ---------------------------------------------------------------------------
# flatten / unflatten (라벨 정의 한 곳에서 관리)
# ---------------------------------------------------------------------------
FORM_LABELS = [
    "freeobj 곡선-토공-자갈도상",
    "freeobj 곡선-토공-콘크리트도상",
    "freeobj 곡선-교량-자갈도상",
    "freeobj 곡선-교량-콘크리트도상",
    "freeobj 곡선-터널-자갈도상",
    "freeobj 곡선-터널-콘크리트도상",
    "freeobj 직선",
    "railtype 곡선",
    "railtype 직선-토공-자갈도상",
    "railtype 직선-토공-콘크리트도상",
    "railtype 직선-교량-자갈도상",
    "railtype 직선-교량-콘크리트도상",
    "railtype 직선-터널-자갈도상",
    "railtype 직선-터널-콘크리트도상",
]


def flatten_defaults(defaults: dict) -> dict[str, int]:
    flat: dict[str, int] = {}
    for curve_type, sub in defaults["freeobj"][CURVE].items():
        for track_type, val in sub.items():
            flat[f"freeobj 곡선-{curve_type}-{track_type}"] = val
    flat["freeobj 직선"] = defaults["freeobj"][STRAIGHT]
    flat["railtype 곡선"] = defaults["railtype"][CURVE]
    for curve_type, sub in defaults["railtype"][STRAIGHT].items():
        for track_type, val in sub.items():
            flat[f"railtype 직선-{curve_type}-{track_type}"] = val
    return flat


def unflatten_defaults(flat: dict[str, str]) -> dict:
    def get(key: str) -> int:
        return int(flat[key])

    return {
        "freeobj": {
            CURVE: {
                STRUCTURE_TUNNEL: {
                    TRACK_CONCRETE: get("freeobj 곡선-터널-콘크리트도상"),
                    TRACK_BALLAST: get("freeobj 곡선-터널-자갈도상"),
                },
                STRUCTURE_EARTHWORK: {
                    TRACK_CONCRETE: get("freeobj 곡선-토공-콘크리트도상"),
                    TRACK_BALLAST: get("freeobj 곡선-토공-자갈도상"),
                },
                STRUCTURE_BRIDGE: {
                    TRACK_CONCRETE: get("freeobj 곡선-교량-콘크리트도상"),
                    TRACK_BALLAST: get("freeobj 곡선-교량-자갈도상"),
                },
            },
            STRAIGHT: get("freeobj 직선"),
        },
        "railtype": {
            CURVE: get("railtype 곡선"),
            STRAIGHT: {
                STRUCTURE_TUNNEL: {
                    TRACK_CONCRETE: get("railtype 직선-터널-콘크리트도상"),
                    TRACK_BALLAST: get("railtype 직선-터널-자갈도상"),
                },
                STRUCTURE_EARTHWORK: {
                    TRACK_CONCRETE: get("railtype 직선-토공-콘크리트도상"),
                    TRACK_BALLAST: get("railtype 직선-토공-자갈도상"),
                },
                STRUCTURE_BRIDGE: {
                    TRACK_CONCRETE: get("railtype 직선-교량-콘크리트도상"),
                    TRACK_BALLAST: get("railtype 직선-교량-자갈도상"),
                },
            },
        },
    }


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
# ===========================================================================
# UserForm — Enter로 다음 칸 이동, 마지막 칸 Enter = 자동 제출
# ===========================================================================
class UserForm(tk.Frame):
    """파라미터 입력 폼 (Toplevel이 아닌 Frame → 메인창에 임베드)."""

    def __init__(self, master, defaults: dict[str, int], on_submit=None):
        super().__init__(master)
        self.defaults = defaults
        self.on_submit = on_submit
        self.entries: dict[str, tk.Entry] = {}
        self._create_widgets()
        self._bind_enter_navigation()

    def _create_widgets(self):
        # 2열 그리드: FreeObj / RailType
        left_labels = [l for l in FORM_LABELS if l.startswith("freeobj")]
        right_labels = [l for l in FORM_LABELS if l.startswith("railtype")]

        for col, (title, labels) in enumerate(
            [("FreeObj 인덱스", left_labels), ("RailType 인덱스", right_labels)]
        ):
            box = ttk.LabelFrame(self, text=title, padding=8)
            box.grid(row=0, column=col, sticky="nsew", padx=6, pady=6)
            for i, label in enumerate(labels):
                ttk.Label(box, text=label).grid(row=i, column=0, sticky="w", pady=2)
                entry = ttk.Entry(box, width=8, justify="right")
                entry.grid(row=i, column=1, sticky="e", pady=2)
                entry.insert(0, str(self.defaults.get(label, "")))
                self.entries[label] = entry
            self.columnconfigure(col, weight=1)

        # 버튼 행
        btn_row = ttk.Frame(self)
        btn_row.grid(row=1, column=0, columnspan=2, pady=(4, 8))
        ttk.Button(
            btn_row, text="▶ 실행 (Ctrl+Enter)", command=self._submit
        ).pack(side="left", padx=4)
        ttk.Button(
            btn_row, text="기본값 복원", command=self._reset_defaults
        ).pack(side="left", padx=4)

    def _ordered_entries(self) -> list[tk.Entry]:
        """Tab 순서대로 Entry 리스트 (FreeObj → RailType)."""
        order = [l for l in FORM_LABELS if l in self.entries]
        return [self.entries[l] for l in order]

    def _bind_enter_navigation(self):
        entries = self._ordered_entries()
        for i, entry in enumerate(entries):
            if i < len(entries) - 1:
                nxt = entries[i + 1]
                entry.bind("<Return>", lambda e, n=nxt: (n.focus_set(), n.select_range(0, "end"), "break")[2])
            else:
                # 마지막 칸 Enter → 자동 제출
                entry.bind("<Return>", lambda e: (self._submit(), "break")[1])
            # 숫자만 허용
            entry.bind("<KeyPress>", self._only_numeric)

        # Ctrl+Enter는 어디서든 제출
        self.bind_all("<Control-Return>", lambda e: self._submit())

        # 폼 최초 포커스
        if entries:
            self.after(50, lambda: (entries[0].focus_set(), entries[0].select_range(0, "end")))

    @staticmethod
    def _only_numeric(event):
        if event.char and not event.char.isdigit() and event.keysym not in (
            "BackSpace", "Delete", "Left", "Right", "Tab", "Return", "Home", "End"
        ):
            return "break"

    def _reset_defaults(self):
        for label, entry in self.entries.items():
            entry.delete(0, "end")
            entry.insert(0, str(self.defaults.get(label, "")))

    def update_defaults(self, new_defaults: dict[str, int]):
        self.defaults = new_defaults
        self._reset_defaults()

    def _submit(self):
        values = {}
        for label, entry in self.entries.items():
            raw = entry.get().strip()
            if not raw:
                messagebox.showwarning("입력 오류", f"'{label}' 값이 비어 있습니다.")
                entry.focus_set()
                return
            try:
                values[label] = int(raw)
            except ValueError:
                messagebox.showwarning("입력 오류", f"'{label}' 값이 숫자가 아닙니다.")
                entry.focus_set()
                entry.select_range(0, "end")
                return
        if self.on_submit:
            self.on_submit(values)



class FreeobjApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BVE FreeObj 자동 생성기")
        self.geometry("820x680")
        self.minsize(760, 620)

        self.alignment_type = tk.StringVar(value="도시철도")
        self.curve_path = tk.StringVar()
        self.structure_path = tk.StringVar()
        self.output_dir = tk.StringVar()

        self.user_form: UserForm | None = None
        self._build_ui()
        self._on_alignment_change()  # 초기 폼 구성

    # ---- UI 구성 --------------------------------------------------------
    def _build_ui(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="노선 유형:").grid(row=0, column=0, sticky="w")
        cb = ttk.Combobox(
            top,
            textvariable=self.alignment_type,
            values=[v for v in ALIGNMENT_TYPES if v in _DEFAULT_VALUES],
            state="readonly",
            width=12,
        )
        cb.grid(row=0, column=1, sticky="w", padx=6)
        cb.bind("<<ComboboxSelected>>", lambda e: self._on_alignment_change())

        # 파일 경로 3행
        self._path_row(top, 1, "곡선 파일", self.curve_path,
                       [("CURVE_INFO", "*.txt"), ("All files", "*.*")])
        self._path_row(top, 2, "구조물 XLSX", self.structure_path,
                       [("Excel", "*.xlsx")])
        self._path_row(top, 3, "출력 폴더", self.output_dir, None)  # 폴더 선택
        top.columnconfigure(1, weight=1)

        # 폼 컨테이너
        self.form_container = ttk.Frame(self, padding=(10, 0))
        self.form_container.pack(fill="x")

        # 로그
        log_frame = ttk.LabelFrame(self, text="로그", padding=6)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(4, 10))
        self.log_box = tk.Text(log_frame, height=12, wrap="word", font=("Consolas", 10))
        sb = ttk.Scrollbar(log_frame, command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=sb.set)
        self.log_box.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.log("노선 유형을 선택하고 파일 경로를 지정한 뒤 실행하세요.")

    def _path_row(self, parent, row, label, var, filetypes):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=2)
        entry = ttk.Entry(parent, textvariable=var)
        entry.grid(row=row, column=1, sticky="ew", padx=6)

        def browse():
            if filetypes is None:  # 폴더 선택
                path = filedialog.askdirectory(title=f"{label} 선택")
            else:
                path = filedialog.askopenfilename(title=f"{label} 선택", filetypes=filetypes)
            if path:
                var.set(path)

        ttk.Button(parent, text="찾아보기", command=browse).grid(row=row, column=2)

    # ---- 이벤트 ---------------------------------------------------------
    def _on_alignment_change(self):
        try:
            defaults = get_default_values(self.alignment_type.get())
        except ValueError:
            return
        flat = flatten_defaults(defaults)
        if self.user_form is None:
            self.user_form = UserForm(
                self.form_container, defaults=flat, on_submit=self._run_with_values
            )
            self.user_form.pack(fill="x")
        else:
            self.user_form.update_defaults(flat)

    def log(self, message: str):
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.update_idletasks()

    # ---- 실행 -----------------------------------------------------------
    def _run_with_values(self, values: dict[str, int]):
        # 경로 검증
        curve = self.curve_path.get().strip()
        structure = self.structure_path.get().strip()
        outdir = self.output_dir.get().strip()

        from pathlib import Path
        if not curve or not Path(curve).is_file():
            messagebox.showwarning("입력 오류", "곡선 파일을 선택하세요.")
            return
        if not structure or not Path(structure).is_file():
            messagebox.showwarning("입력 오류", "구조물 XLSX 파일을 선택하세요.")
            return
        if not outdir:
            # 폴더 미지정 시 곡선 파일과 같은 위치 사용
            outdir = str(Path(curve).parent)
            self.output_dir.set(outdir)
            self.log(f"출력 폴더 미지정 → {outdir} 사용")

        try:
            self._execute(curve, structure, outdir, unflatten_defaults(values))
            self.log("✅ 모든 작업 완료.")
        except Exception as e:
            self.log(f"[오류] {type(e).__name__}: {e}")
            messagebox.showerror("오류", f"실행 중 오류 발생:\n{e}")

    def _execute(self, curve_path: str, structure_path: str, outdir: str, index_dict: dict):
        self.log("곡선 파일 읽는 중...")
        with open(curve_path, "r", encoding="utf-8") as f:
            lines = list(csv.reader(f))

        self.log("구조물 정보 로드 중...")
        structure_list = find_structure_section(structure_path)
        self.log("구조물 정보 로드 완료.")

        self.log("곡선 정보 파싱 중...")
        curveinfo = parsing_curveinfo(lines)

        self.log("FreeObj 계산 중...")
        freeobj = cal_mainlogic(curveinfo)

        self.log("FreeObj 구문 생성 중...")
        content = modify_content(
            create_freeobj(freeobj, structure_list, curveinfo, index_dict)
        )

        from datetime import datetime
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        from pathlib import Path
        freeobj_path = Path(outdir) / f"freeobj_{stamp}.txt"
        railtype_path = Path(outdir) / f"railtype_{stamp}.txt"

        save_lines(content, str(freeobj_path))
        self.log(f"FreeObj 저장: {freeobj_path}")

        self.log("RailType 구문 생성 중...")
        railtype = create_railtype(curveinfo, structure_list, index_dict)
        save_lines(railtype, str(railtype_path))
        self.log(f"RailType 저장: {railtype_path}")


if __name__ == "__main__":
    FreeobjApp().mainloop()