import csv
import logging

logger = logging.getLogger(__name__)

def read_alignment_file() -> list[list[str]]:
    """파일 선택 및 읽기 (UTF-8 → EUC-KR 폴백)"""
    from tkinter import filedialog

    file_path = filedialog.askopenfilename(
        defaultextension=".txt",
        filetypes=[("txt files", "*.txt"), ("All files", "*.*")],
    )
    if not file_path:
        return []
    logger.info("선택 파일: %s", file_path)

    for encoding in ("utf-8", "euc-kr"):
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return list(csv.reader(f))
        except UnicodeDecodeError:
            logger.warning("%s 인코딩 실패, 다음 시도...", encoding)
    logger.error("파일을 읽을 수 없습니다: %s", file_path)
    return []


def parse_ip_lines(lines: list[list[str]]) -> list[list[float]]:
    """IP 데이터 파싱 (예외 처리 강화)"""
    alignment = []
    for line in lines:
        try:
            ip_y = float(line[0])
            ip_x = float(line[1])
            radius = float(line[2]) if len(line) > 2 else 0.0
        except (IndexError, ValueError) as e:
            logger.warning("IP 파싱 실패 (line=%s): %s", line, e)
            continue
        alignment.append([ip_x, ip_y, radius])
    return alignment