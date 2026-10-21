import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from section_view import SectionView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CivilCraft - Cross Section View")
        self.resize(800, 500)

        # 뷰어 위젯 생성
        self.view = SectionView(self)
        self.setCentralWidget(self.view)

        # 샘플 데이터 주입 테스트
        sample_data = {
            'station': 'Sta. 10+00.00',
            'exaggeration': 2.0,
            'labels': {'cut': 'Cut Area: 12.5 sq ft', 'fill': 'Fill Area: 0.0 sq ft', 've': 'VE: 2×'},
            'section': {
                'left': 20.0, 'right': 20.0,
                'ground': [[{'o': -20, 'z': 100}, {'o': 0, 'z': 98}, {'o': 20, 'z': 101}]],
                'design': [[{'o': -12, 'z': 99.76}, {'o': 0, 'z': 100}, {'o': 12, 'z': 99.76}]],
                'parts': [{'o0': -12, 'o1': 0, 'kind': 'fill'}, {'o0': 0, 'o1': 12, 'kind': 'cut'}],
                'marks': [{'code': 'CL', 'o': 0, 'z': 100}, {'code': 'EOP_L', 'o': -12, 'z': 99.76}]
            }
        }
        self.view.set_data(sample_data)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())