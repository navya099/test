from model.model import BVERouteData, Curve, Pitch, Station

class BVERouteFactory:
    @staticmethod
    def from_current_route(current_route: list) -> BVERouteData:
        curves = []
        pitchs = []
        stations_list = []

        trackpositions, radiuss, pitch_values, station_names, coords, directions = current_route

        # Curve & Pitch 생성
        for idx, trackpos in enumerate(trackpositions):
            curves.append(Curve(trackpos, radiuss[idx], 0))
            pitchs.append(Pitch(trackpos, pitch_values[idx]))

        # Station 생성
        for pos, name in enumerate(station_names):
            stations_list.append(Station(pos, name))

        # BVERouteData 생성
        data = BVERouteData('a', curves=curves, pitchs=pitchs, stations=stations_list,coords=coords)
        return data
