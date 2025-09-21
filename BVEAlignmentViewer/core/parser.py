# BVEParser 루트 경로를 sys.path에 추가
import sys
from tkinter import messagebox


from RouteLoader import RouteLoader


class CSVRouteParser:
    """
       BVEParser를 래핑하는 클래스.

       Attributes:
           current_route (CurrentRoute): openbve CurrentRoute객체
       """
    def __init__(self):
        self.current_route = None

    def parse_route(self, filename: str):
        """
        BVEParser를 래핑하여 파싱하는 메소드
        Attributes:
            filename(str): 루트 전체경로
        """

        #BVE 객체 초기화
        loader = RouteLoader(filename)
        result = loader.load()
        self.current_route = loader.current_route
        messagebox.showinfo("실행 결과", f'파싱 {result[0]}')

    def extract_currentroute(self):
        """
        CurrentRoute를 파싱하여 데이터를 추출하는 메소드
        Returns:
        list: 다음 5개 리스트로 구성된 리스트
            - trackpositions (list[float]): 측점
            - radiuss (list[float]): 곡선 반경 (m 단위, 직선은 0)
            - pitchs (list[float]): 종단 구배 값 (0.001)
            - stations (list[float, str]): 정거장 정보(측점, 이름)
            - coords (list[Vector3]): 좌표
            - directions (list[Vector3]): 3d방향각
        """
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

        #초기표고
        firstelevation = self.current_route.Atmosphere.InitialElevation
        return [trackpositions, radiuss, pitchs, stations, coords, directions, firstelevation]



