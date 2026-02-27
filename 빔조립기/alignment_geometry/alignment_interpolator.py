class RailInterpolator:
    @staticmethod
    def get_point_at_station(sta_target, rails):
        """
        rails: [Rail, Rail, ...] (각 Rail은 station, coord.x, coord.y, coord.z 속성 보유)
        sta_target: 현재 section의 station 값
        """
        # 정확히 일치하는 station이 있으면 그대로 반환
        for r in rails:
            if r.station == sta_target:
                return r.rail_x, r.rail_y

        # 없으면 인접 station 사이에서 보간
        for i in range(len(rails) - 1):
            r1, r2 = rails[i], rails[i+1]
            if r1.station <= sta_target <= r2.station:
                t = (sta_target - r1.station) / (r2.station - r1.station)
                x = r1.rail_x + t * (r2.rail_x - r1.rail_x)
                y = r1.rail_y + t * (r2.rail_y - r1.rail_y)
                return x, y
        return None