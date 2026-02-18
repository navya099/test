import tkinter as tk
from tkinter import ttk
import json

class DataSetEditor(tk.Toplevel):
    def __init__(self, dataset):
        super().__init__()
        self.title("데이터셋 편집")
        self.dataset = dataset

        self.tkdataset = self.init_tkdataset(self.dataset)
        self.add_ui()

    def make_var(self, value):
        if isinstance(value, int):
            return tk.IntVar(value=value)
        elif isinstance(value, float):
            return tk.DoubleVar(value=value)
        elif isinstance(value, (list, dict)):
            # 리스트/딕셔너리는 문자열로 표시
            return tk.StringVar(value=json.dumps(value, ensure_ascii=False))
        else:
            return tk.StringVar(value=str(value))

    def init_tkdataset(self, data):
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                result[key] = self.init_tkdataset(value)
            return result
        elif isinstance(data, list):
            result = []
            for v in data:
                result.append(self.init_tkdataset(v))
            return result
        else:
            return self.make_var(data)


    def add_ui(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # 주요 옵션 탭
        self.add_infotab()
        self.add_poledatatab()
        self.add_brackettab()
        self.add_feederdatatab()

        # Treeview 탭
        self.add_tree_tab()
        #버튼
        # 버튼 영역
        button_frame = tk.Frame(self)
        button_frame.pack(side="bottom", fill="x")
        tk.Button(button_frame, text="적용", command=self.update_dataset).pack(side="left")

    def add_infotab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text='노선 정보')

        row = 0
        ttk.Label(frame, text="설계속도:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.tkdataset['design_speed'] = tk.IntVar(value=self.dataset['design_speed'])
        ttk.Entry(frame, textvariable=self.tkdataset['design_speed']).grid(row=row, column=1)

        row += 1
        ttk.Label(frame, text="전차선로 시스템 타입명:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.tkdataset['prefix'] = tk.StringVar(value=self.dataset['prefix'])
        ttk.Entry(frame, textvariable=self.tkdataset['prefix']).grid(row=row, column=1)

    def add_poledatatab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text='전주 설정')

        # mast_data
        self.add_struct_tab(frame, "구조물별 전주 인덱스 설정", "mast_data", tk.DoubleVar)

        # pole_gauge
        self.add_struct_tab(frame, "구조물별 건식게이지 설정", "pole_gauge", tk.DoubleVar)

    def add_feederdatatab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text='급전선 설정')

        # mast_data
        self.add_struct_tab(frame, "구조물별 급전선 인덱스 설정", "feeder_insulator_idx", tk.IntVar)


    def add_struct_tab(self, frame, title, dataset_key, var_type=tk.DoubleVar):
        """
        공통 구조물별 입력 탭 생성 함수
        frame: 부모 프레임
        title: 라벨프레임 제목
        dataset_key: self.dataset / self.tkdataset에서 사용할 키
        var_type: tk.Variable 타입 (기본은 DoubleVar)
        """
        lf = ttk.LabelFrame(frame, text=title)
        lf.pack(fill="x", padx=5, pady=5)

        structures = ["토공", "교량", "터널"]
        row = 0
        for struct in structures:
            ttk.Label(lf, text=f"{struct}:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
            self.tkdataset[dataset_key][struct] = var_type(value=self.dataset[dataset_key][struct])
            ttk.Entry(lf, textvariable=self.tkdataset[dataset_key][struct]).grid(row=row, column=1)
            row += 1

    def add_brackettab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text='브래킷 설정')

        lf = ttk.LabelFrame(frame, text="구조물별 브래킷 인덱스 설정")
        lf.pack(fill="x", padx=5, pady=5)

        # 구조물 목록
        structures = ["토공", "교량", "터널"]

        for struct in structures:
            lfe = ttk.LabelFrame(lf, text=f"{struct}")
            lfe.pack(fill="x", padx=5, pady=5)

            row = 0
            # 직선
            ttk.Label(lfe, text="직선:").grid(row=row, column=1, padx=5, pady=5, sticky="w")
            for i in range(len(self.dataset['pole_data'][struct]['직선'])):
                self.tkdataset['pole_data'][struct]['직선'][i] = tk.IntVar(
                    value=self.dataset['pole_data'][struct]['직선'][i]
                )
                ttk.Entry(lfe, textvariable=self.tkdataset['pole_data'][struct]['직선'][i]).grid(row=row, column=2 + i)

            # 곡선
            row += 1
            ttk.Label(lfe, text="곡선:").grid(row=row, column=1, padx=5, pady=5, sticky="w")
            for i in range(len(self.dataset['pole_data'][struct]['곡선'])):
                self.tkdataset['pole_data'][struct]['곡선'][i] = tk.IntVar(
                    value=self.dataset['pole_data'][struct]['곡선'][i]
                )
                ttk.Entry(lfe, textvariable=self.tkdataset['pole_data'][struct]['곡선'][i]).grid(row=row, column=2 + i)

    def add_tree_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text='데이터 구조')

        self.tree = ttk.Treeview(frame, columns=("values"), show="tree headings")
        self.tree.heading("#0", text="Key")
        self.tree.heading("values", text="Value")
        self.tree.pack(fill="both", expand=True)

        self.populate_tree("", self.dataset)

        # 편집 영역
        edit_frame = ttk.Frame(frame)
        edit_frame.pack(fill="x", pady=10)
        ttk.Label(edit_frame, text="값 수정:").pack(side="left")
        self.edit_var = tk.StringVar()
        edit_entry = ttk.Entry(edit_frame, textvariable=self.edit_var)
        edit_entry.pack(side="left", padx=5)
        ttk.Button(edit_frame, text="저장", command=self.save_edit).pack(side="left")

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def populate_tree(self, parent, data):
        if isinstance(data, dict):
            for key, value in data.items():
                node_id = self.tree.insert(parent, "end", text=key)
                self.populate_tree(node_id, value)
        elif isinstance(data, list):
            for i, value in enumerate(data):
                node_id = self.tree.insert(parent, "end", text=f"[{i}]", values=str(value))
                self.populate_tree(node_id, value)
        else:
            self.tree.insert(parent, "end", text="값", values=str(data))

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected, "values")
        if values:
            self.edit_var.set(values[0])
        else:
            self.edit_var.set("")

    def save_edit(self):
        selected = self.tree.selection()
        if not selected:
            return
        new_value = self.edit_var.get()
        self.tree.set(selected, "values", new_value)

        # 선택된 노드의 경로 추적
        path = []
        node = selected[0]
        while node:
            path.insert(0, self.tree.item(node, "text"))
            node = self.tree.parent(node)

        # dataset 갱신
        target = self.dataset
        tk_target = self.tkdataset
        for p in path[:-1]:
            if p.startswith("["):
                idx = int(p.strip("[]"))
                target = target[idx]
                tk_target = tk_target[idx]
            else:
                target = target[p]
                tk_target = tk_target[p]

        last_key = path[-1]
        if last_key.startswith("["):
            idx = int(last_key.strip("[]"))
            target[idx] = eval(new_value)
            tk_target[idx].set(eval(new_value))
        else:
            target[last_key] = eval(new_value)
            tk_target[last_key].set(eval(new_value))

    def update_dataset(self, tkdata=None, data=None):
        if tkdata is None and data is None:
            tkdata, data = self.tkdataset, self.dataset

        for key, value in tkdata.items():
            if isinstance(value, dict):
                self.update_dataset(value, data[key])
            else:
                raw = value.get()
                try:
                    data[key] = json.loads(raw)
                except Exception:
                    try:
                        data[key] = float(raw) if "." in raw else int(raw)
                    except Exception:
                        data[key] = raw

        # Treeview 갱신
        self.tree.delete(*self.tree.get_children())
        self.populate_tree("", self.dataset)