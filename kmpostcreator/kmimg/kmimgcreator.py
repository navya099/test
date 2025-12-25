class KMImgCreator:
    def __init__(self):
        pass

    def create_km_image(text, bg_color, filename, text_color, work_directory, image_size=(500, 300), font_size=40):
        # 이미지 생성
        img = Image.new('RGB', image_size, color=bg_color)
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
        wrapped_text = textwrap.fill(text, width=15)  # 글자 수 제한
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
        draw.text((text_x, text_y), wrapped_text, font=font, fill=text_color)

        # 이미지 저장
        if not filename.endswith('.png'):
            filename += '.png'
        final_dir = work_directory + filename
        img.save(final_dir)

    def create_m_image(text, text2, bg_color, filename, text_color, work_directory, image_size=(500, 300), font_size=40,
                       font_size2=40):
        # 이미지 생성
        img = Image.new('RGB', image_size, color=bg_color)
        draw = ImageDraw.Draw(img)

        # 폰트 설정
        try:
            font = ImageFont.truetype('c:/windows/fonts/HYGTRE.ttf', font_size)
            font2 = ImageFont.truetype('c:/windows/fonts/HYGTRE.ttf', font_size2)
        except:
            font = ImageFont.truetype('c:/windows/fonts/H2GTRE.ttf', font_size)
            font2 = ImageFont.truetype('c:/windows/fonts/H2GTRE.ttf', font_size2)
        # km문자 위치
        # 글자수별로 글자 분리
        if len(text) == 1:
            text_x = 80
            text_y = 220
        elif len(text) == 2:
            text_x = 35
            text_y = 220
        elif len(text) == 3:
            text_x = -10
            text_y = 220
        else:
            text_x = 150
            text_y = 220

        # m문자 위치
        text_x2 = 60
        text_y2 = 22

        # km텍스트 추가
        if not len(text) == 3:
            draw.text((text_x, text_y), text, font=font, fill=text_color)
        else:
            # 예시 숫자 '145'
            digit100 = int(text[0])  # 1
            digit10 = int(text[1])  # 4
            digit1 = int(text[2])  # 5
            draw.text((10, text_y), str(digit100), font=font, fill=text_color)  # 100의자리
            draw.text((72, text_y), str(digit10), font=font, fill=text_color)  # 10의자리
            draw.text((152, text_y), str(digit1), font=font, fill=text_color)  # 1의자리
        # 이미지에 텍스트 추가
        draw.text((text_x2, text_y2), text2, font=font2, fill=text_color)
        # 이미지 저장
        if not filename.endswith('.png'):
            filename += '.png'
        final_dir = work_directory + filename
        img.save(final_dir)