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
    structure_list = {"bridge": [], "tunnel": []}
    df_bridge = pd.read_excel(filepath, sheet_name="교량", header=None)
    df_tunnel = pd.read_excel(filepath, sheet_name="터널", header=None)

    print(df_tunnel.shape, df_tunnel.head())

    df_bridge.columns = ["br_NAME", "br_START_STA", "br_END_STA", "br_LENGTH"]
    df_tunnel.columns = ["tn_NAME", "tn_START_STA", "tn_END_STA", "tn_LENGTH"]

    for _, row in df_bridge.iterrows():
        structure_list["bridge"].append((row["br_NAME"], row["br_START_STA"], row["br_END_STA"]))
    for _, row in df_tunnel.iterrows():
        structure_list["tunnel"].append((row["tn_NAME"], row["tn_START_STA"], row["tn_END_STA"]))
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
class UserForm(tk.Toplevel):
    def __init__(self, master=None, defaults: dict | None = None):
        super().__init__(master)
        self.title("구조물 입력 폼")
        self.defaults = defaults or {}
        self.entries: dict[str, tk.Entry] = {}
        self.values: dict[str, str] | None = None
        self._create_widgets()

    def _create_widgets(self):
        for i, label in enumerate(FORM_LABELS):
            tk.Label(self, text=label).grid(row=i, column=0, sticky="w")
            entry = tk.Entry(self)
            entry.grid(row=i, column=1)
            entry.insert(0, self.defaults.get(label, ""))
            self.entries[label] = entry
        tk.Button(self, text="확인", command=self._submit).grid(
            row=len(FORM_LABELS), column=0, columnspan=2
        )

    def _submit(self):
        self.values = {label: e.get() for label, e in self.entries.items()}
        self.destroy()

    def ask_user_form(self) -> dict[str, str] | None:
        self.grab_set()
        self.wait_window()
        return self.values


class FreeobjApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FreeObj 자동 생성기")
        self.geometry("600x400")
        self.alignment_type: str | None = None
        self._create_widgets()

    def _create_widgets(self):
        ttk.Label(
            self, text="BVE FreeObj 자동 생성 프로그램", font=("Arial", 14, "bold")
        ).pack(pady=20)
        self.log_box = tk.Text(self, height=15, wrap=tk.WORD, font=("Consolas", 10))
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        ttk.Button(self, text="FreeObj 생성 실행", command=self.run_main).pack(pady=10)

    def log(self, message: str):
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)

    def _select_alignment_type(self) -> str | None:
        top = tk.Toplevel(self)
        top.title("노선 구분 선택")
        tk.Label(top, text="노선의 종류를 선택하세요:").pack(pady=10)

        result: dict[str, str | None] = {"value": None}

        def select(value: str):
            result["value"] = value
            top.destroy()

        for option in ALIGNMENT_TYPES:
            if option not in _DEFAULT_VALUES:
                continue
            tk.Button(
                top, text=option, width=15, command=lambda v=option: select(v)
            ).pack(pady=5)

        top.grab_set()
        top.wait_window()
        return result["value"]

    def run_main(self):
        try:
            self.alignment_type = self._select_alignment_type()
            if not self.alignment_type:
                self.log("노선 유형이 선택되지 않았습니다.")
                return

            form = UserForm(
                self, defaults=flatten_defaults(get_default_values(self.alignment_type))
            )
            raw = form.ask_user_form()
            if not raw:
                self.log("입력 폼이 취소되었습니다.")
                return
            index_dict = unflatten_defaults(raw)

            self.log("파일을 읽는 중...")
            lines = read_file()
            if not lines:
                self.log("파일 없음 또는 불러오기 실패.")
                return

            self.log("구조물 정보 로드 중...")
            structure_list = load_structure_data()
            if not structure_list:
                self.log("구조물 정보 로드 실패. 중단합니다.")
                return
            self.log("구조물 정보 로드 완료.")

            self.log("곡선 정보 파싱 중...")
            curveinfo = parsing_curveinfo(lines)

            self.log("FreeObj 계산 중...")
            freeobj = cal_mainlogic(curveinfo)

            self.log("FreeObj 생성 중...")
            content = modify_content(
                create_freeobj(freeobj, structure_list, curveinfo, index_dict)
            )
            savefile = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="FREEOBJ 저장",
            )
            save_lines(content, savefile)
            self.log("FreeObj 저장 완료!")

            self.log("Railtype 생성 중...")
            railtype = create_railtype(curveinfo, structure_list, index_dict)
            savefile = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="RAILTYPE 저장",
            )
            save_lines(railtype, savefile)
            self.log("Railtype 저장 완료!")

            messagebox.showinfo("완료", "FreeObj 및 RailType 생성이 완료되었습니다.")
        except Exception as e:
            self.log(f"[오류] {type(e).__name__}: {e}")
            messagebox.showerror("오류", f"실행 중 오류 발생:\n{e}")


if __name__ == "__main__":
    FreeobjApp().mainloop()