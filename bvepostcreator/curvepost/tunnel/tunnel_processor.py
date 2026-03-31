import ezdxf


class TunnelProcessor:
    """터널 구간용 곡선표이미지 처리"""
    def __init__(self, source_directory, work_directory):
        self.source_directory = source_directory
        self.work_directory = work_directory

    # DXF 파일을 생성하는 함수
    def process(self, filename, text):
        doc = ezdxf.new()  # 새로운 DXF 문서 생성
        msp = doc.modelspace()

        # 사각형의 크기 설정
        width = 240
        height = 200
        start_point = (0, 0)
        insert_x, insert_y = start_point[0], start_point[1]

        # 사각형의 4개 점 계산
        left_bottom = (insert_x, insert_y)
        right_bottom = (insert_x + width, insert_y)
        right_top = (insert_x + width, insert_y + height)
        left_top = (insert_x, insert_y + height)

        # 사각형을 그리기 위해 4개의 점을 이어서 폴리라인 추가
        msp.add_lwpolyline([left_bottom, right_bottom, right_top, left_top, left_bottom], close=True)

        # 해치 추가
        hatch = msp.add_hatch(color=5)
        hatch.paths.add_polyline_path([left_bottom, right_bottom, right_top, left_top], is_closed=True)

        # 텍스트 길이에 따른 위치 지정
        if len(text) == 3:
            width = 1.056
        elif len(text) == 4:
            width = 0.792
        elif len(text) == 5:
            width = 0.633
        else:
            width = 1
        text_x, text_y = 49.573, 65.152
        style_name = 'GHS'

        # 텍스트 스타일 생성
        try:
            doc.styles.add(style_name, font='H2GTRE.ttf')
        except:
            doc.styles.add(style_name, font='HYGTRE.ttf')

        # 텍스트 추가
        msp.add_text(text, dxfattribs={'insert': (text_x, text_y), 'height': 75, 'width': width, 'style': style_name})

        # 파일 확장자 확인
        if not filename.endswith('.dxf'):
            filename += '.dxf'

        # DXF 파일 저장
        final_dir = self.work_directory + filename
        doc.saveas(filename)