from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from tkinter.filedialog import askdirectory, askopenfilename
from tkinter.messagebox import askquestion
from tkinter.simpledialog import askinteger
import tkinter as tk
from tkinter import messagebox

import ezdxf
import fitz  # PyMuPDF
import numpy as np


def get_page_dimensions_mm(page):
    """PDF 페이지의 실제 크기를 mm 단위로 정확하게 추출"""
    rect = page.rect
    width_mm = rect.width * (25.4 / 72.0)
    height_mm = rect.height * (25.4 / 72.0)
    return width_mm, height_mm


def classify_paper_size(w, h):
    """용지 규격 판별"""
    max_len, min_len = max(w, h), min(w, h)
    if abs(max_len - 841.0) < 10 and abs(min_len - 594.0) < 10:
        return "A1"
    elif abs(max_len - 594.0) < 10 and abs(min_len - 420.0) < 10:
        return "A2"
    elif abs(max_len - 420.0) < 10 and abs(min_len - 297.0) < 10:
        return "A3"
    else:
        return f"Custom ({max_len:.1f}x{min_len:.1f}mm)"


def define_scale_factor(paper_size: str):
    # 포인트(pt) 단위를 실제 mm 단위로 환산하는 배율 적용
    return 25.4 / 72.0


def get_total_page_count(pdf_path):
    doc = fitz.open(pdf_path)
    total_page_count = len(doc)
    doc.close()
    return total_page_count


def prescan_pdf_layouts(pdf_path):
    """전체 페이지 스캔 및 규격 확인"""
    doc = fitz.open(pdf_path)
    layouts = []

    print("PDF 용지 규격 사전 스캔 중...")
    for i, page in enumerate(doc):
        w_mm, h_mm = get_page_dimensions_mm(page)
        paper_type = classify_paper_size(w_mm, h_mm)
        scale_multiplier = define_scale_factor(paper_type)

        layouts.append({
            "page_num": i,
            "width_mm": w_mm,
            "height_mm": h_mm,
            "type": paper_type,
            "scale": scale_multiplier,
        })

    doc.close()
    print(f"스캔 완료: 총 {len(layouts)}페이지 규격 분석 완료")
    return layouts


def pdf_page_to_dxf(
        pdf_path: str, layout_info: dict, output_dir: Path, skipmode=False
) -> bool:
    page_num = layout_info["page_num"]
    output_path = output_dir / f"page_{page_num + 1:04d}.dxf"

    if output_path.exists() and skipmode:
        return True  # 스킵됨

    doc = fitz.open(pdf_path)
    page = doc[page_num]
    scale = layout_info["scale"]
    doc_dxf = ezdxf.new(dxfversion="AC1032")
    msp = doc_dxf.modelspace()

    entity_count = 0

    # 벡터 그래픽(선, 사각형, 솔리드/해치) 추출
    for path in page.get_drawings():
        fill_color = path.get("fill")
        has_fill = fill_color is not None

        path_pts = []  # 솔리드/해치 영역 구성을 위한 점 수집용

        for item in path.get("items", []):
            cmd = item[0]
            if cmd == "l":
                p1, p2 = item[1], item[2]
                x1, y1 = p1.x * scale, p1.y * scale
                x2, y2 = p2.x * scale, p2.y * scale
                msp.add_line((y2, x2), (y1, x1))

                if has_fill:
                    path_pts.append((y1, x1))
                    path_pts.append((y2, x2))
                entity_count += 1

            elif cmd == "re":
                rect = item[1]
                pts = [
                    (rect.y0 * scale, rect.x0 * scale),
                    (rect.y0 * scale, rect.x1 * scale),
                    (rect.y1 * scale, rect.x1 * scale),
                    (rect.y1 * scale, rect.x0 * scale),
                    (rect.y0 * scale, rect.x0 * scale),
                ]
                msp.add_lwpolyline(pts)

                if has_fill:
                    path_pts.extend(pts[:-1])  # 닫힌 루프를 제외한 고유 꼭짓점 추가
                entity_count += 1

        # [추가] 솔리드 및 면 채우기(Fill) 처리
        if has_fill and len(path_pts) >= 3:
            try:
                hatch = msp.add_hatch(color=7)  # 기본 색상 (화이트/블랙)
                hatch.set_solid_fill()
                hatch.paths.add_polyline_path(path_pts, is_closed=True)
                entity_count += 1
            except Exception:
                pass
                  # 예외 발생 시 무시하고 진행

    # 텍스트(Text) 추출 파서
    text_dict = page.get_text("dict")
    for block in text_dict.get("blocks", []):
        if block.get("type") == 0:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text_str = span.get("text", "").strip()
                    if not text_str:
                        continue

                    origin = span.get("origin", (0, 0))
                    ox, oy = origin[0], origin[1]

                    tx = oy * scale
                    ty = ox * scale
                    font_size = span.get("size", 10) * scale

                    dir_vec = span.get("dir", (1, 0))
                    angle_deg = np.degrees(np.arctan2(-dir_vec[1], dir_vec[0]))

                    msp.add_text(
                        text_str,
                        dxfattribs={
                            "height": font_size,
                            "insert": (tx, ty),
                            "rotation": angle_deg,
                        },
                    )
                    entity_count += 1

    doc_dxf.saveas(output_path)
    doc.close()

    return False  # 새로 생성됨


