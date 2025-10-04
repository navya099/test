import fitz  # PyMuPDF
from PIL import Image
import io
from tkinter import filedialog, ttk

def extract_images_from_pdf(pdf_path, output_folder):
    # PDF 파일 열기
    pdf_document = fitz.open(pdf_path)

    # PDF 페이지를 순회
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        image_list = page.get_images(full=True)
        
        # 페이지의 모든 이미지를 순회
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image = Image.open(io.BytesIO(image_bytes))

            # 이미지 저장
            image_save_path = f"{output_folder}/page_{page_num + 1}_image_{img_index + 1}.{image_ext}"
            image.save(image_save_path, format=image_ext.upper())
            print(f"Saved image to {image_save_path}")

# 예제 사용법
pdf_path = filedialog.askopenfilename()
output_folder = "output_images"

# 폴더가 존재하지 않으면 생성
import os
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

extract_images_from_pdf(pdf_path, output_folder)
