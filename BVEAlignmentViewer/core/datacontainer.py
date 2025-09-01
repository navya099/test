from model.model import BVERouteData, Curve, Pitch, Station

class BVERouteFactory:
    """
    extract_currentroute리스트를 BVERouteData객체로 변환하는 팩토리 클래스
    """
    @staticmethod
    def from_current_route(extracted_currentroute: list) -> BVERouteData:
        """
        extract_currentroute 리스트로부터 BVERouteData 객체를 생성.

        Args:
            extracted_currentroute (list): extract_currentroute 메소드에서 반환된 6개 리스트
                - trackpositions (list[float])
                - radiuss (list[float])
                - pitch_values (list[float])
                - station_names (list[str])
                - coords (list[Vector3])
                - directions (list[Vector3])

        Returns:
            BVERouteData: 변환된 BVERouteData 객체
        """
        #리스트 초기화
        curves = []
        pitchs = []
        stations_list = []

        #리스트 언팩
        trackpositions, radiuss, pitch_values, station_names, coords, directions = extracted_currentroute

        # Curve & Pitch 생성
        for idx, trackpos in enumerate(trackpositions):
            curves.append(Curve(trackpos, radiuss[idx], 0))
            pitchs.append(Pitch(trackpos, pitch_values[idx]))

        # Station 생성
        for pos, name in enumerate(station_names):
            stations_list.append(Station(pos, name))

        # BVERouteData 생성
        data = BVERouteData(
            name='a',
            curves=curves,
            pitchs=pitchs,
            stations=stations_list,
            coords=coords,
            directions=directions
            )
        return data
