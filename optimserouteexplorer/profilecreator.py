import numpy as np
import math
import random

class ProfileCreator:
    def __init__(self, gl):
        self.profile = None
        self.fls = []
        self.gl = gl
        self.els = []

    def generate_longitudinal(self, num_points=100, min_distance=600, chain=40):
        self.generate_random_profile(num_points, min_distance, chain)
        self.check_and_adjust_elevation()
        self.generate_station_elv()


    def generate_station_elv(self):
        """
        계획고 지점(points) 사이를 spline 지반고를 따라 샘플링하여 선형 보간
        Args:
            fl: 계획고 주요지점 (예: [[0,110],[500,120],...])
            gl: 지반고 (예: [[0,100],[100,102],[200,103],...])
        Returns:
            station_elv: [[station, elevation], ...]
        """
        fl_stations = [s for s, _ in self.profile]
        fl_elevations = [e for _, e in self.profile]

        station_elv = []
        for sta, elev in self.gl:

            current_fl = np.interp(sta, fl_stations, fl_elevations)
            station_elv.append([sta, current_fl])

        self.els = station_elv

    def generate_random_profile(self, num_points, min_distance,chain=40):
        """
        spline 기반 경로에서도 사용 가능하도록
        station 값이 정확히 일치하지 않아도 선형보간으로 지반고를 추정합니다.
        """
        # gl을 분리
        gl_stations = [s for s, _ in self.gl]
        gl_elevations = [e for _, e in self.gl]

        # 초기 설정
        start_station, start_elevation = self.gl[0]
        end_station, end_elevation = self.gl[-1]
        points = [[start_station, start_elevation + 10]]

        current_station = start_station
        current_elevation = start_elevation + 10

        for i in range(num_points - 1):


            distance_to_next = chain * math.ceil(random.uniform(min_distance, min_distance * 2) / chain)

            if current_station + distance_to_next >= end_station:
                break

            next_station = current_station + distance_to_next

            # 🔹 지반고를 선형보간으로 추정
            next_elevation = np.interp(next_station, gl_stations, gl_elevations) + 10

            current_station = next_station
            current_elevation = next_elevation
            points.append([current_station, current_elevation])

        points.append([end_station, end_elevation + 10])
        self.profile = points

    def check_and_adjust_elevation(self):
        adjusted_profile = []
        for i, (station, elevation) in enumerate(self.profile):
            rand_el = random.uniform(0, 20)

            if i > 0:
                prev_station, prev_elevation = adjusted_profile[-1]
                if abs(elevation - prev_elevation) > 20:
                    elevation = prev_elevation + (rand_el if elevation > prev_elevation else -rand_el)
            adjusted_profile.append([station, elevation])

        self.profile = adjusted_profile