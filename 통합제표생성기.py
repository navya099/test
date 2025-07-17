import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from 곡선표이미지생성기 import *
from 기울기표이미지생성기 import *
from 거리표이미지생성기 import *

class IntegratedApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("통합 데이터 처리기")
        self.geometry("800x600")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 각 탭 생성
        self.curve_tab = CurveTab(self.notebook)
        self.pitch_tab = PitchTab(self.notebook)
        self.km_tab = KmTab(self.notebook)

        self.notebook.add(self.curve_tab, text="곡선 처리")
        self.notebook.add(self.pitch_tab, text="기울기 처리")
        self.notebook.add(self.km_tab, text="거리 처리")


class BaseTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.work_directory = None
        self.target_directory = None

        self.create_widgets()

    def create_widgets(self):
        # 작업 및 대상 디렉토리 선택
        dir_frame = ttk.Frame(self)
        dir_frame.pack(fill=tk.X, pady=5)

        ttk.Button(dir_frame, text="작업 디렉토리 선택", command=self.select_work_directory).pack(side=tk.LEFT, padx=5)
        ttk.Button(dir_frame, text="대상 디렉토리 선택", command=self.select_target_directory).pack(side=tk.LEFT, padx=5)

        # 로그 박스
        self.log_box = tk.Text(self, height=20, font=("Consolas", 10))
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 실행 버튼
        self.run_button = ttk.Button(self, text="작업 실행", command=self.run_task)
        self.run_button.pack(pady=10)

    def log(self, msg):
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)

    def select_work_directory(self):
        path = filedialog.askdirectory(title="작업 디렉토리 선택")
        if path:
            self.work_directory = path
            self.log(f"작업 디렉토리 선택됨: {path}")

    def select_target_directory(self):
        path = filedialog.askdirectory(title="대상 디렉토리 선택")
        if path:
            self.target_directory = path
            self.log(f"대상 디렉토리 선택됨: {path}")

    def run_task(self):
        raise NotImplementedError("서브클래스에서 구현하세요.")


# 곡선 처리 탭
class CurveTab(BaseTab):
    def run_task(self):
        self.log("곡선 처리 작업 시작")
        try:
            # 작업 디렉토리 기본 설정
            if not self.work_directory:
                self.work_directory = 'c:/temp/curve/'
                if not os.path.exists(self.work_directory):
                    os.makedirs(self.work_directory)
                self.log(f"작업 디렉토리 기본값 사용: {self.work_directory}")

            if not self.target_directory:
                messagebox.showwarning("경고", "대상 디렉토리를 선택하세요.")
                return


            data = read_file()  # 이미 구현된 함수
            if not data:
                self.log("파일이 없습니다.")
                return

            structure_list = load_structure_data()

            file_paths, structure_comment = process_curve_data(self.work_directory, data, structure_list)
            result_list = parse_and_match_data(self.work_directory, file_paths)

            if result_list:
                create_curve_post_txt(result_list, structure_comment)

            cleanup_files(file_paths)
            copy_all_files(self.work_directory, self.target_directory, ['.csv', '.png', '.txt'], ['.dxf', '.ai'])

            self.log("곡선 처리 완료!")
            messagebox.showinfo("완료", "곡선 처리 작업이 완료되었습니다.")
        except Exception as e:
            self.log(f"오류: {e}")
            messagebox.showerror("오류", f"오류가 발생했습니다:\n{e}")


