import math
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QScrollArea, QWidget, QFormLayout
)
from PyQt6.QtCore import Qt

from alignment import build_alignment


def fixed(val, decimals=2):
    if val is None or not math.isfinite(val):
        return "—"
    return f"{val:.{decimals}f}"


def format_station(sta, units='m'):
    if sta is None:
        return "0+000.00"
    km = int(sta // 1000)
    m = sta % 1000
    return f"{km}+{m:06.2f}"


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
    def __init__(self, alignment_data, project_context, on_change_callback=None, parent=None):
        super().__init__(parent)
        self.al_data = alignment_data
        self.ctx = project_context
        self.on_change_callback = on_change_callback

        self.setWindowTitle(f"Alignment Properties: {self.get_val('name', 'Alignment')}")
        self.resize(500, 700)
        self.init_ui()

    def get_val(self, key, default):
        if isinstance(self.al_data, dict):
            return self.al_data.get(key, default)
        return getattr(self.al_data, key, default)

    def set_val(self, key, val):
        if isinstance(self.al_data, dict):
            self.al_data[key] = val
        else:
            setattr(self.al_data, key, val)
        if self.on_change_callback:
            self.on_change_callback()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)

        u_short = 'm' if self.ctx.get('units', 'm') == 'm' else 'ft'
        form_layout = QFormLayout()

        # 이름 입력 (편집 완료 시 반영)
        self.name_input = QLineEdit(str(self.get_val('name', 'Alignment')))
        self.name_input.editingFinished.connect(lambda: self.set_val('name', self.name_input.text().strip()[:120]))
        form_layout.addRow("Name:", self.name_input)

        # 시작 스테이션 입력
        self.start_input = QLineEdit(format_station(self.get_val('start', 0.0), u_short))
        self.start_input.editingFinished.connect(self.on_start_edited)
        form_layout.addRow("Start Station:", self.start_input)

        # 최소 반경 입력
        min_r_val = self.get_val('min_r', 0.0)
        self.minr_input = QLineEdit(str(min_r_val) if min_r_val > 0 else "")
        self.minr_input.setPlaceholderText("None")
        self.minr_input.editingFinished.connect(self.on_minr_edited)

        minr_layout = QHBoxLayout()
        minr_layout.addWidget(self.minr_input)
        minr_layout.addWidget(QLabel(u_short))
        form_layout.addRow("Minimum Radius:", minr_layout)

        layout.addLayout(form_layout)

        # PI 테이블 설정
        layout.addWidget(QLabel("<b>PI (Intersection Points)</b>"))

        self.pi_table = QTableWidget()
        self.pi_table.setColumnCount(5)
        self.pi_table.setHorizontalHeaderLabels(["#", "Easting", "Northing", "Radius (R)", "Clothoid (Ls)", ""])
        self.pi_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.populate_pi_table()

        # 무한 루프 방지를 위해 cellChanged 사용
        self.pi_table.cellChanged.connect(self.on_cell_changed)
        layout.addWidget(self.pi_table)

        # 곡선 제원 요약
        layout.addWidget(QLabel("<b>Curve Elements</b>"))
        self.curves_label = QLabel()
        self.curves_label.setStyleSheet("color: #444444; background: #f9f9f9; padding: 6px; border-radius: 4px;")
        self.update_curves_info()
        layout.addWidget(self.curves_label)

        container.setLayout(layout)
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def populate_pi_table(self):
        # 테이블 설정 중 시그널을 완벽하게 차단하여 크래시 방지
        self.pi_table.blockSignals(True)
        try:
            pis = self.get_val('pis', [])
            self.pi_table.setRowCount(len(pis))

            for i, p in enumerate(pis):
                is_end = (i == 0 or i == len(pis) - 1)

                item_num = QTableWidgetItem(str(i + 1))
                item_num.setFlags(item_num.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.pi_table.setItem(i, 0, item_num)

                self.pi_table.setItem(i, 1, QTableWidgetItem(fixed(p.get('x', 0), 2)))
                self.pi_table.setItem(i, 2, QTableWidgetItem(fixed(p.get('y', 0), 2)))

                r_item = QTableWidgetItem("—" if is_end else fixed(p.get('r', 0), 2))
                if is_end:
                    r_item.setFlags(r_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.pi_table.setItem(i, 3, r_item)

                # 4: Clothoid Length (Ls)
                ls_item = QTableWidgetItem("—" if is_end else fixed(p.get('ls', 0.0), 2))
                if is_end:
                    ls_item.setFlags(ls_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.pi_table.setItem(i, 4, ls_item)

                if len(pis) > 2:
                    btn_del = QPushButton("×")
                    btn_del.setFixedWidth(30)
                    btn_del.clicked.connect(lambda checked, idx=i: self.remove_pi(idx))
                    self.pi_table.setCellWidget(i, 5, btn_del)
                else:
                    self.pi_table.setItem(i, 4, QTableWidgetItem(""))
        finally:
            self.pi_table.blockSignals(False)

    def on_cell_changed(self, row, col):
        pis = self.get_val('pis', [])
        if row >= len(pis):
            return

        item = self.pi_table.item(row, col)
        if not item:
            return

        try:
            val = float(item.text())
            if col == 1:
                pis[row]['x'] = val
            elif col == 2:
                pis[row]['y'] = val
            elif col == 3 and 0 < row < len(pis) - 1:
                pis[row]['r'] = max(0.0, val)
            elif col == 4 and 0 < row < len(pis) - 1:
                pis[row]['ls'] = max(0.0, val)  # 완화곡선 길이 실시간 반영
            self.update_curves_info()
            if self.on_change_callback:
                self.on_change_callback()
        except ValueError:
            pass

    def on_start_edited(self):
        s = parse_station(self.start_input.text(), self.ctx.get('units', 'm'))
        if s is not None:
            self.set_val('start', s)

    def on_minr_edited(self):
        try:
            val = float(self.minr_input.text()) if self.minr_input.text().strip() else 0.0
            self.set_val('min_r', max(0.0, val))
        except ValueError:
            pass

    def remove_pi(self, index):
        pis = self.get_val('pis', [])
        if len(pis) > 2:
            pis.pop(index)
            self.populate_pi_table()
            self.update_curves_info()
            if self.on_change_callback:
                self.on_change_callback()

    def update_curves_info(self):
        pis = self.get_val('pis', [])
        al = build_alignment(pis, start=self.get_val('start', 0.0))
        if al and al.ok:
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
            self.curves_label.setText("Alignment geometry is invalid (Check minimum radius or overlap).")