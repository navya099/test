"""
검증 결과 패널
===============
선형 정렬 검증 결과를 표시하고, 항목 클릭 시 관련 IP로 이동.
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# 심각도 표시 설정
_SEVERITY_STYLE = {
    "error":   {"text": "오류",   "tag": "error"},
    "warning": {"text": "경고",   "tag": "warning"},
    "info":    {"text": "정보",   "tag": "info"},
}


class ValidatorPanel(ttk.Frame):
    """검증 결과 패널

    이벤트:
        on_issue_select(ip_index) — 검증 항목 선택 시 관련 IP 인덱스 전달
        on_run_validate()         — '검증 실행' 버튼 클릭 시
    """

    def __init__(
        self,
        master: tk.Widget,
        on_issue_select: Optional[Callable[[Optional[int]], None]] = None,
        on_run_validate: Optional[Callable[[], None]] = None,
    ):
        super().__init__(master)
        self._on_issue_select = on_issue_select
        self._on_run_validate = on_run_validate
        self._issues: list[dict] = []

        self._build()

    # ------------------------------------------------------------------
    # UI 구성
    # ------------------------------------------------------------------
    def _build(self) -> None:
        # 상단 툴바
        top = ttk.Frame(self)
        top.pack(fill="x", padx=4, pady=4)

        self.btn_run = ttk.Button(
            top, text="검증 실행", command=self._handle_run
        )
        self.btn_run.pack(side="left")

        ttk.Label(top, text="심각도:").pack(side="left", padx=(12, 4))

        self.severity_var = tk.StringVar(value="all")
        for value, label in (
            ("all", "전체"),
            ("error", "오류"),
            ("warning", "경고"),
            ("info", "정보"),
        ):
            ttk.Radiobutton(
                top,
                text=label,
                value=value,
                variable=self.severity_var,
                command=self._refresh_tree,
            ).pack(side="left", padx=2)

        # 요약 라벨
        self.summary_var = tk.StringVar(value="검증 결과 없음")
        ttk.Label(self, textvariable=self.summary_var, anchor="w").pack(
            fill="x", padx=6
        )

        # 결과 트리
        columns = ("severity", "code", "message", "location")
        self.tree = ttk.Treeview(
            self, columns=columns, show="headings", height=10
        )
        self.tree.heading("severity", text="심각도")
        self.tree.heading("code", text="코드")
        self.tree.heading("message", text="메시지")
        self.tree.heading("location", text="위치")

        self.tree.column("severity", width=60, anchor="center", stretch=False)
        self.tree.column("code", width=90, anchor="center", stretch=False)
        self.tree.column("message", width=280, anchor="w")
        self.tree.column("location", width=90, anchor="center", stretch=False)

        # 태그 색상
        self.tree.tag_configure("error", foreground="#c0392b")
        self.tree.tag_configure("warning", foreground="#e67e22")
        self.tree.tag_configure("info", foreground="#2980b9")

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)
        vsb.pack(side="right", fill="y", pady=4)

        # 선택 이벤트
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------
    def set_results(self, issues: list[dict]) -> None:
        """검증 결과 리스트를 받아 표시.

        Parameters
        ----------
        issues : list[dict]
            각 항목 예:
            {
                "severity": "error"/"warning"/"info",
                "code": "RADIUS_TOO_SMALL",
                "message": "곡선 반경이 최소 기준 미달",
                "ip_index": 3,          # 관련 IP (없으면 None)
                "element_index": 2,     # 관련 요소 (선택)
            }
        """
        self._issues = list(issues)
        self._refresh_tree()

    def clear(self) -> None:
        """결과 초기화."""
        self._issues.clear()
        self._refresh_tree()

    def set_busy(self, busy: bool) -> None:
        """검증 실행 중 버튼 비활성화 등."""
        state = "disabled" if busy else "normal"
        self.btn_run.configure(state=state)

    # ------------------------------------------------------------------
    # 내부
    # ------------------------------------------------------------------
    def _handle_run(self) -> None:
        if self._on_run_validate is not None:
            try:
                self._on_run_validate()
            except Exception:
                logger.exception("on_run_validate 콜백 실행 중 오류")

    def _refresh_tree(self) -> None:
        # 기존 항목 제거
        for item in self.tree.get_children():
            self.tree.delete(item)

        severity_filter = self.severity_var.get()

        counts = {"error": 0, "warning": 0, "info": 0}
        for issue in self._issues:
            sev = issue.get("severity", "info")
            counts[sev] = counts.get(sev, 0) + 1

            if severity_filter != "all" and sev != severity_filter:
                continue

            sev_meta = _SEVERITY_STYLE.get(sev, _SEVERITY_STYLE["info"])
            location = self._format_location(issue)

            self.tree.insert(
                "",
                "end",
                values=(
                    sev_meta["text"],
                    issue.get("code", ""),
                    issue.get("message", ""),
                    location,
                ),
                tags=(sev_meta["tag"],),
            )

        # 요약 라벨 갱신
        if not self._issues:
            self.summary_var.set("검증 결과 없음")
        else:
            self.summary_var.set(
                f"오류 {counts.get('error', 0)} · "
                f"경고 {counts.get('warning', 0)} · "
                f"정보 {counts.get('info', 0)}"
            )

    def _format_location(self, issue: dict) -> str:
        ip_index = issue.get("ip_index")
        if ip_index is not None:
            return f"IP{ip_index}"
        element_index = issue.get("element_index")
        if element_index is not None:
            return f"요소#{element_index}"
        return "-"

    def _on_tree_select(self, _event) -> None:
        if self._on_issue_select is None:
            return

        sel = self.tree.selection()
        if not sel:
            self._on_issue_select(None)
            return

        # 선택된 행 → 원본 issue 매핑
        # (필터로 인해 트리 인덱스와 _issues 인덱스가 다를 수 있으므로 값으로 매칭)
        values = self.tree.item(sel[0], "values")
        code, message = values[1], values[2]

        ip_index: Optional[int] = None
        for issue in self._issues:
            if (
                issue.get("code", "") == code
                and issue.get("message", "") == message
            ):
                ip_index = issue.get("ip_index")
                break

        try:
            self._on_issue_select(ip_index)
        except Exception:
            logger.exception("on_issue_select 콜백 실행 중 오류")