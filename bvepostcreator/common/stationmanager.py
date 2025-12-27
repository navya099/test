class StationManager:
    """측점 관리 클래스"""
    @staticmethod
    def to_reverse_station(forward_end, reverse_start, station):
        """
        정방향 측점을 역방향 측점으로 변환
        전제: 정/역 노선 길이가 동일함
        """
        return reverse_start + forward_end - station

    @staticmethod
    def apply_brokenchain(origin_station, brokenchain):
        """측점에 파정 적용"""
        return origin_station + brokenchain

    @staticmethod
    def get_origin_station(station , brokenchain):
        """파정 적용된 측점으로부터 원래 측점 얻기"""
        return station - brokenchain

    @staticmethod
    def is_within(start: float, end: float, station: float) -> bool:
        """station이 start~end 구간 안에 있는지 확인"""
        return start <= station <= end

    @staticmethod
    def distance(station1: float, station2: float) -> float:
        """두 측점 사이 거리"""
        return abs(station2 - station1)

    @staticmethod
    def reverse_with_brokenchain(forward_end: float, reverse_start: float, station: float, brokenchain: float) -> float:
        """정방향 측점을 역방향 파정 측점으로 변환"""
        return StationManager.apply_brokenchain(
            StationManager.to_reverse_station(forward_end, reverse_start, station),
            brokenchain
        )

    @staticmethod
    def format_distance(number: float, display_type: str = "+") -> str:
        """
        거리/측점을 포맷 (예: 1234.56 → 1+234.56)

        Args:
            number: 거리 값 (m 단위)
            display_type: km와 m 사이 구분자, 기본 '+'
        """
        negative = number < 0
        number = abs(number)

        km = int(number // 1000)
        m = number % 1000

        formatted_distance = f"{km}{display_type}{m:06.2f}"
        if negative:
            formatted_distance = "-" + formatted_distance

        return formatted_distance

