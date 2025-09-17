from tkinter import messagebox
from controller.controller_base import AppController
from core.alignment.alginmentcalculator import AlignmentCalculator
from core.alignment.alignmentbuilder import AlignmentBuilder
from core.processor import RouteProcessor
from core.profile.profilebuilder import ProfileBuilder


class EventHandler:
    """
    이벤트 관리 클래스.

    Attributes:
        some_option_var (None): 설정 옵션 변경용 변수 할당
        main_app (tk.Tk) TK 메인 인스턴스
        app_controller (AppController): 메인 APP 컨트롤러
        file_controller(FileController): 파일 열기/저장 및 경로 관리를 담당하는 컨트롤러
        settings_controller (SettingsController): 설정 호출용 클래스
    """
    def __init__(self, main_app, app_controller: AppController, file_controller, settings_controller):
        self.some_option_var = None
        self.main_app = main_app
        self.app_controller = app_controller
        self.file_controller = file_controller
        self.settings_controller = settings_controller

    def on_file_open(self):
        """
        파일 열기 이벤트 처리.
        1. 파일 선택 및 로드
        2. CurrentRoute 추출 후 BVERouteData 변환
        3. 라스트블럭 기준으로 리스트 자르기
        4. 중복 반경/구배 제거
        5. 좌표 정리
        6. Calculator 초기화 및 IPData 빌드
        """
        #파일 열기
        self.file_controller.open_file()
        #파일 경로 할당
        filepath = self.file_controller.filepath

        if filepath:
            self._process_and_plot(filepath)

    def _process_and_plot(self, filepath):
        extracted_list = self.app_controller.load_route(filepath)  # ✅ 공식 인터페이스 호출
        if extracted_list:
            self.app_controller.convert_to_bveroute(extracted_list)
            # bvedata로 변환
            bve_data = self.app_controller.bvedata
            # 전처리
            routeprocessor = RouteProcessor(bve_data)  # 인스턴스 생성
            routeprocessor.run()
            # 선형객체 빌드
            alignments = AlignmentBuilder.build_ipdata_from_sections(bve_data)
            # 정거장 정보 계산
            calculator = AlignmentCalculator()
            calculator.calculate_stationinfo(bve_data)

            #종단 객체 빌드
            profile = ProfileBuilder.build_profile(bve_data)
            # 선형객체 저장
            self.app_controller.alignments = alignments
            # PlotFrame에 데이터 설정
            self.main_app.plot_frame.set_data(alignments, bve_data)

    def on_file_save(self):
        self.file_controller.save_file()
        filename = self.file_controller.savefilepath
        if filename:
            # dxf 인스턴스 생성
            self.app_controller.export_dxf(filename)
            messagebox.showinfo("도면 저장", f"dxf 저장 성공 {filename}")

    def on_open_settings(self):
        messagebox.showinfo("설정 기능", f"설정 저장 기능")