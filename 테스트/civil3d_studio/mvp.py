import tkinter as tk
import math



MAX_DISTANCE = 99999

class AlignmentTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Civil 3D 선형 실시간 Station / Offset 시뮬레이터")

        # 캔버스 생성
        self.canvas = tk.Canvas(root, width=900, height=600, bg="#1e1e1e")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 1. 가상의 선형(Alignment) 정점 데이터 (X, Y 좌표)
        # 직선과 꺾인 구간, 곡선 근사 구간을 포함한 샘플 선형
        self.raw_points = [
            (100, 450), (250, 450), (350, 420), (430, 360),
            (480, 280), (500, 180), (620, 130), (780, 150)
        ]

        # 2. 선형 세그먼트 사전 캐싱 (C3D 최적화 원리 적용)
        # 마우스 이동 시 매번 길이를 다시 계산하지 않도록 시작/끝 측점을 미리 계산해 둠
        self.segments = self._build_alignment_cache(self.raw_points, start_station=0.0)

        # 선형 그리기
        self._draw_alignment()

        # 3. 마우스 이동 이벤트 바인딩 (C3D의 Editor.PointMonitor 역할)
        self.canvas.bind("<Motion>", self.on_mouse_move)

        # 안내 문구
        self.canvas.create_text(
            20, 20, anchor="nw", fill="#aaaaaa", font=("맑은 고딕", 10),
            text="마우스 커서를 선형 근처로 움직여보세요. (실시간 수직 투영 및 Station/Offset 계산)"
        )

    def _build_alignment_cache(self, pts, start_station=0.0):
        """선형의 각 선분(Segment) 정보와 누적 측점(Station)을 메모리에 사전 캐싱"""
        segments = []
        current_sta = start_station

        for i in range(len(pts) - 1):
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            dx = x2 - x1
            dy = y2 - y1
            length = math.hypot(dx, dy)

            if length == 0:
                continue

            segments.append({
                "x1": x1, "y1": y1,
                "x2": x2, "y2": y2,
                "dx": dx, "dy": dy,
                "len_sq": dx * dx + dy * dy,
                "length": length,
                "start_sta": current_sta,
                "end_sta": current_sta + length
            })
            current_sta += length

        return segments

    def _draw_alignment(self):
        """캔버스에 선형 중심선과 주요 정점(PI/측점) 표시"""
        # 중심선 그리기
        flat_coords = [coord for pt in self.raw_points for coord in pt]
        self.canvas.create_line(*flat_coords, fill="#00d2ff", width=3, tags="alignment")

        # 시작점 및 주요 정점 표시
        for idx, seg in enumerate(self.segments):
            x, y = seg["x1"], seg["y1"]
            self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill="#ffcc00", outline="")
            sta_text = self.format_station(seg["start_sta"])
            self.canvas.create_text(x, y + 15, text=sta_text, fill="#888888", font=("Consolas", 9))

        # 마지막 끝점 표시
        last = self.segments[-1]
        self.canvas.create_oval(last["x2"] - 4, last["y2"] - 4, last["x2"] + 4, last["y2"] + 4, fill="#ffcc00",
                                outline="")
        self.canvas.create_text(last["x2"], last["y2"] + 15, text=self.format_station(last["end_sta"]), fill="#888888",
                                font=("Consolas", 9))

    def calculate_station_offset(self, px, py):
        """
        C3D Alignment.StationOffset()의 핵심 수학 원리:
        모든 선분에 수직 투영(벡터 내적)을 수행하여 가장 가까운 투영점과 좌/우 부호(외적)를 산출
        """
        min_dist = float("inf")
        best_result = None

        for seg in self.segments:
            # 벡터 AP (선분 시작점 -> 마우스 커서)
            apx = px - seg["x1"]
            apy = py - seg["y1"]

            # 벡터 내적(Dot Product)을 이용한 투영 비율 t 계산 (0.0 <= t <= 1.0 이면 선분 내부에 수선의 발 존재)
            t = (apx * seg["dx"] + apy * seg["dy"]) / seg["len_sq"]

            # 선분 범위를 벗어난 경우 예외 처리 (C3D의 PointNotOnEntityException과 동일 원리)
            if t < 0.0 or t > 1.0:
                continue

            # 수선의 발(투영점 Q) 좌표
            qx = seg["x1"] + t * seg["dx"]
            qy = seg["y1"] + t * seg["dy"]

            # 커서와 투영점 사이의 거리 (Offset 크기)
            dist = math.hypot(px - qx, py - qy)

            if dist < min_dist:
                min_dist = dist
                station = seg["start_sta"] + t * seg["length"]

                # 2D 외적(Cross Product)으로 진행 방향 기준 좌/우 판별
                # (화면 좌표계는 Y가 아래로 증가하므로 일반 수학 좌표계와 부호 방향 주의)
                cross = seg["dx"] * (py - qy) - seg["dy"] * (px - qx)
                signed_offset = dist if cross >= 0 else -dist

                best_result = (station, signed_offset, qx, qy)

        return best_result

    @staticmethod
    def format_station(sta):
        """측점 숫자를 토목 표준 표기(예: 125.40 -> 0+125.40)로 변환"""
        km = int(sta // 1000)
        m = sta % 1000
        return f"{km}+{m:06.2f}"

    def on_mouse_move(self, event):
        """마우스가 움직일 때마다 실행되는 실시간 렌더링 루프"""
        # 이전 프레임의 임시 그래픽(수직선, 툴팁) 삭제 (C3D TransientManager 역할)
        self.canvas.delete("tracker")

        px, py = event.x, event.y
        result = self.calculate_station_offset(px, py)

        # 유효 투영 범위 밖이거나 선형에서 너무 멀리 떨어진 경우 표시 안 함
        if result is None or abs(result[1]) > MAX_DISTANCE:  # 오타 수정: result[0]->역산거리 등 확인, 기존 코드 유지하려면 abs(result[1]) 혹은 result
            pass  # 기존 조건식 유지 가능하나 아래 로직 집중

        if result is None:
            return

        station, offset, qx, qy = result
        if abs(offset) > MAX_DISTANCE:
            return

        # 1. 커서에서 선형 중심선까지 수직 보조선(점선) 그리기
        self.canvas.create_line(
            px, py, qx, qy, fill="#ff5555", dash=(4, 4), width=1.5, tags="tracker"
        )
        # 선형 위 투영점 강조 표시
        self.canvas.create_oval(
            qx - 4, qy - 4, qx + 4, qy + 4, fill="#ff5555", outline="#ffffff", tags="tracker"
        )

        # 2. 툴팁 텍스트 구성
        side = "우측(R)" if offset >= 0 else "좌측(L)"
        sta_str = self.format_station(station)
        tooltip_text = f"STA: {sta_str}\nOFF: {side} {abs(offset):.2f}m"

        # 3. 마우스 커서 옆 반투명 스타일 툴팁 박스 렌더링
        tx, ty = px + 16, py + 16
        # 화면 우측/하단 경계 이탈 방지
        if tx > 740: tx = px - 150
        if ty > 530: ty = py - 60

        text_id = self.canvas.create_text(
            tx + 8, ty + 6, anchor="nw", text=tooltip_text,
            fill="#ffffff", font=("Consolas", 10, "bold"), tags="tracker"
        )

        # [수정된 부분] bbox 튜플 요소를 각각 분해하여 사각형 좌표 계산
        bbox = self.canvas.bbox(text_id)
        if bbox:
            x1, y1, x2, y2 = bbox
            rect_id = self.canvas.create_rectangle(
                x1 - 6, y1 - 4, x2 + 6, y2 + 4,
                fill="#2b2b2b", outline="#00d2ff", width=1, tags="tracker"
            )
            self.canvas.tag_raise(text_id, rect_id)


if __name__ == "__main__":
    root = tk.Tk()
    app = AlignmentTrackerApp(root)
    root.mainloop()
