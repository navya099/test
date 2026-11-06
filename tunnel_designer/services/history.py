"""FL 자동 맞춤 이력."""
from __future__ import annotations
import csv
from dataclasses import asdict
from datetime import datetime

from core.models import FitHistoryEntry, TunnelParams


class FitHistory:
    def __init__(self, max_size: int = 100):
        self.entries: list[FitHistoryEntry] = []
        self.max_size = max_size

    def add(self, p: TunnelParams, R1_Y_prev: float,
            achieved_FL: float, success: bool) -> FitHistoryEntry:
        e = FitHistoryEntry(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            target_FL=p.FL, achieved_FL=achieved_FL,
            R1_Y=p.R1_Y, dR1_Y=p.R1_Y - R1_Y_prev,
            R1=p.R1, top_angle=p.top_angle,
            R2=p.R2, r2_angle=p.r2_angle, D=p.D,
            success=success,
        )
        self.entries.append(e)
        if len(self.entries) > self.max_size:
            self.entries.pop(0)
        return e

    def to_csv(self, path: str):
        if not self.entries:
            raise ValueError("저장할 이력이 없습니다.")
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(asdict(self.entries[0]).keys()))
            w.writeheader()
            for e in self.entries:
                w.writerow(asdict(e))