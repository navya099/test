import meshio


class SlopeBuilder:
    def __init__(self, mesh):
        self.mesh = mesh

    def add_slope(self, track_edges, dem: SrtmDEM30, slope_ratio, side="left"):
        slope_side = []
        n = len(track_edges)

        for i in range(n):
            x, y, z = track_edges[i]

            # 1. 해당 지점의 법선 벡터(Normal Vector) 계산
            # 현재 점과 다음 점(또는 이전 점)을 이용하여 진행 방향의 수직 벡터를 구함
            if i < n - 1:
                dx = track_edges[i + 1][0] - x
                dy = track_edges[i + 1][1] - y
            else:
                dx = x - track_edges[i - 1][0]
                dy = y - track_edges[i - 1][1]

            length = np.sqrt(dx ** 2 + dy ** 2)
            nx, ny = (-dy / length, dx / length) if side == "left" else (dy / length, -dx / length)

            # 2. 성토/절토 판정 (선로 바로 옆 지면 높이 확인)
            long, lat = convert_coordinates([x + nx * 0.1, y + ny * 0.1], 5186, 4326)
            dem_z = dem.get_elevation(long, lat) + 100  # 보정치 포함
            is_cut = z < dem_z  # 선로가 지면보다 낮으면 절토

            # 3. 이진 탐색으로 Daylight Point(교점) 찾기
            low = 0.0
            high = 500.0  # 최대 탐색 거리
            intersect_pos = [x, y, z]

            for _ in range(15):  # 15회 반복으로 정밀도 확보
                mid = (low + high) / 2
                curr_x = x + nx * mid
                curr_y = y + ny * mid

                # 사면의 높이 계산
                # 절토(is_cut): 위로 올라감(+), 성토: 아래로 내려감(-)
                slope_z = z + (mid / slope_ratio) if is_cut else z - (mid / slope_ratio)

                # 해당 지점의 실제 지면 높이
                l, a = convert_coordinates([curr_x, curr_y], 5186, 4326)
                curr_dem_z = dem.get_elevation(l, a) + 100

                if is_cut:
                    if slope_z < curr_dem_z:
                        low = mid
                    else:
                        high = mid
                else:
                    if slope_z > curr_dem_z:
                        low = mid
                    else:
                        high = mid

            # 탐색 완료된 최종 좌표 저장
            final_dist = (low + high) / 2
            fx, fy = x + nx * final_dist, y + ny * final_dist
            fl, fa = convert_coordinates([fx, fy], 5186, 4326)
            fz = dem.get_elevation(fl, fa) + 100
            slope_side.append((fx, fy, fz))

        # 4. 메쉬 생성 (기존 로직 유지)
        vertices = np.array(track_edges + slope_side)
        faces = []
        for i in range(n - 1):
            ti, ti_next = i, i + 1
            si, si_next = i + n, i + 1 + n
            faces.append([ti, si, ti_next])
            faces.append([si, si_next, ti_next])

        return meshio.Mesh(points=vertices, cells=[("triangle", np.array(faces))])

