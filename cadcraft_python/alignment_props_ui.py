import math
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QScrollArea, QWidget, QFormLayout
)
from PyQt6.QtCore import Qt


# --- 유틸리티 및 포맷팅 헬퍼 함수들 (기존 프로젝트 기준) ---
def fixed(val, decimals=2):
    if val is None or not math.isfinite(val):
        return "—"
    return f"{val:.{decimals}f}"


def format_station(sta, units='m'):
    if sta is None:
        return "0+000.00"
    km = int(sta // 1000)
    m = sta % 1000
    return f"{km}+{m:06.2f}" if units == 'm' else f"{km}+{m:06.2f}"


def parse_station(text, units='m'):
    try:
        text = text.strip()
        if '+' in text:
            parts = text.split('+')
            return float(parts[0]) * 1000 + float(parts[1])
        return float(text)
    except ValueError:
        return None


def rad_to_dms(rad):
    deg = math.degrees(rad)
    d = int(deg)
    m = int((deg - d) * 60)
    s = ((deg - d) * 60 - m) * 60
    return f"{d}°{m:02d}'{s:05.2f}\""


class AlignmentPropsDialog(QDialog):
    def __init__(self, alignment_data, project_context, parent=None):
        super().__init__(parent)
        self.al_data = alignment_data  # 선형 딕셔너리 또는 객체 (a)
        self.ctx = project_context  # {'project': proj, 'units': 'm', ...}

        self.setWindowTitle(f"Alignment Properties: {getattr(self.al_data, 'name', 'Alignment')}")
        self.resize(500, 700)
        self.init_ui()

    def get_project(self):
        return self.ctx.get('project')

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # 스크롤 영역 설정 (속성 항목이 많을 때 대비)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)

        u_short = 'm' if self.ctx.get('units', 'm') == 'm' else 'ft'

        # 1. 기본 선형 정보 입력 폼
        form_layout = QFormLayout()

        # 선형 이름 (Name)
        self.name_input = QLineEdit(str(getattr(self.al_data, 'name', 'Alignment')))
        self.name_input.textChanged.connect(self.on_name_changed)
        form_layout.addRow("Name:", self.name_input)

        # 시작 스테이션 (Start Station)
        start_val = getattr(self.al_data, 'start', 0.0)
        self.start_input = QLineEdit(format_station(start_val, u_short))
        self.start_input.editingFinished.connect(self.on_start_changed)
        form_layout.addRow("Start Station:", self.start_input)

        # 최소 반경 (Min Radius)
        min_r_val = getattr(self.al_data, 'min_r', 0.0)
        min_r_str = str(min_r_val) if min_r_val > 0 else ""
        self.minr_input = QLineEdit(min_r_str)
        self.minr_input.setPlaceholderText("None")
        self.minr_input.editingFinished.connect(self.on_minr_changed)

        minr_layout = QHBoxLayout()
        minr_layout.addWidget(self.minr_input)
        minr_layout.addWidget(QLabel(u_short))
        form_layout.addRow("Minimum Radius:", minr_layout)

        layout.addLayout(form_layout)

        # 2. PI (Intersection Points) 테이블
        layout.addWidget(QLabel("<b>PI (Intersection Points)</b>"))

        self.pi_table = QTableWidget()
        self.pi_table.setColumnCount(5)
        self.pi_table.setHorizontalHeaderLabels(["#", "Easting", "Northing", "Radius (R)", ""])
        self.pi_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.populate_pi_table()
        layout.addWidget(self.pi_table)

        # 3. 곡선 제원 요약 (Arcs / Curves)
        layout.addWidget(QLabel("<b>Curve Elements</b>"))
        self.curves_label = QLabel()
        self.curves_label.setStyleSheet("color: #444444; background: #f9f9f9; padding: 6px; border-radius: 4px;")
        self.update_curves_info()
        layout.addWidget(self.curves_label)

        # 4. 하단 액션 버튼들 (프로파일 뷰, 삭제 등)
        action_layout = QHBoxLayout()

        self.btn_profile = QPushButton("View Profile")
        self.btn_profile.clicked.connect(self.on_view_profile)
        action_layout.addWidget(self.btn_profile)

        self.btn_delete = QPushButton("Delete Alignment")
        self.btn_delete.setStyleSheet("color: red;")
        self.btn_delete.clicked.connect(self.on_delete_alignment)
        action_layout.addWidget(self.btn_delete)

        layout.addLayout(action_layout)

        container.setLayout(layout)
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def populate_pi_table(self):
        # 딕셔너리(.get)와 객체(getattr) 모두 지원하도록 안전하게 처리
        if isinstance(self.al_data, dict):
            pis = self.al_data.get('pis', [])
        else:
            pis = getattr(self.al_data, 'pis', [])

        self.pi_table.setRowCount(len(pis))

        for i, p in enumerate(pis):
            is_end = (i == 0 or i == len(pis) - 1)

            # # 번호
            self.pi_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))

            # Easting (X)
            self.pi_table.setItem(i, 1, QTableWidgetItem(fixed(p.get('x', 0), 2)))

            # Northing (Y)
            self.pi_table.setItem(i, 2, QTableWidgetItem(fixed(p.get('y', 0), 2)))

            # Radius (R) - 시점/종점은 '—' 표시
            r_item = QTableWidgetItem("—" if is_end else fixed(p.get('r', 0), 2))
            if is_end:
                r_item.setFlags(r_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.pi_table.setItem(i, 3, r_item)

            # 삭제 버튼 (PI가 2개 초과일 때만)
            if len(pis) > 2:
                btn_del = QPushButton("×")
                btn_del.setFixedWidth(30)
                btn_del.clicked.connect(lambda checked, idx=i: self.remove_pi(idx))
                self.pi_table.setCellWidget(i, 4, btn_del)
            else:
                self.pi_table.setItem(i, 4, QTableWidgetItem(""))

    def update_curves_info(self):
        proj = self.get_project()
        al = proj.alignment(self.al_data.get('id')) if proj and hasattr(proj, 'alignment') else None

        if al and getattr(al, 'ok', False):
            arcs = [e for e in al.elements if e.get('type') == 'arc']
            if arcs:
                info_texts = []
                for c in arcs:
                    sta_pc = format_station(c.get('sta', 0), self.ctx.get('units', 'm'))
                    sta_pt = format_station(c.get('sta', 0) + c.get('len', 0), self.ctx.get('units', 'm'))
                    delta_str = rad_to_dms(c.get('delta', 0))
                    info_texts.append(
                        f"• PC: {sta_pc} ~ PT: {sta_pt} | R={fixed(c.get('r'), 2)}, Δ={delta_str}, Len={fixed(c.get('len'), 2)}"
                    )
                self.curves_label.setText("<br>".join(info_texts))
            else:
                self.curves_label.setText("No curve elements generated.")
        else:
            self.curves_label.setText("Alignment geometry is invalid or not computed.")

    # --- 이벤트 핸들러 메서드들 ---
    def on_name_changed(self):
        new_name = self.name_input.text().strip()[:120]
        self.al_data['name'] = new_name or "Alignment"

    def on_start_changed(self):
        s = parse_station(self.start_input.text(), self.ctx.get('units', 'm'))
        if s is not None:
            self.al_data['start'] = s

    def on_minr_changed(self):
        try:
            val = float(self.minr_input.text()) if self.minr_input.text().strip() else 0.0
            self.al_data['min_r'] = max(0.0, val)
        except ValueError:
            pass

    def remove_pi(self, index):
        pis = getattr(self.al_data, 'pis', [])
        if len(pis) > 2:
            pis.pop(index)
            self.populate_pi_table()
            self.update_curves_info()

    def on_view_profile(self):
        QMessageBox.information(self, "Profile View", "Opening Profile View window...")

    def on_delete_alignment(self):
        reply = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this alignment?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.accept()