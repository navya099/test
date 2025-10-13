import numpy as np
from optimserouteexplorer.util import haversine

class Evaluate:
    def __init__(self):
        self.cost = 0.0
        self.score = 0.0

    def evaluate_longitudinal(self, coords, elevs, ground):

        dz = np.array(elevs) - np.array(ground)

        ds = np.array([haversine(coords[i], coords[i+1]) for i in range(len(coords)-1)])
        slope = np.abs(dz[:-1]/(ds + 1e-9))
        mean_slope = np.mean(slope)

        bridges, tunnels = {}, {}
        start_idx = 0
        while start_idx < len(dz)-1:
            current_sign = np.sign(dz[start_idx])
            end_idx = start_idx
            while end_idx < len(dz)-1 and np.sign(dz[end_idx]) == current_sign:
                end_idx += 1
            segment_len = ds[start_idx:end_idx].sum()
            segment_height = np.max(np.abs(dz[start_idx:end_idx]))
            if current_sign > 0 and segment_height >= 15 and segment_len >= 100:
                bridges[start_idx] = (start_idx, end_idx)
            elif current_sign < 0 and segment_height >= 15 and segment_len >= 100:
                tunnels[start_idx] = (start_idx, end_idx)
            start_idx = end_idx

        # 각 구간 길이 합산
        total_bridge_length = sum([sum(ds[s:e]) for s, e in bridges.values()])
        total_tunnel_length = sum([sum(ds[s:e]) for s, e in tunnels.values()])

        cutfill_cost = np.sum(np.abs(dz)*20.0)
        self.cost = route_length(coords) + 200*mean_slope + 500*total_tunnel_length + 300*total_bridge_length + 0.01*cutfill_cost

        return bridges, tunnels, slope