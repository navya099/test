from dataset.dataset_manager import load_dataset
from gui.dataset_gui import DataSetEditor
import tkinter as tk


def main():
    root = tk.Tk()
    root.withdraw()  # 루트 창 숨기기 (Toplevel만 띄우고 싶을 때)
    db = DataSetEditor(load_dataset(150, False))
    db.mainloop()    # 이벤트 루프 실행

if __name__ == '__main__':
    main()
