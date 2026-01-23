import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext

def show_long_message(master, text):
    win = tk.Toplevel(master)
    win.title("BVE 코드")
    win.geometry("600x400")

    st = scrolledtext.ScrolledText(win, wrap="word")
    st.insert("1.0", text)
    st.config(state="disabled")
    st.pack(fill="both", expand=True)

    def copy_to_clipboard():
        master.clipboard_clear()
        master.clipboard_append(text)
        master.update()

    ttk.Button(win, text="복사하기", command=copy_to_clipboard).pack(side="left", padx=5, pady=5)
    ttk.Button(win, text="닫기", command=win.destroy).pack(side="right", padx=5, pady=5)