def batch_convert_pdf(
        pdf_path: str,
        output_dir_str: str,
        end_page: int = 8,
        start_page: int = 0,
        skipmode=False,
):
    output_dir = Path(output_dir_str)
    output_dir.mkdir(parents=True, exist_ok=True)

    layouts = prescan_pdf_layouts(pdf_path)
    run_layouts = layouts[start_page:end_page]
    total_pages = len(run_layouts)

    print(f"총 {total_pages}페이지 대용량 안심 변환 작업 시작 (솔리드/해치 포함)...")

    completed = 0
    skipped = 0
    for layout in run_layouts:
        page_idx = layout["page_num"]
        try:
            print(f"페이지 {page_idx + 1} 추출 중...")
            was_skipped = pdf_page_to_dxf(pdf_path, layout, output_dir, skipmode)
            if was_skipped:
                skipped += 1
            else:
                completed += 1

            if (page_idx + 1 - start_page) % 20 == 0 or (page_idx + 1) == end_page:
                print(
                    f"진행 상황: 처리 완료 [용지 규격: {layout['type']}] (신규:"
                    f" {completed}, 스킵: {skipped})"
                )
        except Exception as e:
            print(
                f"[오류 발생] 페이지 {page_idx + 1} ({layout['type']}) 변환 중 예외"
                f" 발생: {e} -> 건너뜁니다."
            )

    print("모든 변환 작업이 완벽하게 완료되었습니다.")


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    pdf_file = askopenfilename(
        title="변환할 PDF 도면 파일 선택",
        filetypes=[("PDF 파일", "*.pdf"), ("모든 파일", "*.*")],
    )
    if not pdf_file:
        print("PDF 파일 선택이 취소되었습니다.")
        exit()

    out_folder = askdirectory(title="DXF 저장 폴더 선택")
    if not out_folder:
        print("저장 폴더 선택이 취소되었습니다.")
        exit()

    total_page = get_total_page_count(pdf_file)

    start_input = askinteger(
        "시작 페이지",
        f"시작할 페이지 번호를 입력하세요 (전체 {total_page}페이지):",
        initialvalue=1,
    )
    if start_input is None:
        print("작업이 취소되었습니다.")
        exit()
    start_page = start_input - 1

    max_page = askinteger(
        "끝 페이지",
        f"변환할 마지막 페이지 번호를 입력하세요 (전체 {total_page}페이지):",
        initialvalue=total_page,
    )
    if max_page is None:
        print("작업이 취소되었습니다.")
        exit()

    skipmode = messagebox.askyesno(
        "스킵 모드 확인",
        "이미 변환된 DXF 파일이 있다면 건너뛸까요? (예: 스킵 / 아니오: 덮어쓰기)",
    )

    print(f"\n[선택된 설정]")
    print(f"- 파일 경로: {pdf_file}")
    print(f"- 저장 폴더: {out_folder}")
    print(f"- 범위: {start_input}페이지 ~ {max_page}페이지")
    print(f"- 기존 파일 스킵 여부: {skipmode}\n")

    batch_convert_pdf(
        pdf_path=pdf_file,
        output_dir_str=out_folder,
        start_page=start_page,
        end_page=max_page,
        skipmode=skipmode,
    )