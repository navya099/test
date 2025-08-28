# BVEParser 루트 경로를 sys.path에 추가
import os
import sys
from tkinter import messagebox

from traits.trait_types import false

from OpenBveApi.System.BaseOptions import BaseOptions
from Plugins.RouteCsvRw.Plugin import Plugin
from Plugins.RouteCsvRw.RouteData import RouteData
from RouteManager2.CurrentRoute import CurrentRoute


class CSVRouteParser:
    #openbve parser를 감싸는 래퍼클래스
    def __init__(self):
        self.current_route = None

    def parse_route(self, filename: str) -> RouteData:
        from Plugins.RouteCsvRw.CsvRwRouteParser import Parser
        self.current_route = CurrentRoute()
        plugin = Plugin()
        Plugin.CurrentHost = None
        Plugin.FileSystem = None
        Plugin.CurrentOptions = BaseOptions()
        # ✅ 루트 로드 (백그라운드에서 실행)
        result = plugin.LoadRoute(
            filename,
            'utf-8',
            '',
            '',
            '',
            True,
            self.current_route)

        messagebox.showinfo("실행 결과", f'파싱 {result}')
    def extract_route(self, filename: str) -> RouteData:
        pass