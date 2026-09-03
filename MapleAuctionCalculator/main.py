# main.py

import tkinter as tk

from gui.main_window import MainWindow
from models.charactermanager import CharacterManager


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