# 기울기 처리 탭
class PitchTab(BaseTab):
    def run_task(self):
        self.log("기울기 처리 작업 시작")
        try:
            if not self.work_directory:
                self.work_directory = 'c:/temp/pitch/'
                if not os.path.exists(self.work_directory):
                    os.makedirs(self.work_directory)
                self.log(f"작업 디렉토리 기본값 사용: {self.work_directory}")

            if not self.target_directory:
                messagebox.showwarning("경고", "대상 디렉토리를 선택하세요.")
                return

            data = read_file()
            if not data:
                self.log("파일이 없습니다.")
                return

            # Civil3D 여부 묻기
            is_civil3d = messagebox.askyesno("질문", "pitch_info가 Civil3D인가요?")

            structure_list = load_structure_data()

            if is_civil3d:
                sections = process_sections_civil3d(data)
                image_names, structure_comment = civil3d_profile(sections, structure_list)
                output_file = os.path.join(self.work_directory, '주석처리된파일.txt')
                create_outfile(output_file, sections)

                with open(output_file, 'r', encoding='utf-8') as f:
                    reader1 = csv.reader(f)
                    lines1 = list(reader1)

                obj_data = os.path.join(self.work_directory, 'pitch_index.txt')
                with open(obj_data, 'r', encoding='utf-8') as f:
                    reader2 = csv.reader(f)
                    lines2 = list(reader2)

                sections_2_f = os.path.join(self.work_directory, 'sections_2_f.txt')
                sections_2 = parse_sections_civil3d(lines1)
                sections_2 = remove_first_entry_dictionary(sections_2)

                with open(sections_2_f, 'w', encoding='utf-8') as f:
                    f.write(str(sections_2))

                tag_mapping = parse_object_index(lines2)

                result_list = search_STA_value(sections_2, tag_mapping)
                if result_list:
                    create_curve_post_txt(result_list, structure_comment)

                self.log("Civil3D 처리 완료")
            else:
                file_paths, annotated_sections = process_and_save_sections(self.work_directory, data)
                GRADE_LIST, VIP_STA_LIST, L_LIST, VCL_LIST = process_sections_VIP(annotated_sections)
                image_names, structure_comment = bve_profile(annotated_sections, GRADE_LIST, VIP_STA_LIST, L_LIST,
                                                             VCL_LIST, structure_list)
                result_list = parse_and_match_data(self.work_directory, file_paths)
                create_curve_post_txt(result_list, structure_comment)
                cleanup_files(file_paths)
                self.log("BVE 처리 완료")

            copy_all_files(self.work_directory, self.target_directory, ['.csv', '.png', '.txt'], ['.dxf', '.ai'])

            self.log("기울기 처리 완료!")
            messagebox.showinfo("완료", "기울기 처리 작업이 완료되었습니다.")

        except Exception as e:
            self.log(f"오류: {e}")
            messagebox.showerror("오류", f"오류가 발생했습니다:\n{e}")


# 거리 처리 탭
class KmTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)
        self.structure_excel_path = None
        # 엑셀 파일 선택 버튼 추가
        btn_excel = ttk.Button(self, text="구조물 엑셀 파일 선택", command=self.select_excel_file)
        btn_excel.pack(pady=5)

    def select_excel_file(self):
        filetypes = [("Excel files", "*.xls *.xlsx"), ("All files", "*.*")]
        path = filedialog.askopenfilename(title="구조물 엑셀 파일 선택", filetypes=filetypes)
        if path:
            self.structure_excel_path = path
            self.log(f"선택된 엑셀 파일: {path}")

    def run_task(self):
        self.log("거리 처리 작업 시작")
        try:
            if not self.work_directory:
                self.work_directory = 'c:/temp/km/'
                if not os.path.exists(self.work_directory):
                    os.makedirs(self.work_directory)
                self.log(f"작업 디렉토리 기본값 사용: {self.work_directory}")

            if not self.structure_excel_path:
                messagebox.showwarning("경고", "구조물 정보 엑셀 파일을 선택해주세요.")
                return

            data = read_file()
            if not data:
                self.log("데이터가 비어 있습니다.")
                return

            last_block = find_last_block(data)
            self.log(f"마지막 측점 = {last_block}")

            structure_list = find_structure_section(self.structure_excel_path)
            if structure_list:
                self.log("구조물 정보가 성공적으로 로드되었습니다.")
            else:
                self.log("구조물 정보가 없습니다.")

            index_datas, post_datas = create_km_object(last_block, structure_list)

            index_file = os.path.join(self.work_directory, 'km_index.txt')
            post_file = os.path.join(self.work_directory, 'km_post.txt')

            create_txt(index_file, index_datas)
            create_txt(post_file, post_datas)

            self.log("txt 작성이 완료됐습니다.")
            self.log("모든 작업이 완료됐습니다.")
            messagebox.showinfo("완료", "거리 처리 작업이 완료되었습니다.")

        except Exception as e:
            self.log(f"오류: {e}")
            messagebox.showerror("오류", f"작업 중 오류가 발생했습니다:\n{e}")


if __name__ == "__main__":
    app = IntegratedApp()
    app.mainloop()
