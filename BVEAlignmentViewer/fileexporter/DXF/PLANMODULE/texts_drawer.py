from model.ipdata import IPdata


class TextsDrawer:
    def __init__(self, msp):
        self.msp = msp

    def draw_texts(self, ipdata_list: list[IPdata], layer: str, text_func):
        """
        텍스트 추가용 공통 메소드
        Args:
            ipdata_list: IPdata 리스트
            layer: 문자열, 레이어 이름
            text_func: 각 IPdata에 대해 문자열 반환 함수
        """
        for i, ip in enumerate(ipdata_list):
            text = text_func(ip, i, len(ipdata_list))
            if text:
                self.msp.add_text(text, dxfattribs={
                    'insert': (ip.coord.x, ip.coord.y),
                    'height': 5,
                    'color': 1,
                    'layer': layer,
                    'style': 'Gulim'
                })
    def draw_mtexts(self, ipdata_list: list[IPdata], layer: str, text_func):
        """
        텍스트 추가용 공통 메소드
        Args:
            ipdata_list: IPdata 리스트
            layer: 문자열, 레이어 이름
            text_func: 각 IPdata에 대해 문자열 반환 함수
        """
        for i, ip in enumerate(ipdata_list):
            text = text_func(ip, i, len(ipdata_list))
            if text:
                self.msp.add_mtext(text, dxfattribs={
                    'insert': (ip.coord.x, ip.coord.y),
                    'char_height': 5,
                    'color': 1,
                    'layer': layer,
                    'style': 'Gulim'
                })