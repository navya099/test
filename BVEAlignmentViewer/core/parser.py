# BVEParser 루트 경로를 sys.path에 추가
from tkinter import messagebox
from OpenBveApi.System.BaseOptions import BaseOptions
from Plugins.RouteCsvRw.Plugin import Plugin
from RouteManager2.CurrentRoute import CurrentRoute

class CSVRouteParser:
    #openbve parser를 감싸는 래퍼클래스
    def __init__(self):
        self.current_route = None
        self.routedata = None

    def parse_route(self, filename: str):
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

    def extract_currentroute(self):
        trackpositions, radiuss, pitchs, coords, directions = [], [], [], [], []
        stations = []

        # 트랙 요소 (리스트 순회)
        for elem in self.current_route.Tracks[0].Elements:
            trackpositions.append(elem.StartingTrackPosition)
            radiuss.append(elem.CurveRadius)
            pitchs.append(elem.Pitch)
            coords.append(elem.WorldPosition)
            directions.append(elem.WorldDirection)

        # 정거장 요소
        for station in self.current_route.Stations:
            name = station.Name
            position = station.DefaultTrackPosition
            stations.append([position, name])

        return [trackpositions, radiuss, pitchs, stations, coords, directions]



