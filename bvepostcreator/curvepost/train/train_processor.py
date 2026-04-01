import fitz  # pymupdf
import os

class TrainProcessor:
    """일반철도,준고속철도,고속철도용"""
    def __init__(self):
        pass

    def process(self, curvetype: str, station: str, cant: str, filename='output.png', source_directory='',
                           work_directory=''):

        ai_file = os.path.join(source_directory, curvetype + '.AI')

        doc = fitz.open(ai_file)

        # 텍스트 정보 (소수점 자릿수 계산)
        text_parts = station.split('.')  # 소수점을 기준으로 나누기
        if len(text_parts) == 2:  # 소수점이 있는 경우
            digit = len(text_parts[0])  # 소수점 뒤 자릿수
        else:
            digit = 0  # 소수점이 없으면 자릿수는 0

            # 조정값 설정 (자리수에 따라 텍스트 좌표를 조정)
        if digit == 1:
            cooradjust = 20  # 1자리일 경우 좌표 조정 없음
        elif digit == 2:
            cooradjust = 0  # 2자리일 경우 좌표를 왼쪽으로 조정
        elif digit == 3:
            cooradjust = -10  # 3자리일 경우 좌표를 더 왼쪽으로 조정
        else:
            cooradjust = 0  # 그 외의 경우 오른쪽으로 조정

        if curvetype == 'PC' or curvetype == 'CP' or curvetype == 'BC' or curvetype == 'EC':
            x = 121 + cooradjust
            y = 92
        else:
            x = 121 + cooradjust
            y = 115
        # 텍스트 정보(3자리 기준 -10)

        style = "helvetica"
        size = 160.15  # pt 텍스트크기
        color = (255 / 255, 255 / 255, 255 / 255)  # 흰색 (0-1 범위로 변환)

        pt = 2.83465
        # 🔹 mm -> pt 변환 (1mm = 2.83465 pt)
        x_pt = x * pt
        y_pt = y * pt

        size_pt = size  # 이미 pt로 제공되므로 그대로 사용

        # 🔹 텍스트 삽입
        insert_x = x_pt
        insert_y = y_pt

        for page in doc:
            # 텍스트 삽입
            page.insert_text((insert_x, insert_y), station, fontname=style, fontsize=size_pt, color=color)

        # 🔹 원본 크기 가져오기
        page = doc[0]  # 첫 번째 페이지 기준
        pix = page.get_pixmap()
        orig_width, orig_height = pix.width, pix.height

        # 🔹 비율 유지하여 300x200에 맞게 조정
        target_width, target_height = 300, 200
        scale = min(target_width / orig_width, target_height / orig_height)  # 가장 작은 비율 선택
        new_width = int(orig_width * scale)
        new_height = int(orig_height * scale)

        # 🔹 변환 적용 및 PNG 저장
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
        save_file = work_directory + filename + '.png'
        pix.save(save_file)