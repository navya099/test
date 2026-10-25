from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import fitz  # PyMuPDF
import ezdxf
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

def define_scale_factor(paprer_size: str):
    if paprer_size == 'A0':
        scale_multiplier = 1 * 0.352778
    elif paprer_size == 'A1':
        scale_multiplier = 1 * 0.352778
    elif paprer_size == 'A2':
        scale_multiplier = 1 * 0.352778
    elif paprer_size == 'A3':
        scale_multiplier = 1 * 0.352778
    elif paprer_size == 'A4':
        scale_multiplier = 1 * 0.352778
    else:
        scale_multiplier = 1 * 0.352778
    return scale_multiplier


def prescan_pdf_layouts(pdf_path):
  """전체 페이지 스캔 및 누적 X 오프셋 계산"""
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
  print(
      f"스캔 완료: 총 {len(layouts)}페이지 (혼합 규격 오프셋 계산 완료)"
  )
  return layouts

def pdf_page_to_dxf(pdf_path: str, layout_info: dict, output_dir: Path, skipmode=False) -> bool:


    page_num = layout_info["page_num"]
    output_path = output_dir / f"page_{page_num+1:04d}.dxf"

    if output_path.exists and skipmode:
        return True

    doc = fitz.open(pdf_path)
    page = doc[page_num]
    scale = layout_info["scale"]
    doc_dxf = ezdxf.new(dxfversion="AC1032")
    msp = doc_dxf.modelspace()

    line_count = 0
    for path in page.get_drawings():
        for item in path.get("items", []):
            cmd = item[0]
            if cmd == 'l':
                p1, p2 = item[1], item[2]
                x1, y1 = p1.x * scale , p1.y * scale
                x2, y2 = p2.x * scale , p2.y * scale
                msp.add_line((y2, x2), (y1, x1))
                line_count += 1

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
                line_count += 1

    doc_dxf.saveas(output_path)
    doc.close()

    return False


def batch_convert_pdf(pdf_path: str, output_dir_str: str, end_page: int = 8, start_page: int=0, skipmode=False):
  output_dir = Path(output_dir_str, )
  output_dir.mkdir(parents=True, exist_ok=True)

  layouts = prescan_pdf_layouts(pdf_path)
  run_layouts = layouts[start_page:end_page]
  total_pages = len(run_layouts)

  print(f"총 {total_pages}페이지 대용량 안심 변환 작업 시작)...")

  completed = 0
  skipped = 0
  for layout in run_layouts:
    page_idx = layout["page_num"]
    try:
      print(f"페이지{page_idx} 추출중...")
      was_skipped = pdf_page_to_dxf(
          pdf_path, layout, output_dir, skipmode
      )
      if was_skipped:
        skipped += 1
      else:
        completed += 1

      if (page_idx + 1) % 20 == 0 or (page_idx + 1) == total_pages:
        print(
            f"진행 상황: {page_idx + 1}/{total_pages} 페이지 완료 [용지 규격:"
            f" {layout['type']}] (신규: {completed}, 스킵: {skipped})"
        )
    except Exception as e:
      print(
          f"[오류 발생] 페이지 {page_idx + 1} ({layout['type']}) 변환 중 예외 발생:"
          f" {e} -> 건너뜁니다."
      )

  print("모든 변환 작업이 완벽하게 완료되었습니다.")


if __name__ == "__main__":
  pdf_file = "C:/Temp/09. 실시설계도면.pdf"
  out_folder = "C:/Temp/dxf_output"
  batch_convert_pdf(pdf_file, output_dir_str=out_folder, start_page=19, end_page=36, skipmode=False)