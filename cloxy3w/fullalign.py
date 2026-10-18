"""
fullalign.py - BP ~ EP 전체 선형(직선부 포함)의 측점별 좌표.

OUTSIDE/INSIDE 는 곡선마다 정해지는 이름(원곡선 중심의 반대/같은 쪽)이므로, 좌회전 다음에 우회전이 오면
같은 이름이 서로 반대쪽 궤도가 된다. 전체 선형은 진행 방향 기준의 물리적 궤도로 잇는다.
    좌회전 곡선: 좌측 궤도 = INSIDE, 우측 궤도 = OUTSIDE
    우회전 곡선: 좌측 궤도 = OUTSIDE, 우측 궤도 = INSIDE
곡선 k 의 BTC 앞과 ETC 뒤의 직선은 그 곡선의 접선 위로 연장해서 구한다.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from ip2_engine import frame, station_coord

SIDES = ("left", "center", "right")
SIDE_LABEL = {"left": "LEFT", "center": "CENTER", "right": "RIGHT"}
SIDE_KO = {"left": "좌측 궤도", "center": "중앙선", "right": "우측 궤도"}


@dataclass
class FullInfo:
    bp_xy: tuple          # (X북, Y동)
    ep_xy: tuple
    start_sta: float
    end_sta: float
    chain: float


class Full:
    def __init__(self, curves, fi: FullInfo):
        self.cv = curves
        self.fi = fi
        self.fr = [frame(c) for c in curves]

    def lname(self, k: int, side: str) -> str:
        """곡선 k 에서 물리적 궤도(side)에 해당하는 선 이름"""
        if side == "center":
            return "center"
        left_turn = self.fr[k]["s_turn"] > 0
        if side == "left":
            return "inside" if left_turn else "outside"
        return "outside" if left_turn else "inside"

    def ln(self, k: int, side: str):
        return self.cv[k].lines[self.lname(k, side)]

    def _pick(self, side: str, s: float) -> int:
        n = len(self.cv)
        for k in range(n - 1):
            if s < (self.ln(k, side).ETC + self.ln(k + 1, side).BTC) / 2:
                return k
        return n - 1

    def point_from(self, k: int, side: str, s: float):
        n, e, _ = station_coord(self.cv[k], self.ln(k, side), s, self.fr[k])
        return n, e

    def point(self, side: str, s: float):
        return self.point_from(self._pick(side, s), side, s)

    def stations(self, side: str):
        """[(측점, 태그, IP번호)] — BP, EP, 각 곡선의 BTC/BC/BCC/ECC/EC/ETC, chain 배수"""
        fi = self.fi
        pts = [(fi.start_sta, "BP", 0), (fi.end_sta, "EP", 0)]
        for k, cv in enumerate(self.cv):
            ln = self.ln(k, side)
            for tag, v in (("BTC", ln.BTC), ("BC", cv.BC), ("BCC", ln.BCC), ("ECC", ln.ECC), ("EC", cv.EC), ("ETC", ln.ETC)):
                pts.append((v, tag, k + 1))
        j = math.floor(fi.start_sta / fi.chain) + 1
        reg = []
        while j * fi.chain < fi.end_sta - 1e-9:
            s = j * fi.chain
            if all(abs(s - p[0]) > 5e-4 for p in pts):
                reg.append((s, "", 0))
            j += 1
        return sorted(pts + reg, key=lambda t: (t[0], t[2]))

    def straights(self, side: str):
        """직선구간 [(시점(N,E), 끝점(N,E))] : BP~BTC1, ETCk~BTCk+1, ETCn~EP"""
        fi, out = self.fi, []
        n = len(self.cv)
        out.append((self.point_from(0, side, fi.start_sta), self.point_from(0, side, self.ln(0, side).BTC)))
        for k in range(n - 1):
            out.append((self.point_from(k, side, self.ln(k, side).ETC),
                        self.point_from(k + 1, side, self.ln(k + 1, side).BTC)))
        out.append((self.point_from(n - 1, side, self.ln(n - 1, side).ETC), self.point_from(n - 1, side, fi.end_sta)))
        return out
