"""ttk 테마."""
import tkinter as tk
from tkinter import ttk


def setup_style(root: tk.Tk):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        style.theme_use("default")
    base = ("Malgun Gothic", 10)
    bold = ("Malgun Gothic", 10, "bold")
    title = ("Malgun Gothic", 12, "bold")
    root.option_add("*Font", base)
    style.configure("TFrame", background="#f5f6f8")
    style.configure("Card.TFrame", background="#ffffff")
    style.configure("TLabel", background="#f5f6f8", font=base)
    style.configure("Card.TLabel", background="#ffffff", font=base)
    style.configure("Unit.TLabel", background="#ffffff",
                    foreground="#888888", font=("Malgun Gothic", 9))
    style.configure("Title.TLabel", background="#f5f6f8", font=title,
                    foreground="#1a1a1a")
    style.configure("Info.TLabel", background="#f5f6f8",
                    foreground="#555555", font=("Malgun Gothic", 9))
    style.configure("Spec.TLabel", background="#eaf1ff", font=bold,
                    foreground="#1a3a70", padding=6)
    style.configure("TLabelframe", background="#f5f6f8",
                    bordercolor="#d0d4da", relief="solid")
    style.configure("TLabelframe.Label", background="#f5f6f8",
                    font=bold, foreground="#333333")
    style.configure("TScale", background="#ffffff", troughcolor="#e0e4ea")
    style.configure("TEntry", fieldbackground="#ffffff", padding=4)
    style.configure("TButton", padding=(10, 6), font=base)
    style.configure("Accent.TButton", font=bold, foreground="white",
                    background="#2f6fed")
    style.map("Accent.TButton",
              background=[("active", "#1e5ad6"), ("disabled", "#a9bce8")])
    style.configure("Link.TButton", font=bold, foreground="white",
                    background="#2b8a3e")
    style.map("Link.TButton",
              background=[("active", "#226c31"), ("disabled", "#a9d0b3")])
    style.configure("Danger.TButton", foreground="#b00020")
    style.configure("Treeview", rowheight=26, font=base)
    style.configure("Treeview.Heading", font=bold)
    style.configure("TNotebook", background="#f5f6f8", borderwidth=0)
    style.configure("TNotebook.Tab", padding=(14, 8), font=base)
    style.map("TNotebook.Tab",
              background=[("selected", "#ffffff"), ("!selected", "#e6e9ee")])
    style.configure("TCheckbutton", background="#f5f6f8", font=base)