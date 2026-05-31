import tkinter as tk
from tkinter import messagebox
import re

def normalize_path(path: str) -> str:
    """
    경로 문자열을 정리:
    - 끝의 불필요한 특수문자(; , 공백 등) 제거
    - 확장자는 항상 .csv로 통일
    - 대소문자 무시 (소문자로 변환)
    - 슬래시 방향 통일 (\ → /)
    """
    # 끝의 ; , 공백 제거
    normalized = re.sub(r"[;,\s]+$", "", path.strip())

    # 확장자 통일 (.csv)
    if normalized.lower().endswith('.csv'):
        normalized = normalized[:normalized.lower().rfind('.csv')] + '.csv'

    # 슬래시 방향 통일 및 소문자 변환
    normalized = normalized.replace("\\", "/").lower()

    return normalized


def define_syntax_list():
    syntax_list = ['Rail', 'FormL', 'FormR', 'FormcL', 'FormcR', 'roofL',
                   'roofcR', 'roofcL', 'roofR', 'dikeL', 'dikeR', 'WallL',
                   'WallR', 'freeobj', 'pole']
    
    return syntax_list

def parse_rail_data(lines):
    rail_data = {}
    syntax_list = define_syntax_list()

    syntax_pattern = "|".join(syntax_list)
    pattern = rf"(\.({syntax_pattern})\((\d+)\))\s+([^\s,;]+)"

    # pole 구문을 위한 별도의 패턴
    pole_pattern = r"\.pole\((\d+);(\d+)\)\s+([^\s,;]+)"

    for line in lines:
        # 일반 구문 처리
        match = re.match(pattern, line, re.IGNORECASE)
        if match:
            full_tag, tag_type, index, path = match.groups()
            index = int(index)
            normalized_path = normalize_path(path)  # 경로 정리
            rail_data[(tag_type.lower(), index)] = (full_tag, normalized_path)

        # pole 구문 처리
        pole_match = re.match(pole_pattern, line, re.IGNORECASE)
        if pole_match:
            # 두 개의 인덱스와 경로를 구분해서 처리
            try:
                index1, index2, path = pole_match.groups()
                index = (int(index1), int(index2))  # 두 개의 인덱스를 튜플로 저장
                normalized_path = normalize_path(path)  # 경로 정리
                rail_data[('pole', index)] = (f".pole({index1};{index2})", normalized_path)
            except ValueError:
                print(f"Warning: 잘못된 pole 구문 발견: {line}")
                continue

    return rail_data

def find_matching_entry(base_lines, new_lines, input_tag, input_index):
    base_data = parse_rail_data(base_lines)
    new_data = parse_rail_data(new_lines)

    # input_index가 튜플일 수 있으므로 처리하는 방식이 달라짐
    input_key = (input_tag.lower(), input_index) if isinstance(input_index, int) else (input_tag.lower(), tuple(input_index))

    if input_key not in base_data:
        return f"⚠ 입력한 `{input_tag}({input_index})`은(는) 베이스 파일에 없음."

    base_path = base_data[input_key][1]  # 베이스 파일에서 찾은 경로
    print("DEBUG base_path:", base_path)
    for (tag, idx), (_, path) in new_data.items():
        print("DEBUG new_path:", normalize_path(path))

    # 새 파일에서 같은 경로를 가진 태그 찾기
    matches = [(tag, idx) for (tag, idx), (_, path) in new_data.items() if normalize_path(path) == base_path]

    if not matches:
        return f"🔍 경로 `{base_path}`에 해당하는 새로운 파일의 항목을 찾을 수 없음."

    # 찾은 결과 반환
    result = "\n".join([f".{tag}({idx}) {base_path}" for tag, idx in matches])
    return f"✅ 일치하는 새 파일의 항목:\n{result}"

# 파일 경로 설정
syntax_list = define_syntax_list()



def select_base_file(entry):
    from tkinter import filedialog
    file_path = filedialog.askopenfilename(title="파일 선택")
    if file_path:
        entry.delete(0, tk.END)
        entry.insert(0, file_path)

