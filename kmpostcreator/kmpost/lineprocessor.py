class LineProcessor:
    LAYER_RULES = {
        "일반철도": {
            "km": {
                1: [("1자리", lambda km, m: km)],
                2: [
                    ("2자리-앞", lambda km, m: km[0]),
                    ("2자리-뒤", lambda km, m: km[1]),
                ],
                3: [
                    ("3자리-앞", lambda km, m: km[0]),
                    ("3자리-뒤", lambda km, m: km[2]),
                    ("1자리", lambda km, m: km[1]),
                ],
            },
            "m": {
                1: [
                    ("1자리", lambda km, m: km),
                    ("m", lambda km, m: m),
                ],
                2: [
                    ("2자리-앞", lambda km, m: km[0]),
                    ("2자리-뒤", lambda km, m: km[1]),
                    ("m", lambda km, m: m),
                ],
                3: [
                    ("3자리-앞", lambda km, m: km[0]),
                    ("1자리", lambda km, m: km[1]),
                    ("3자리-뒤", lambda km, m: km[2]),
                    ("m", lambda km, m: m),
                ],
            }
        },
        "도시철도": {
            "km": {
                1: [("KM-1자리", lambda km, m: km)],
                2: [("KM-2자리", lambda km, m: km)],
            },
            "m": {
                1: [
                    ("KM-1자리", lambda km, m: km),
                    ("M-1자리", lambda km, m: m[0]),
                ],
                2: [
                    ("KM-2자리-앞", lambda km, m: km[0]),
                    ("KM-2자리-뒤", lambda km, m: km[1]),
                    ("M-1자리", lambda km, m: m[0]),
                ],
            },
        },
    }

    def __init__(self, file_path, modified_path, kmtext, mtext, line_type="normal"):
        self.file_path = file_path
        self.modified_path = modified_path
        self.kmtext = kmtext
        self.mtext = mtext
        self.line_type = line_type  # "normal" or "city"

    def replace_text_in_dxf(self, mode="km"):
        """DXF 텍스트 교체"""
        try:
            doc = ezdxf.readfile(self.file_path)
            msp = doc.modelspace()
            layers = doc.layers

            rules = self.LAYER_RULES[self.line_type][mode]
            length = len(self.kmtext)

            if length not in rules:
                raise ValueError(f"길이 {length}에 대한 규칙 없음")

            for entity in msp.query("TEXT"):
                for layer, text_func in rules[length]:
                    if entity.dxf.layer == layer:
                        entity.dxf.text = text_func(self.kmtext, self.mtext)
                        layers.get(layer).on()

            doc.saveas(self.modified_path)
            return True

        except Exception as e:
            print(f"❌ DXF 수정 실패: {e}")
            return False