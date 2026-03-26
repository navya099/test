import ezdxf
import os

class TunnelPitchCreator:
    """터널 구배 DXF 파일을 생성하는 클래스"""

    def __init__(self, work_directory):
        self.work_directory = work_directory

    def create_tunnel_pitch_image(self, filename, text):
        """터널 구배 DXF 생성"""
        doc = ezdxf.new()
        msp = doc.modelspace()

        # 기본 사각형 추가
        self.draw_rectangle(msp, 0, 0, 238, 150, color=8)

        # 텍스트 전처리 (공백 처리 등)
        formatted_result = self.format_text(text)

        # 정수부 및 소수부 분리
        formatted_text, text_x, text_y, is_negative = formatted_result[:4]

        # 텍스트 스타일 설정 및 추가
        style_name = 'GHS'
        try:
            doc.styles.add(style_name, font='H2GTRE.ttf')
        except:
            doc.styles.add(style_name, font='HYGTRE.ttf')

        # 정수부 텍스트 추가
        self.create_text(msp, formatted_text, text_x, text_y, 59.9864, 1, style_name)

        # 소수부가 존재하면 추가
        if len(formatted_result) > 4:
            formatted_text2, text_x2, text_y2, height2 = formatted_result[4:]
            self.create_text(msp, formatted_text2, text_x2, text_y2, height2, 0.8162, style_name)
            if is_negative:
                x = 161.376
                y = 76.37

            else:
                x = 161.376
                y = 13.5468
            width = 10
            height = 10

            self.draw_rectangle_with_hatch(msp, x, y, width, height, color=1)  # 소수점 그리기

        # 화살표 추가
        if not 'L' in formatted_text:
            self.create_tunnel_pitch_arrow(msp, is_negative)

        # DXF 저장
        final_path = os.path.join(self.work_directory, filename)
        doc.saveas(final_path)
        return final_path

    def draw_rectangle(self, msp, x, y, width, height, color=0):
        """사각형을 생성하는 함수"""
        points = [(x, y), (x + width, y), (x + width, y + height), (x, y + height), (x, y)]
        msp.add_lwpolyline(points, close=True, dxfattribs={'color': color})

    def draw_rectangle_with_hatch(self, msp, x, y, width, height, color=0):
        """사각형을 생성하는 함수(해치포함)"""
        points = [(x, y), (x + width, y), (x + width, y + height), (x, y + height), (x, y)]
        msp.add_lwpolyline(points, close=True, dxfattribs={'color': color})
        hatch = msp.add_hatch(color=1)
        hatch.paths.add_polyline_path(points, is_closed=True)

    def format_text(self, text):
        """텍스트를 포맷팅하여 위치 값과 함께 반환"""
        is_negative = text.startswith('-')
        integer_part, decimal_part = text.lstrip('-').split('.') if '.' in text else (text.lstrip('-'), None)

        # 텍스트 길이에 따라 공백 처리
        if not is_negative:  # 상구배
            if len(text) == 1:  # 3
                formatted_text = '  L' if integer_part == '0' else '  ' + integer_part
            elif len(text) == 2:  # 13
                formatted_text = ' ' + integer_part
            elif len(text) == 3:  # 1.1
                formatted_text = ' ' + integer_part  # 정수부만 사용
            elif len(text) == 4:  # 27.4
                formatted_text = integer_part  # 정수부만 사용

            text_x, text_y = 60.7065, 13.5468  # 정수부 위치

            if decimal_part:  # 소수부가 있는 경우
                formatted_text2 = decimal_part  # 소수부만 사용
                text_x2, text_y2 = 176.0235, 28.5329  # 소수부 위치
                height2 = 45.043  # 소수부 글자 크기
                return formatted_text, text_x, text_y, is_negative, formatted_text2, text_x2, text_y2, height2

        else:  # 하구배
            if len(text) == 2:  # -3
                formatted_text = '  L' if integer_part == '0' else '  ' + integer_part
            elif len(text) == 3:  # -11
                formatted_text = ' ' + integer_part
            elif len(text) == 4:  # -4.5
                formatted_text = ' ' + integer_part  # 정수부만 사용
            elif len(text) == 5:  # -11.5
                formatted_text = integer_part  # 정수부만 사용

            text_x, text_y = 60.7065, 76.37  # 정수부 위치

            if decimal_part:  # 소수부가 있는 경우
                formatted_text2 = decimal_part  # 소수부만 사용
                text_x2, text_y2 = 176.0235, 91.3561  # 소수부 위치
                height2 = 45.043  # 소수부 글자 크기
                return formatted_text, text_x, text_y, is_negative, formatted_text2, text_x2, text_y2, height2

        return formatted_text, text_x, text_y, is_negative  # 소수부가 없으면 정수부만 반환

    def create_text(sefl, msp, text, text_x, text_y, height, width, style_name):
        msp.add_text(text, dxfattribs={
            'insert': (text_x, text_y),
            'height': height,
            'width': width,
            'style': style_name,
            'color': 1
        })

    def create_tunnel_pitch_arrow(self, msp, is_negative):
        """터널 구배 화살표 생성"""
        if not is_negative:  # 상구배
            points = [
                (115.825, 116.333), (135.8065, 136.3991), (155.8726, 116.333), (155.8726, 102.1935),
                (140.8865, 117.2643), (140.8865, 91.3561), (130.8111, 91.3561), (130.8111, 117.2643),
                (115.825, 102.1935)
            ]
        else:  # 하구배
            points = [
                (115.9096, 33.6129), (135.8911, 13.5468), (155.8726, 33.6129), (155.8726, 47.7524),
                (140.8865, 32.7663), (140.8865, 58.5898), (130.8958, 58.5898), (130.8958, 32.7663),
                (115.9096, 47.7524)
            ]

        # 화살표 추가
        msp.add_lwpolyline(points, close=True, dxfattribs={'color': 1})
        hatch = msp.add_hatch(color=1)
        hatch.paths.add_polyline_path(points, is_closed=True)