class MainAPP(tk.Tk):
    def __init__(self):
        super().__init__()
        # GUI 구성
        self.title("경로 찾기")

        # 베이스파일 경로
        base_label = tk.Label(self, text="베이스파일 경로:")
        base_label.pack(padx=10, pady=5)

        base_frame = tk.Frame(self)
        base_frame.pack(padx=10, pady=5)

        self.base_entry = tk.Entry(base_frame, width=50)
        self.base_entry.pack(side=tk.LEFT, padx=5)

        base_button = tk.Button(base_frame, text="선택", command= lambda: select_base_file(self.base_entry))
        base_button.pack(side=tk.LEFT)

        # new 파일 경로
        new_file_label = tk.Label(self, text="new 파일 경로:")
        new_file_label.pack(padx=10, pady=5)

        new_frame = tk.Frame(self)
        new_frame.pack(padx=10, pady=5)

        self.new_file_entry = tk.Entry(new_frame, width=50)
        self.new_file_entry.pack(side=tk.LEFT, padx=5)

        new_frame_button = tk.Button(new_frame, text="선택", command=lambda: select_base_file(self.new_file_entry))
        new_frame_button.pack(side=tk.LEFT)

        # freeobj 파일 경로
        freeobj_label = tk.Label(self, text="freeobj 파일 경로:")
        freeobj_label.pack(padx=10, pady=5)

        freeobj_frame = tk.Frame(self)
        freeobj_frame.pack(padx=10, pady=5)

        self.freeobj_entry = tk.Entry(freeobj_frame, width=50)
        self.freeobj_entry.pack(side=tk.LEFT, padx=5)

        freeobj_button = tk.Button(freeobj_frame, text="선택", command=lambda: select_base_file(self.freeobj_entry))
        freeobj_button.pack(side=tk.LEFT)


        # SYSTAX 입력
        tag_label = tk.Label(self, text="SYSTAX (대소문자 무관):")
        tag_label.pack(padx=10, pady=5)

        self.tag_entry = tk.Entry(self, width=30)
        self.tag_entry.pack(padx=10, pady=5)

        # 인덱스 입력
        index_label = tk.Label(self, text="인덱스:")
        index_label.pack(padx=10, pady=5)

        self.index_entry = tk.Entry(self, width=30)
        self.index_entry.pack(padx=10, pady=5)

        # 검색 버튼
        search_button = tk.Button(self, text="검색", command=self.search_entry)
        search_button.pack(pady=10)

        # 결과 표시
        result_label = tk.Label(self, text="결과:")
        result_label.pack(padx=10, pady=5)

        self.result_text = tk.Text(self, height=10, width=50)
        self.result_text.pack(padx=10, pady=5)

    def search_entry(self):
        input_tag = self.tag_entry.get().strip()
        input_index = self.index_entry.get().strip()

        # 파일 경로 가져오기
        base_file = self.base_entry.get().strip()
        new_file = self.new_file_entry.get().strip()
        freeobj_file = self.freeobj_entry.get().strip()

        if not base_file or not new_file or not freeobj_file:
            messagebox.showerror("입력 오류", "세 개의 파일 경로를 모두 선택해주세요.")
            return

        # 파일 읽기
        try:
            with open(base_file, "r", encoding="utf-8") as f1, \
                    open(new_file, "r", encoding="utf-8") as f2, \
                    open(freeobj_file, "r", encoding="utf-8") as f3:
                base_lines = f1.read().splitlines()
                new_lines = f2.read().splitlines()
                freeobj_lines = f3.read().splitlines()
        except Exception as e:
            messagebox.showerror("파일 오류", f"파일을 읽을 수 없습니다: {e}")
            return

        if not input_tag or not input_index:
            messagebox.showerror("입력 오류", "구문과 인덱스를 정확히 입력해주세요.")
            return

        # pole 구문 처리
        if input_tag.lower() == 'pole':
            if ';' in input_index:
                input_index = tuple(map(int, input_index.split(';')))
            else:
                messagebox.showerror("입력 오류", "'pole' 구문은 두 개의 인덱스를 입력해야 합니다. 예: 1;0")
                return
        else:
            if not input_index.isdigit():
                messagebox.showerror("입력 오류", "인덱스는 숫자만 가능합니다.")
                return
            input_index = int(input_index)

        if input_tag.lower() not in [s.lower() for s in syntax_list]:
            messagebox.showerror("입력 오류", "올바른 구문을 입력하세요.")
            return

        if input_tag == 'freeobj':
            result = find_matching_entry(base_lines, freeobj_lines, input_tag, input_index)
        else:
            result = find_matching_entry(base_lines, new_lines, input_tag, input_index)

        self.result_text.delete(1.0, tk.END)  # 기존 결과 지우기
        self.result_text.insert(tk.END, result)  # 새 결과 삽입

if __name__ == '__main__':
    app = MainAPP()
    app.mainloop()
