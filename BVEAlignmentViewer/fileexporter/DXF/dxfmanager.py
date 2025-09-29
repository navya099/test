import ezdxf

class DXFManager:
    def __init__(self):
        self.msp = None
        self.doc = None

    def create(self):
        self.doc = ezdxf.new()
        self.msp = self.doc.modelspace()

    def save(self, filepath):
        self.doc.saveas(filepath)

    def clear(self):
        self.msp = None
        self.doc = None
    def read(self, filepath):
        pass

    def create_style(self, style, font):
        """
        ️ 글꼴 스타일 생성
        Args:
            style: 스타일이름
            font: 폰트파일명
        """
        if style not in self.doc.styles:
            self.doc.styles.new(style, dxfattribs={'font': font})
