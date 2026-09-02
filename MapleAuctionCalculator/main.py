# main.py

import tkinter as tk

from models import CharacterManager
from gui.main_window import MainWindow


def main():

    manager = CharacterManager()

    root = tk.Tk()

    MainWindow(
        root,
        manager
    )

    root.mainloop()


if __name__ == "__main__":
    main()