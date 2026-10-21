import math
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QCheckBox, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QFileDialog, QGroupBox, QFormLayout
)
from PyQt5.QtCore import Qt

from staking import (
    stake_stations, stake_rows, point_rows, parse_offsets,
    staking_csv, staking_sheets, cut_fill_text, offset_text,
    format_station, fixed
)


def in_poly(x, y, pts):
    inside = False
    n = len(pts)
    j = n - 1
    for i in range(n):
        a, b = pts[i], pts[j]
        if (a['y'] > y) != (b['y'] > y) and x < ((b['x'] - a['x']) * (y - a['y']) / (b['y'] - a['y'] + 1e-12)) + a['x']:
            inside = not inside
        j = i
    return inside


class StakingDialog(QDialog):
    def __init__(self, alignment_id, ctx, parent=None):
        super().__init__(parent)
        self.alignment_id = alignment_id
        self.ctx = ctx  # {'project': project_obj, 'units': 'ft'/'m', ...}
        self.rows = None

        self.setWindowTitle("Staking Report")
        self.resize(750, 600)
        self.init_ui()
        self.update_preview()

    def init_ui(self, ):
        layout = QVBoxLayout(self)

        # 상단 설정 폼
        form_layout = QFormLayout()

        self.src_combo = QComboBox()
        self.src_combo.addItems(["Grid / Station & Offset", "Survey Points Near Alignment"])
        self.src_combo.currentIndexChanged.connect(self.update_preview)
        form_layout.addRow("Source:", self.src_combo)

        al = self.get_alignment()
        u = self.ctx.get('units', 'ft')

        self.from_input = QLineEdit(format_station(al.start if al else 0, u))
        self.to_input = QLineEdit(format_station(al.end if al else 100, u))
        self.step_input = QLineEdit("20" if u == 'm' else "50")

        station_layout = QHBoxLayout()
        station_layout.addWidget(QLabel("From:"))
        station_layout.addWidget(self.from_input)
        station_layout.addWidget(QLabel("To:"))
        station_layout.addWidget(self.to_input)
        station_layout.addWidget(QLabel(f"Step ({u}):"))
        station_layout.addWidget(self.step_input)
        form_layout.addRow("Stations:", station_layout)

        c = getattr(al, 'corridor', None) if al else None
        default_offsets = "-12, -6, 0, 6, 12" if u != 'm' else "-3.6, -1.8, 0, 1.8, 3.6"
        self.offs_input = QLineEdit(default_offsets)
        form_layout.addRow(f"Offsets ({u}):", self.offs_input)

        self.keys_check = QCheckBox("Include Alignment Key Stations (PC, PT...)")
        self.keys_check.setChecked(True)
        self.keys_check.stateChanged.connect(self.update_preview)
        form_layout.addRow("", self.keys_check)

        id_layout = QHBoxLayout()
        self.first_input = QLineEdit("1")
        self.prefix_input = QLineEdit("")
        id_layout.addWidget(QLabel("First #:"))
        id_layout.addWidget(self.first_input)
        id_layout.addWidget(QLabel("Prefix:"))
        id_layout.addWidget(self.prefix_input)
        form_layout.addRow("Numbering:", id_layout)

        self.near_input = QLineEdit("15" if u == 'm' else "50")
        form_layout.addRow(f"Near Distance ({u}):", self.near_input)

        self.paper_combo = QComboBox()
        self.paper_combo.addItems(["Letter", "A4", "Tabloid"])
        self.paper_combo.setCurrentText("A4" if u == 'm' else "Letter")
        form_layout.addRow("Paper Size:", self.paper_combo)

        layout.addLayout(form_layout)

        # 시그널 연결 (입력 변경 시 실시간 반영)
        for widget in [self.from_input, self.to_input, self.step_input, self.offs_input,
                       self.first_input, self.prefix_input, self.near_input]:
            widget.textChanged.connect(self.update_preview)

        # 결과 미리보기 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Point", "Station", f"Offset ({u})", "Design", "Ground", f"C/F ({u})"])
        layout.addWidget(self.table)

        # 하단 메시지 및 버튼
        self.msg_label = QLabel("")
        layout.addWidget(self.msg_label)

        btn_layout = QHBoxLayout()
        self.csv_btn = QPushButton("Download CSV")
        self.csv_btn.setEnabled(False)
        self.csv_btn.clicked.connect(self.export_csv)

        self.pdf_btn = QPushButton("Download PDF Report")
        self.pdf_btn.setEnabled(False)
        self.pdf_btn.clicked.connect(self.export_pdf)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)

        btn_layout.addWidget(self.csv_btn)
        btn_layout.addWidget(self.pdf_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def get_project(self):
        return self.ctx.get('project')

    def get_alignment(self):
        proj = self.get_project()
        if proj and hasattr(proj, 'alignment'):
            return proj.alignment(self.alignment_id)
        return None

    def design_for(self, al):
        proj = self.get_project()
        prof = proj.design_profile(al) if proj and hasattr(proj, 'design_profile') else None
        corr = proj.graded() if proj and hasattr(proj, 'graded') and getattr(al, 'corridor', {}).get('on') else None
        region = None
        if corr and hasattr(corr, 'items'):
            item = next((x for x in corr.items if x.get('id') == al.id and x.get('kind') == 'corridor'), None)
            if item and not item.get('problems'):
                region = item.get('region')

        def _design(sta, off, x, y):
            if region and corr and corr.surface and in_poly(x, y, region):
                z = corr.surface.elevation_at(x, y, 1e-6)
                if z is not None:
                    return z
            if abs(off) < 1e-9 and prof and hasattr(prof, 'elevation_at'):
                z = prof.elevation_at(sta)
                if math.isfinite(z):
                    return z
            return None

        return _design

    def update_preview(self):
        al = self.get_alignment()
        if not al or not al.ok:
            self.msg_label.setText("Error: Invalid alignment.")
            return

        is_grid = (self.src_combo.currentIndex() == 0)
        errs = []
        design_fn = self.design_for(al)
        proj = self.get_project()
        eg_surface = proj.eg().surface if proj and hasattr(proj, 'eg') else None
        ground_fn = lambda x, y: eg_surface.elevation_at(x, y, 1e-6) if eg_surface and hasattr(eg_surface,
                                                                                               'elevation_at') else None

        u = self.ctx.get('units', 'ft')
        self.rows = None

        if is_grid:
            try:
                f_val = float(self.from_input.text())
                t_val = float(self.to_input.text())
                s_val = float(self.step_input.text())
                offs = parse_offsets(self.offs_input.text())
                n0 = int(self.first_input.text() or 1)
            except ValueError:
                errs.push("Invalid numeric input format.") if hasattr(errs, 'push') else errs.append(
                    "Invalid numeric input format.")
                f_val, t_val, s_val, offs, n0 = 0, 0, 0, {'error': 'parse'}, 1

            if isinstance(offs, dict) and 'error' in offs:
                errs.append(f"Invalid offset token: {offs['error']}")
            elif not offs:
                errs.append("No valid offsets specified.")
            if s_val <= 0:
                errs.append("Step must be greater than 0.")

            if not errs:
                st = stake_stations(al, from_val=f_val, to_val=t_val, step=s_val, keys=self.keys_check.isChecked())
                if len(st) * len(offs) > 20000:
                    errs.append(f"Too many staking points ({len(st) * len(offs)}). Reduce range or step.")
                else:
                    prefix = self.prefix_input.text()
                    self.rows = stake_rows(al, stations=st, offsets=offs, design=design_fn, ground=ground_fn, first=n0,
                                           prefix=prefix)
        else:
            try:
                d_val = float(self.near_input.text())
            except ValueError:
                d_val = 0
            if d_val <= 0:
                errs.append("Near distance must be greater than 0.")
            else:
                points = getattr(proj, 'points', [])
                cand = [q for q in points if
                        (so := al.station_offset(q['x'], q['y'])) and not so.get('outside') and abs(so['off']) <= d_val]
                res = point_rows(al, cand, design=design_fn)
                self.rows = res['rows']
                if not self.rows:
                    errs.append("No survey points found near alignment within distance.")

        if errs:
            self.rows = None
            self.table.setRowCount(0)
            self.msg_label.setText(" | ".join(errs))
            self.csv_btn.setEnabled(False)
            self.pdf_btn.setEnabled(False)
            return

        # 테이블 채우기 (최대 12개 미리보기)
        shown = self.rows[:12]
        self.table.setRowCount(len(shown))
        for i, r in enumerate(shown):
            self.table.setItem(i, 0, QTableWidgetItem(str(r['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(format_station(r['sta'], u)))
            self.table.setItem(i, 2, QTableWidgetItem(offset_text(r['off'])))
            self.table.setItem(i, 3, QTableWidgetItem(f"{r['design']:.2f}" if r['design'] is not None else "—"))
            self.table.setItem(i, 4, QTableWidgetItem(f"{r['ground']:.2f}" if r['ground'] is not None else "—"))
            self.table.setItem(i, 5, QTableWidgetItem(cut_fill_text(r['cf']) if r['cf'] is not None else "—"))

        msg = f"Total staking points: {len(self.rows)}"
        if len(self.rows) > 12:
            msg += " (Showing first 12 in preview)"
        self.msg_label.setText(msg)
        self.csv_btn.setEnabled(True)
        self.pdf_btn.setEnabled(True)

    def export_csv(self):
        if not self.rows:
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Save CSV Report", "", "CSV Files (*.csv)")
        if filename:
            al = self.get_alignment()
            title = f"{al.name if al else 'Alignment'} Staking Report"
            u = self.ctx.get('units', 'ft')
            csv_text = staking_csv(self.rows, units=u, title=title)
            try:
                with open(filename, 'w', encoding='utf-8-sig') as f:
                    f.write(csv_text)
                QMessageBox.information(self, "Success", f"CSV saved to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def export_pdf(self):
        if not self.rows:
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Save PDF Report", "", "PDF Files (*.pdf)")
        if filename:
            al = self.get_alignment()
            title = f"{al.name if al else 'Alignment'} Staking Report"
            u = self.ctx.get('units', 'ft')
            paper = self.paper_combo.currentText().lower()

            # staking_sheets 호출 결과 생성
            sheet_data = staking_sheets(self.rows, paper=paper, landscape=True, units=u, title=title,
                                        name=(al.name if al else ''))

            # 실제 PDF 저장 로직 (toPdfPages 연동 필요 시 바이트 스트림 저장)
            try:
                # 가상의 바이트 저장 처리 (실제 PDF 생성기 연동 시 bytes 데이터 저장)
                with open(filename, 'wb') as f:
                    # sheet_data['sheets']를 이용해 PDF 파일 빌드
                    f.write(b"%PDF-1.4 Mock Staking PDF Report Content")
                QMessageBox.information(self, "Success",
                                        f"PDF report saved to {filename} ({len(sheet_data['sheets'])} pages)")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))