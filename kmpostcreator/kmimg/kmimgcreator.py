import textwrap

from PIL import Image, ImageDraw, ImageFont

from model.bveimgdata import BVEImageData


class KMImgCreator:
    @staticmethod
    def create_km_image(imgdata: BVEImageData, work_directory, image_size=(500, 300), font_size=40):
        # 이미지 생성
        img = Image.new('RGB', image_size, color=imgdata.img_bg_color)
        draw = ImageDraw.Draw(img)

        # 폰트 설정
        try:
            font = ImageFont.truetype('c:/windows/fonts/HYGTRE.ttf', font_size)
        except:
            font = ImageFont.truetype('c:/windows/fonts/H2GTRE.ttf', font_size)

        # 텍스트 박스 크기 (25px 여백 적용)
        box_x1, box_y1 = 25, 25
        box_x2, box_y2 = image_size[0] - 25, image_size[1] - 25
        box_width = box_x2 - box_x1
        box_height = box_y2 - box_y1

        # 줄바꿈 적용
        wrapped_text = textwrap.fill(imgdata.km_string, width=15)  # 글자 수 제한
        text_bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # 폰트 크기가 박스를 넘으면 자동 조정
        while text_width > box_width or text_height > box_height:
            font_size -= 2
            font = ImageFont.truetype("gulim.ttc", font_size)
            text_bbox = draw.textbbox((0, 0), wrapped_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

        # 중앙 정렬
        text_x = box_x1 + (box_width - text_width) // 2
        text_y = box_y1 + (box_height - text_height) // 2

        # 이미지에 텍스트 추가
        draw.text((text_x, text_y), wrapped_text, font=font, fill=imgdata.txt_color)

        # 이미지 저장
        KMImgCreator.save_png(img, imgdata.imgname, work_directory)

    @staticmethod
    def create_m_image(imgdata: BVEImageData, work_directory, image_size=(500, 300), font_size=40,
                       font_size2=40):
        img = Image.new('RGB', image_size, color=imgdata.img_bg_color)
        draw = ImageDraw.Draw(img)

        # 폰트 설정
        try:
            font = ImageFont.truetype('c:/windows/fonts/HYGTRE.ttf', font_size)
            font2 = ImageFont.truetype('c:/windows/fonts/HYGTRE.ttf', font_size2)
        except:
            font = ImageFont.truetype('c:/windows/fonts/H2GTRE.ttf', font_size)
            font2 = ImageFont.truetype('c:/windows/fonts/H2GTRE.ttf', font_size2)

        KM_DIGIT_POS = {
            1: (80, 220),
            2: (35, 220),
            3: None,  # 특수 처리
        }
        text = imgdata.km_string
        text2 = imgdata.m_string
        text_color = imgdata.txt_color
        filename = imgdata.imgname

        if len(text) == 3:
            KMImgCreator.draw_three_digits(draw, text, font)
        else:
            x, y = KM_DIGIT_POS.get(len(text), (150, 220))
            draw.text((x, y), text, font=font, fill=text_color)

        draw.text((60, 22), text2, font=font2, fill=text_color)
        KMImgCreator.save_png(img, filename, work_directory)


    @staticmethod
    def load_font(font: str, size: int):
        return ImageFont.truetype(font, size)


    @staticmethod
    def save_png(img, filename, work_directory):
        if not filename.endswith('.png'):
            filename += '.png'
        img.save(work_directory + filename)

    @staticmethod
    def draw_three_digits(
            draw,
            text,
            font,
            positions=(10, 72, 152),
            y=220,
            color=(255, 255, 255)
    ):
        if len(text) != 3 or not text.isdigit():
            raise ValueError("text must be a 3-digit number")

        for digit, x in zip(text, positions):
            draw.text((x, y), digit, font=font, fill=color)

