import os
from PIL import Image, ImageDraw, ImageFont

class NormalGradePostCreator:
    """일반철도용 기울기표 생성기"""
    def __init__(self, work_directory: str):
        self.work_directory = work_directory
        if not os.path.exists(self.work_directory):
            os.makedirs(self.work_directory)

    def create_text_image(self, text, font, text_color, image_size, rotate_angle=0):
        text_image = Image.new('RGBA', image_size, (255, 255, 255, 0))
        text_draw = ImageDraw.Draw(text_image)
        text_draw.text((20, 20), text, font=font, fill=text_color)
        rotated_text_image = text_image.rotate(rotate_angle, expand=True)
        bbox = rotated_text_image.getbbox()
        cropped_temp_img = rotated_text_image.crop(bbox) if bbox else rotated_text_image
        white_bg = Image.new('RGB', cropped_temp_img.size, (255, 255, 255))
        white_bg.paste(cropped_temp_img, (0, 0), cropped_temp_img.split()[3])
        return white_bg

    def create_arrow_symbol(self, image_size, text_color, is_negative):
        arrow_image = Image.new('RGBA', image_size, (255, 255, 255, 0))
        arrow_draw = ImageDraw.Draw(arrow_image)
        arrow_points = [(372, 70), (417, 42), (401, 15), (456, 38), (458, 98), (440, 73), (393, 104), (372, 70)]
        arrow_draw.polygon(arrow_points, fill=text_color, outline=text_color)
        return arrow_image.transpose(Image.FLIP_TOP_BOTTOM) if is_negative else arrow_image

    def create_grade_post(self, text, text2, filename, text_color, post_direction, image_size=(500, 400),
                          font_size1=180, font_size2=100):
        img = Image.new('RGB', image_size, (255, 255, 255))
        draw = ImageDraw.Draw(img)
        try:
            font_main = ImageFont.truetype('c:/windows/fonts/HYGTRE.ttf', font_size1)
            font_sub = ImageFont.truetype("gulim.ttc", font_size2)
        except:
            font_main = ImageFont.truetype('c:/windows/fonts/H2GTRE.ttf', font_size1)
            font_sub = ImageFont.truetype("gulim.ttc", font_size2)

        is_negative = text.startswith('-')
        integer_part, decimal_part = text.lstrip('-').split('.') if '.' in text else (text.lstrip('-'), None)
        rotate_angle = -30 if is_negative else 30
        if text == '0':
            white_bg = img
        else:
            white_bg = self.create_text_image(integer_part, font_main, text_color, image_size, rotate_angle)
        post_positions = {'좌': (107, 70 if int(integer_part) > 9 else 110), '우': (110, 110)}
        img.paste(white_bg, post_positions.get(post_direction, (110, 110)))

        if decimal_part:
            try:
                font_decimal = ImageFont.truetype('c:/windows/fonts/HYGTRE.ttf', 75)
            except:
                font_decimal = ImageFont.truetype('c:/windows/fonts/H2GTRE.ttf', 75)
            decimal_bg = self.create_text_image(decimal_part, font_decimal, text_color, image_size, rotate_angle)
            decimal_positions = self.get_decimal_position(post_direction, integer_part, is_negative)
            img.paste(decimal_bg, decimal_positions)

        draw.line([(0, 280), (500, 280)], fill=text_color, width=10)
        distance_positions = self.get_distance_position(post_direction, text2)
        distance_text = f'L={text2}M'
        draw.text(distance_positions, distance_text, font=font_sub, fill=text_color)
        if text == '0':
            arrow_image = self.create_L_symbol(image_size, text_color)
        else:
            arrow_image = self.create_arrow_symbol(image_size, text_color, is_negative)

        img.paste(arrow_image, (0, -120 if is_negative else 0), arrow_image)

        if not filename.endswith('.png'):
            filename += '.png'
        final_dir = os.path.join(self.work_directory, filename)
        img.save(final_dir)
        # print(f"최종 이미지 저장됨: {final_dir}")

    def get_decimal_position(self, post_direction, integer_part, is_negative):
        if post_direction == '좌':
            if int(integer_part) > 9:  # 구배가 2자리
                return (330, 140) if is_negative else (310, 40)
            else:  # 구배가 1자리
                return (240, 160) if is_negative else (200, 60)
        return (110, 110)  # '우' 기본 위치

    def get_distance_position(self, post_direction, integer_part):
        if post_direction == '좌':

            if len(integer_part) == 3:  # 거리가 3자리
                return (100, 290)
            elif len(integer_part) == 4:  # 거리가 4자리
                return (75, 290)
            else:
                return (60, 290)

    def create_L_symbol(self, image_size, text_color):
        arrow_image = Image.new('RGBA', image_size, (255, 255, 255, 0))
        arrow_draw = ImageDraw.Draw(arrow_image)
        arrow_points = [(121, 42), (121, 242), (313, 242), (313, 181), (171, 181), (171, 42)]
        arrow_draw.polygon(arrow_points, fill=text_color, outline=text_color)
        return arrow_image
