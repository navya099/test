"""BVE 곡선 파일 기반 곡선레일(5m) 설치 구문 생성기.

입력: BVE에서 추출한 CURVE_INFO.TXT, 구조물 측점 XLSX
출력: FREEOBJ 구문 파일, RAILTYPE 구문 파일
"""
from bve.bve_curve_ui import FreeobjApp

if __name__ == "__main__":
    FreeobjApp().mainloop()