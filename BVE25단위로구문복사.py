import tkinter as tk
from tkinter import ttk, messagebox
import pyperclip


class BVECommandGenerator:
    @staticmethod
    def create_rail(track_position, rail_index, x_offset, y_offset, railobj_index):
        return f'{track_position},.rail {rail_index};{x_offset};{y_offset};{railobj_index};'

    @staticmethod
    def create_curve(track_position, radius, cant):
        return f'{track_position},.curve {radius};{cant};'

    @staticmethod
    def create_freeobject(track_position, rail_index, free_object_index, x_offset=0.0, y_offset=0.0, yaw=0, pitch=0, roll=0):
        return f'{track_position},.Freeobj {rail_index};{free_object_index};{x_offset};{y_offset};{yaw};{pitch};{roll};'


class BVEGuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BVE 구문 생성기")

        self.command_var = tk.StringVar(value="rail")

        # 기본 입력
        self.start_entry = self._labeled_entry("시작 측점:", 0)
        self.end_entry = self._labeled_entry("끝 측점:", 1)
        self.interval_entry = self._labeled_entry("간격:", 2)

        # 구문 종류 선택
        ttk.Label(root, text="구문 종류:").grid(row=3, column=0, sticky='e')
        self.command_option = ttk.Combobox(root, textvariable=self.command_var, values=["rail", "freeobj", "curve"])
        self.command_option.grid(row=3, column=1, sticky='we')
        self.command_option.bind("<<ComboboxSelected>>", self.update_fields)

        # 동적 옵션 입력 영역
        self.option_frame = ttk.Frame(root)
        self.option_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky='we')

        # 결과 출력 텍스트박스
        self.output_text = tk.Text(root, height=10)
        self.output_text.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky='we')

        # 버튼
        ttk.Button(root, text="생성 및 복사", command=self.generate).grid(row=6, column=0, columnspan=2, pady=10)

        self.update_fields()

    def _labeled_entry(self, label, row):
        ttk.Label(self.root, text=label).grid(row=row, column=0, sticky='e')
        entry = ttk.Entry(self.root)
        entry.grid(row=row, column=1, sticky='we')
        return entry

    def update_fields(self, event=None):
        for widget in self.option_frame.winfo_children():
            widget.destroy()

        self.inputs = {}

        cmd = self.command_var.get()
        match cmd:
            case "rail":
                self._add_input("rail_index")
                self._add_input("x_offset")
                self._add_input("y_offset")
                self._add_input("object_index")
            case "freeobj":
                self._add_input("rail_index")
                self._add_input("object_index")
                self._add_input("x_offset")
                self._add_input("y_offset")
                self._add_input("yaw")
                self._add_input("pitch")
                self._add_input("roll")
            case "curve":
                self._add_input("radius")
                self._add_input("cant")

    def _add_input(self, name):
        ttk.Label(self.option_frame, text=f"{name}:").pack(anchor='w')
        entry = ttk.Entry(self.option_frame)
        entry.pack(fill='x')
        self.inputs[name] = entry

    def generate(self):
        try:
            start = int(self.start_entry.get())
            end = int(self.end_entry.get())
            interval = int(self.interval_entry.get())
            cmd = self.command_var.get()

            values = {k: float(v.get()) if '.' in v.get() else int(v.get()) for k, v in self.inputs.items()}
            lines = []

            for pos in range(start, end, interval):
                match cmd:
                    case "rail":
                        line = BVECommandGenerator.create_rail(
                            pos,
                            values["rail_index"],
                            values["x_offset"],
                            values["y_offset"],
                            values["object_index"]
                        )
                    case "freeobj":
                        line = BVECommandGenerator.create_freeobject(
                            pos,
                            values["rail_index"],
                            values["object_index"],
                            values["x_offset"],
                            values["y_offset"],
                            values["yaw"],
                            values["pitch"],
                            values["roll"]
                        )
                    case "curve":
                        line = BVECommandGenerator.create_curve(
                            pos,
                            values["radius"],
                            values["cant"]
                        )
                    case _:
                        line = ""
                lines.append(line)

            result = "\n".join(lines)
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, result)
            pyperclip.copy(result)
            messagebox.showinfo("완료", "구문이 생성되어 클립보드에 복사되었습니다.")

        except Exception as e:
            messagebox.showerror("오류", f"입력값 확인 필요:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("400x600")
    app = BVEGuiApp(root)
    root.mainloop()
