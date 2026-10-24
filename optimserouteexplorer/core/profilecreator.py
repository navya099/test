# core/profilecreator.py
import numpy as np


class ProfileCreator:
    def __init__(self, gl, *, min_cover: float = 5.0, max_grade: float = 0.035):
        if not gl or len(gl) < 2:
            raise ValueError("gl requires at least 2 points")
        self.gl = gl
        self.min_cover = min_cover
        self.max_grade = max_grade
        self.profile = None
        self.els = []
        self.constraints_ok = True
        self.min_cover_violation = 0.0

    def generate_longitudinal(self, num_points=100, min_distance=600, chain=40) -> bool:
        self.generate_random_profile(num_points, min_distance, chain)
        self.constraints_ok = self.check_and_adjust_elevation()
        self.generate_station_elv()
        self.min_cover_violation = self._compute_min_cover_violation()
        return self.constraints_ok

    def generate_random_profile(self, num_points, min_distance, chain=40):
        gl_stations = np.array([s for s, _ in self.gl], dtype=float)
        gl_elevations = np.array([e for _, e in self.gl], dtype=float)
        start_station = float(gl_stations[0])
        end_station = float(gl_stations[-1])
        total_length = end_station - start_station
        if total_length <= 0:
            self.profile = [[start_station, float(gl_elevations[0]) + self.min_cover]]
            return
        n_intervals = max(1, min(num_points - 1, int(total_length // min_distance)))
        interval = total_length / n_intervals
        vip_stations = [start_station + k * interval for k in range(n_intervals + 1)]
        smoothed = self._smooth(gl_elevations, window=3)
        smoothed = np.maximum(smoothed, gl_elevations)   # 상향만
        vip_elevations = np.interp(vip_stations, gl_stations, smoothed) + self.min_cover
        self.profile = [[float(s), float(e)] for s, e in zip(vip_stations, vip_elevations)]

    def check_and_adjust_elevation(self) -> bool:
        if not self.profile or len(self.profile) < 2:
            return True
        gl_stations = np.array([s for s, _ in self.gl], dtype=float)
        gl_elevs = np.array([e for _, e in self.gl], dtype=float)
        tol = 1e-6
        # 1) min_cover 가능한 한
        for i in range(len(self.profile)):
            s, e = self.profile[i]
            ground = float(np.interp(s, gl_stations, gl_elevs))
            self.profile[i][1] = max(e, ground + self.min_cover)
        # 2) 경사 클램프 (경계 여유)
        self._clamp_grade()
        # 3) 경사만 검증
        return self._grade_satisfied(tol)

    def _clamp_grade(self):
        adjusted = [list(self.profile[0])]
        for i in range(1, len(self.profile)):
            s_prev, e_prev = adjusted[-1]
            s_cur, e_cur = self.profile[i]
            ds = s_cur - s_prev
            if ds <= 0:
                adjusted.append([s_cur, e_prev])
                continue
            max_dh = self.max_grade * ds * (1.0 - 1e-6)   # 경계 여유
            dh = e_cur - e_prev
            if dh > max_dh:
                e_cur = e_prev + max_dh
            elif dh < -max_dh:
                e_cur = e_prev - max_dh
            adjusted.append([s_cur, e_cur])
        self.profile = adjusted

    def _grade_satisfied(self, tol: float = 1e-6) -> bool:
        for i in range(1, len(self.profile)):
            s0, h0 = self.profile[i - 1]
            s1, h1 = self.profile[i]
            ds = s1 - s0
            if ds > 0 and abs((h1 - h0) / ds) > self.max_grade + tol:
                return False
        return True

    def _compute_min_cover_violation(self) -> float:
        if not self.profile:
            return 0.0
        gl_stations = np.array([s for s, _ in self.gl], dtype=float)
        gl_elevs = np.array([e for _, e in self.gl], dtype=float)
        total = 0.0
        for s, e in self.profile:
            ground = float(np.interp(s, gl_stations, gl_elevs))
            total += max(0.0, ground + self.min_cover - e)
        return float(total)

    def generate_station_elv(self):
        fl_stations = [s for s, _ in self.profile]
        fl_elevations = [e for _, e in self.profile]
        self.els = [
            float(np.interp(sta, fl_stations, fl_elevations))
            for sta, _ in self.gl
        ]

    @property
    def slopes(self) -> list[float]:
        if not self.profile or len(self.profile) < 2:
            return []
        slopes = []
        for i in range(1, len(self.profile)):
            s0, h0 = self.profile[i - 1]
            s1, h1 = self.profile[i]
            ds = s1 - s0
            slopes.append((h1 - h0) / ds if ds != 0 else 0.0)
        return slopes

    @staticmethod
    def _smooth(arr: np.ndarray, window: int = 3) -> np.ndarray:
        if len(arr) < window or window < 2:
            return arr
        kernel = np.ones(window) / window
        smoothed = np.convolve(arr, kernel, mode="same")
        half = window // 2
        smoothed[:half] = arr[:half]
        smoothed[-half:] = arr[-half:]
        return smoothed