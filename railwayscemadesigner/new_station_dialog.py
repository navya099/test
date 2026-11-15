# new_station_dialog.py
""""새 정거장" 대화상자 — 입력 수집 + 즉시 검증만 담당(모델 조립/씬 갱신은 MainWindow)."""

import re

from PyQt6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QDialog, QDialogButtonBox,
    QFormLayout, QLineEdit, QLabel, QVBoxLayout,
)

from model import STATION_TYPES


def suggest_station_id(existing_ids):
    """기존 ID 목록 대비 다음 STN-### 제안 (예: STN-001, STN-002 → STN-003)."""
    highest = 0
    for sid in existing_ids:
        m = re.fullmatch(r"STN-(\d+)", sid or "")
        if m:
            highest = max(highest, int(m.group(1)))
    return f"STN-{highest + 1:03d}"


class NewStationDialog(QDialog):
    """수락 시 (id, name, type, mileage_start, mileage_end) 튜플을 돌려준다."""

    def __init__(self, existing_ids=(), parent=None):
        super().__init__(parent)
        self.setWindowTitle("새 정거장")
        self._result = None

        form = QFormLayout(self)

        self.id_edit = QLineEdit(suggest_station_id(existing_ids))
        self.name_edit = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(STATION_TYPES)

        self.start_spin = QDoubleSpinBox()
        self.start_spin.setDecimals(3)
        self.start_spin.setRange(0.0, 100000.0)
        self.end_spin = QDoubleSpinBox()
        self.end_spin.setDecimals(3)
        self.end_spin.setRange(0.0, 100000.0)

        form.addRow("정거장 ID", self.id_edit)
        form.addRow("이름", self.name_edit)
        form.addRow("유형", self.type_combo)
        form.addRow("마일지 시작 (km)", self.start_spin)
        form.addRow("마일지 끝 (km)", self.end_spin)

        self.error_label = QLabel()
        self.error_label.setWordWrap(True)
        form.addRow(self.error_label)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

        # 초기 상태(이름 미입력)를 바로 라벨로 안내
        self._validate(last_error=None)

    def _validate(self, last_error=None):
        """검증 통과 시 결과 튜플 저장 후 수락. 실패 시 오류 라벨만 채운다."""
        values = (
            self.id_edit.text().strip(),
            self.name_edit.text().strip(),
            self.type_combo.currentText(),
            self.start_spin.value(),
            self.end_spin.value(),
        )
        error = self._check(values)
        if error is None:
            self.error_label.setText("")
            self._result = values
            self.accept()
            return
        if error != last_error:
            self.error_label.setText(error)

    @staticmethod
    def _check(values):
        sid, name, stype, start, end = values
        if not sid:
            return "정거장 ID를 입력하세요."
        if not re.fullmatch(r"[A-Za-z0-9_-]+", sid):
            return "정거장 ID는 영문/숫자/-/_ 만 사용할 수 있습니다."
        if not name:
            return "이름을 입력하세요."
        if not STATION_TYPES or stype not in STATION_TYPES:
            return "정거장 유형을 선택하세요."
        if not (0.0 <= start < end):
            return "마일지는 0 이상, 시작 < 끝 이어야 합니다."
        return None

    def station_values(self):
        return self._result

