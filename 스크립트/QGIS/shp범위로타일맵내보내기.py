import math
import requests
from PIL import Image
from io import BytesIO
import time
import os
from qgis.core import (
    QgsProject,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem)

from qgis.PyQt.QtWidgets import (
    QDialog, QFormLayout, QComboBox,
    QSpinBox, QLineEdit, QPushButton,
    QFileDialog, QDialogButtonBox,
    QHBoxLayout, QMessageBox
)

# =========================
# 🔥 VWorld 다운로드 설정 UI
# =========================

class DownloadSettingsDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("VWorld 지도 다운로드 설정")
        self.setMinimumWidth(450)

        layout = QFormLayout(self)

        # 1. 지도 모드
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Street", "Satellite"])
        layout.addRow("지도 모드:", self.mode_combo)

        # 2. Zoom
        self.zoom_spin = QSpinBox()
        self.zoom_spin.setRange(1, 19)
        self.zoom_spin.setValue(16)
        layout.addRow("Zoom:", self.zoom_spin)

        # 3. Segment 시작 번호
        self.start_spin = QSpinBox()
        self.start_spin.setRange(1, 9999)
        self.start_spin.setValue(1)
        layout.addRow("시작 Segment:", self.start_spin)

        # 4. Segment 종료 번호
        self.end_spin = QSpinBox()
        self.end_spin.setRange(1, 9999)
        self.end_spin.setValue(20)
        layout.addRow("종료 Segment:", self.end_spin)

        # 5. 저장 경로
        path_layout = QHBoxLayout()

        self.path_edit = QLineEdit()
        self.path_edit.setText(
            r"D:\BVE\루트\Railway\Object\GTX-A\지형"
        )

        browse_button = QPushButton("찾아보기")
        browse_button.clicked.connect(self.select_folder)

        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_button)

        layout.addRow("저장 경로:", path_layout)

        # 6. 실행 / 취소 버튼
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok |
            QDialogButtonBox.Cancel
        )

        buttons.button(
            QDialogButtonBox.Ok
        ).setText("다운로드 시작")

        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def select_folder(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "저장 폴더 선택",
            self.path_edit.text()
        )

        if folder:
            self.path_edit.setText(folder)

    def validate_and_accept(self):

        if self.start_spin.value() > self.end_spin.value():
            QMessageBox.warning(
                self,
                "설정 오류",
                "시작 Segment는 종료 Segment보다 클 수 없습니다."
            )
            return

        if not self.path_edit.text().strip():
            QMessageBox.warning(
                self,
                "설정 오류",
                "저장 경로를 지정하세요."
            )
            return

        self.accept()

# =========================
# 🔥 타일 좌표 변환
# =========================
def deg2num(lat, lon, zoom):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return xtile, ytile

# =========================
# 타일 다운로드
# =========================
def get_tile(x, y, z):

    if mode == "Street":
        url = (
            f"https://xdworld.vworld.kr/"
            f"2d/Base/service/{z}/{x}/{y}.png"
        )

    elif mode == "Satellite":
        url = (
            f"https://xdworld.vworld.kr/"
            f"2d/Satellite/service/{z}/{x}/{y}.jpeg"
        )

    time.sleep(0.05)

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(
        url,
        headers=headers,
        timeout=10
    )

    r.raise_for_status()

    return Image.open(
        BytesIO(r.content)
    ).convert("RGB")

# =========================
# 🔥 extent → 위경도 변환
# =========================
def extent_to_wgs84(extent, crs):
    transform = QgsCoordinateTransform(
        crs,
        QgsCoordinateReferenceSystem("EPSG:4326"),
        QgsProject.instance()
    )

    min_pt = transform.transform(extent.xMinimum(), extent.yMinimum())
    max_pt = transform.transform(extent.xMaximum(), extent.yMaximum())

    return (
        min_pt.y(), min_pt.x(),  # min_lat, min_lon
        max_pt.y(), max_pt.x()   # max_lat, max_lon
    )
def deg2num_float(lat, lon, zoom):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n
    return x, y

# =========================
# 🔥 타일 다운로드 + 합성
# =========================
def download_and_stitch(min_lat, min_lon, max_lat, max_lon, zoom):
    tile_size = 256

    # 🔥 float tile 좌표 (핵심)
    x_min_f, y_max_f = deg2num_float(min_lat, min_lon, zoom)
    x_max_f, y_min_f = deg2num_float(max_lat, max_lon, zoom)

    # 🔥 타일 index
    x_min = int(x_min_f)
    x_max = int(x_max_f)
    y_min = int(y_min_f)
    y_max = int(y_max_f)

    # 🔥 전체 타일 이미지 생성
    width = (x_max - x_min + 1) * tile_size
    height = (y_max - y_min + 1) * tile_size
    full_img = Image.new("RGB", (width, height))

    # 🔥 타일 붙이기
    for x in range(x_min, x_max + 1):
        for y in range(y_min, y_max + 1):
            try:
                tile = get_tile(x, y, zoom)
                px = (x - x_min) * tile_size
                py = (y - y_min) * tile_size
                full_img.paste(tile, (px, py))
            except Exception as e:
                raise RuntimeError(
                    f"타일 다운로드 실패: "
                    f"Zoom={zoom}, X={x}, Y={y}\n{e}"
                ) from e

    # =========================
    # 🔥 여기부터가 핵심 (crop)
    # =========================

    crop_x_min = int((x_min_f - x_min) * tile_size)
    crop_y_min = int((y_min_f - y_min) * tile_size)
    crop_x_max = int((x_max_f - x_min) * tile_size)
    crop_y_max = int((y_max_f - y_min) * tile_size)

    cropped = full_img.crop((crop_x_min, crop_y_min, crop_x_max, crop_y_max))

    return cropped


# =========================
# 🔥 UI 실행 및 설정값 가져오기
# =========================

dialog = DownloadSettingsDialog()

if dialog.exec_() != QDialog.Accepted:
    raise RuntimeError("다운로드가 취소되었습니다.")

mode = dialog.mode_combo.currentText()
zoom = dialog.zoom_spin.value()

start_segment = dialog.start_spin.value()
end_segment = dialog.end_spin.value()

output_path = dialog.path_edit.text().strip()

os.makedirs(output_path, exist_ok=True)

print("=" * 45)
print("VWorld 지도 다운로드 설정")
print(f"지도 모드     : {mode}")
print(f"Zoom          : {zoom}")
print(f"Segment 범위  : {start_segment} ~ {end_segment}")
print(f"저장 경로     : {output_path}")
print("=" * 45)

# =========================
# 🔥 실행
# =========================
project = QgsProject.instance()

for i in range(start_segment,end_segment + 1):
    layer_name = f"segment_{i}"
    layers = project.mapLayersByName(layer_name)

    if not layers:
        print(f"{layer_name} 없음")
        continue

    layer = layers[0]
    extent = layer.extent()

    if extent.width() == 0 or extent.height() == 0:
        print(f"{layer_name} extent 오류")
        continue

    print(f"{layer_name} 처리중...")


    # 🔥 extent → 위경도
    min_lat, min_lon, max_lat, max_lon = extent_to_wgs84(extent, layer.crs())

    # 🔥 타일 다운로드 + 합성
    image = download_and_stitch(min_lat, min_lon, max_lat, max_lon, zoom)

    # 🔥 저장
    filename = os.path.join(
        output_path,
        f"{layer_name}.png"
    )

    image.save(filename)





    print(f"{filename} 저장 완료")
    time.sleep(1)
print("모든 파일 저장 완료")