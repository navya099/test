"""
bve 자동 전주 설계ㅐ 프로그램
made by dger

ver 2025.04.09
2차 준공
전주 전차선까지 처리 및 gui프로세스 개선
스레딩 적용
프로젝트 구조변경
"""
from ui.main_gui import MainWindow


def main():
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
