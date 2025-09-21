import os
import sys


# moduule 경로 자동 추가
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULES_DIR = os.path.join(os.path.dirname(BASE_DIR), 'modules')
CAD_DIR = os.path.join(os.path.dirname(BASE_DIR), 'AutoCAD')
parserdir = os.path.join(os.path.dirname(BASE_DIR), 'BVEParser')
CIVIL3D_DIR = os.path.join(os.path.dirname(BASE_DIR), 'CIVIL3D')
for path in [MODULES_DIR, CAD_DIR, parserdir, CIVIL3D_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

from gui.main_window import MainApp
if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
