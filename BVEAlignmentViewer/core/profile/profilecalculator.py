class ProfileCalculator:
    @staticmethod
    def calculate_elevation(station1: float, slope1: float,
                            station2: float, slope2: float, start_elevation: float=0.0) -> tuple[float, float]:
        """
        두 점과 진출 구배를 이용하여 시작/끝 표고 계산
        Args:
            station1 (float): 시작 측점
            slope1 (float): station1 진출 구배
            station2 (float): 끝 측점
            slope2 (float): station2 진출 구배
            start_elevation (float): 시작 표고
        Returns:
            tuple[float, float]: (start_elevation, end_elevation)
        """
        distance = station2 - station1
        if distance == 0:
            return 0.0, 0.0
        # 구간 평균 구배로 끝점 표고 계산
        end_elevation = start_elevation + slope1 * distance

        return start_elevation, end_elevation
