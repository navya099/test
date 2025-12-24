# moduule 경로 자동 추가
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULES_DIR = os.path.join(os.path.dirname(BASE_DIR), 'modules')
CAD_DIR = os.path.join(os.path.dirname(BASE_DIR), 'AutoCAD')
parserdir = os.path.join(os.path.dirname(BASE_DIR), 'BVEParser')
CIVIL3D_DIR = os.path.join(os.path.dirname(BASE_DIR), 'CIVIL3D')
RAILWAYS_DIR = os.path.join(os.path.dirname(BASE_DIR), 'RAILWAYS')
for path in [MODULES_DIR, CAD_DIR, parserdir, CIVIL3D_DIR, RAILWAYS_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)