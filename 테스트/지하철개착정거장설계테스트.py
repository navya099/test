import tkinter as tk
from tkinter import messagebox, ttk
import os
import ezdxf


class StationMVPAppSlope:
    def __init__(self, root):
        self.root = root
        self.root.title("지하철 개착정거장 자동 설계 (종단구배 반영)")
        self.root.geometry("440x820")
        self.root.resizable(False, False)

        pad_opts = {'padx': 10, 'pady': 3}

        # --- [PART 1: 정거장 선형 및 골조 파라미터] ---
        tk.Label(root, text="[ 1. 선형 및 3D 골조 파라미터 ]", font=("Malgun Gothic", 10, "bold"), fg="#1565C0").pack(anchor="w",
                                                                                                             padx=10,
                                                                                                             pady=(
                                                                                                             10, 2))

        tk.Label(root, text="정거장 총 길이 (L, m):", font=("Malgun Gothic", 9)).pack(anchor="w", **pad_opts)
        self.entry_length = tk.Entry(root, font=("Malgun Gothic", 9), width=35)
        self.entry_length.pack(anchor="w", **pad_opts)
        self.entry_length.insert(0, "200")

        tk.Label(root, text="정거장 전체 폭 (W, m) [CL 기준]:", font=("Malgun Gothic", 9)).pack(anchor="w", **pad_opts)
        self.entry_width = tk.Entry(root, font=("Malgun Gothic", 9), width=35)
        self.entry_width.pack(anchor="w", **pad_opts)
        self.entry_width.insert(0, "20")

        tk.Label(root, text="시점(STA. 0+000) 기준선 표고 (Base Level):", font=("Malgun Gothic", 9)).pack(anchor="w",
                                                                                                   **pad_opts)
        self.entry_align_lv = tk.Entry(root, font=("Malgun Gothic", 9), width=35)
        self.entry_align_lv.pack(anchor="w", **pad_opts)
        self.entry_align_lv.insert(0, "134.45")

        tk.Label(root, text="종단구배 (퍼밀, ‰) [예: 상구배 10 = 1%]:", font=("Malgun Gothic", 9, "bold"), fg="#D32F2F").pack(
            anchor="w", **pad_opts)
        self.entry_slope = tk.Entry(root, font=("Malgun Gothic", 9), width=35)
        self.entry_slope.pack(anchor="w", **pad_opts)
        self.entry_slope.insert(0, "10")  # 10‰ (0.01 m/m)

        tk.Label(root, text="선형 기준선 ~ 바닥 상단 오프셋 (m):", font=("Malgun Gothic", 9)).pack(anchor="w", **pad_opts)
        self.entry_offset = tk.Entry(root, font=("Malgun Gothic", 9), width=35)
        self.entry_offset.pack(anchor="w", **pad_opts)
        self.entry_offset.insert(0, "5.0")

        tk.Label(root, text="정거장 총 높이 (내부공간 H, m):", font=("Malgun Gothic", 9)).pack(anchor="w", **pad_opts)
        self.entry_height = tk.Entry(root, font=("Malgun Gothic", 9), width=35)
        self.entry_height.pack(anchor="w", **pad_opts)
        self.entry_height.insert(0, "12")

        tk.Label(root, text="층수 (예: 2):", font=("Malgun Gothic", 9)).pack(anchor="w", **pad_opts)
        self.entry_floors = tk.Entry(root, font=("Malgun Gothic", 9), width=35)
        self.entry_floors.pack(anchor="w", **pad_opts)
        self.entry_floors.insert(0, "2")

        tk.Label(root, text="두께 (외벽 / 바닥 / 슬래브, m):", font=("Malgun Gothic", 9)).pack(anchor="w", **pad_opts)
        t_frame = tk.Frame(root)
        t_frame.pack(anchor="w", **pad_opts)
        self.entry_wall_t = tk.Entry(t_frame, font=("Malgun Gothic", 9), width=10);
        self.entry_wall_t.pack(side="left", padx=2);
        self.entry_wall_t.insert(0, "0.8")
        self.entry_floor_t = tk.Entry(t_frame, font=("Malgun Gothic", 9), width=10);
        self.entry_floor_t.pack(side="left", padx=2);
        self.entry_floor_t.insert(0, "1.0")
        self.entry_slab_t = tk.Entry(t_frame, font=("Malgun Gothic", 9), width=10);
        self.entry_slab_t.pack(side="left", padx=2);
        self.entry_slab_t.insert(0, "0.6")

        btn_3d = tk.Button(root, text="종단구배 반영 3D 개착박스 DXF 생성", font=("Malgun Gothic", 10, "bold"), bg="#3F51B5",
                           fg="white", command=self.on_generate_3d)
        btn_3d.pack(pady=5, fill="x", padx=10)

        ttk.Separator(root, orient="horizontal").pack(fill="x", padx=10, pady=8)

        # --- [PART 2: 단면 추출 옵션] ---
        tk.Label(root, text="[ 2. 단면 추출 및 도면화 (STA) ]", font=("Malgun Gothic", 10, "bold"), fg="#D32F2F").pack(
            anchor="w", padx=10, pady=(2, 2))

        self.section_mode = tk.StringVar(value="range")
        mode_frame = tk.Frame(root)
        mode_frame.pack(anchor="w", padx=10, pady=2)
        tk.Radiobutton(mode_frame, text="범위 측점 추출 (일괄)", variable=self.section_mode, value="range",
                       command=self.toggle_mode).pack(side="left", padx=5)
        tk.Radiobutton(mode_frame, text="단일 측점 추출", variable=self.section_mode, value="single",
                       command=self.toggle_mode).pack(side="left", padx=5)

        self.range_frame = tk.Frame(root)
        self.range_frame.pack(anchor="w", padx=10, pady=2)
        tk.Label(self.range_frame, text="추출 간격 (m):", font=("Malgun Gothic", 9)).grid(row=0, column=0, sticky="w",
                                                                                      padx=2)
        self.entry_interval = tk.Entry(self.range_frame, font=("Malgun Gothic", 9), width=15)
        self.entry_interval.grid(row=0, column=1, padx=2);
        self.entry_interval.insert(0, "50")

        self.single_frame = tk.Frame(root)
        tk.Label(self.single_frame, text="추출할 특정 STA (m):", font=("Malgun Gothic", 9)).grid(row=0, column=0, sticky="w",
                                                                                            padx=2)
        self.entry_single_sta = tk.Entry(self.single_frame, font=("Malgun Gothic", 9), width=15)
        self.entry_single_sta.grid(row=0, column=1, padx=2);
        self.entry_single_sta.insert(0, "100")

        btn_section = tk.Button(root, text="구배 반영 2D 단면도 DXF 일괄 생성", font=("Malgun Gothic", 11, "bold"), bg="#E65100",
                                fg="white", command=self.on_generate_section)
        btn_section.pack(pady=10, fill="x", padx=10)

    def toggle_mode(self):
        if self.section_mode.get() == "range":
            self.single_frame.pack_forget()
            self.range_frame.pack(anchor="w", padx=10, pady=2)
        else:
            self.range_frame.pack_forget()
            self.single_frame.pack(anchor="w", padx=10, pady=2)

    def get_params(self):
        return (
            float(self.entry_length.get()), float(self.entry_width.get()),
            float(self.entry_align_lv.get()), float(self.entry_slope.get()),
            float(self.entry_offset.get()), float(self.entry_height.get()),
            int(self.entry_floors.get()), float(self.entry_wall_t.get()),
            float(self.entry_floor_t.get()), float(self.entry_slab_t.get())
        )

    def calc_align_lv(self, x, base_lv, slope_permil):
        # 종단구배 계산: 10‰ = 0.01 m/m
        return base_lv + (slope_permil / 1000.0) * x

    def on_generate_3d(self):
        try:
            L, W, base_lv, slope_permil, offset, H, num_floors, t_wall, t_floor, t_slab = self.get_params()
            half_w = W / 2.0

            doc = ezdxf.new('R2000')
            msp = doc.modelspace()
            doc.layers.add("ALIGNMENT_CL", color=1)
            doc.layers.add("STRUCT_WALL", color=3)
            doc.layers.add("STRUCT_SLAB", color=5)

            # 1. 종단구배가 적용된 선형 중심선 (CL) 3D 선 작도 (시작점과 끝점 연결)
            start_lv = self.calc_align_lv(0, base_lv, slope_permil)
            end_lv = self.calc_align_lv(L, base_lv, slope_permil)
            msp.add_line((0, 0, start_lv), (L, 0, end_lv), dxfattribs={"layer": "ALIGNMENT_CL"})

            # 2. 경사지형을 부드럽게 표현하기 위해 종방향으로 세그먼트 분할 작도 (예: 5m 간격 세그먼트)
            seg_size = 5.0
            x_curr = 0.0
            while x_curr < L:
                x_next = min(x_curr + seg_size, L)

                # 각 세그먼트 시작/끝에서의 표고 계산
                lv1 = self.calc_align_lv(x_curr, base_lv, slope_permil)
                lv2 = self.calc_align_lv(x_next, base_lv, slope_permil)

                f_top1, f_top2 = lv1 - offset, lv2 - offset
                f_bot1, f_bot2 = f_top1 - t_floor, f_top2 - t_floor
                r_top1, r_top2 = f_top1 + H, f_top2 + H
                r_bot1, r_bot2 = r_top1 - t_slab, r_top2 - t_slab

                # 2-1. 바닥 슬래브 세그먼트
                for f in self.create_sloped_box_faces(x_curr, x_next, -half_w, half_w, f_bot1, f_bot2, f_top1, f_top2):
                    msp.add_3dface(f, dxfattribs={"layer": "STRUCT_SLAB"})

                # 2-2. 천장 슬래브 세그먼트
                for f in self.create_sloped_box_faces(x_curr, x_next, -half_w, half_w, r_bot1, r_bot2, r_top1, r_top2):
                    msp.add_3dface(f, dxfattribs={"layer": "STRUCT_SLAB"})

                # 2-3. 중간 슬래브 세그먼트
                story_height = H / num_floors
                for i in range(1, num_floors):
                    z1 = f_top1 + (i * story_height)
                    z2 = f_top2 + (i * story_height)
                    for f in self.create_sloped_box_faces(x_curr, x_next, -half_w, half_w, z1 - t_slab / 2,
                                                          z2 - t_slab / 2, z1 + t_slab / 2, z2 + t_slab / 2):
                        msp.add_3dface(f, dxfattribs={"layer": "STRUCT_SLAB"})

                # 2-4. 외벽 세그먼트 (좌, 우, 시작, 끝단)
                for f in self.create_sloped_box_faces(x_curr, x_next, -half_w, -half_w + t_wall, f_top1, f_top2, r_bot1,
                                                      r_bot2): msp.add_3dface(f, dxfattribs={"layer": "STRUCT_WALL"})
                for f in self.create_sloped_box_faces(x_curr, x_next, half_w - t_wall, half_w, f_top1, f_top2, r_bot1,
                                                      r_bot2): msp.add_3dface(f, dxfattribs={"layer": "STRUCT_WALL"})

                if x_curr == 0.0:
                    for f in self.create_flat_box_faces(0, t_wall, -half_w, half_w, f_top1, r_bot1): msp.add_3dface(f,
                                                                                                                    dxfattribs={
                                                                                                                        "layer": "STRUCT_WALL"})
                if x_next == L:
                    for f in self.create_flat_box_faces(L - t_wall, L, -half_w, half_w, f_top2, r_bot2): msp.add_3dface(
                        f, dxfattribs={"layer": "STRUCT_WALL"})

                x_curr = x_next

            doc.saveas("station_sloped_3d.dxf")
            messagebox.showinfo("성공", f"종단구배({slope_permil}‰) 반영 3D 개착박스 DXF 생성 완료!")
        except Exception as e:
            messagebox.showerror("오류", f"3D 생성 중 오류 발생:\n{e}")

    def on_generate_section(self):
        try:
            params = self.get_params()
            L = params[0]
            mode = self.section_mode.get()

            stations = []
            if mode == "range":
                interval = float(self.entry_interval.get())
                if interval <= 0: raise ValueError("간격은 0보다 커야 합니다.")
                cur = 0.0
                while cur <= L:
                    stations.append(cur)
                    cur += interval
                if cur - interval < L: stations.append(L)
            else:
                s_val = float(self.entry_single_sta.get())
                if not (0 <= s_val <= L): raise ValueError(f"측점 범위(0 ~ {L}m)를 벗어났습니다.")
                stations.append(s_val)

            output_file = self.generate_2d_section_dxf(stations, params)

            sta_str = ", ".join([f"STA. 0+{int(s):03d}" for s in stations])
            res_msg = (
                f"종단구배 반영 2D 단면도 DXF 추출 완료!\n\n"
                f"- 추출된 측점 수: {len(stations)}개소\n"
                f"- 측점 목록: {sta_str}\n"
                f"- 저장 파일: {os.path.abspath(output_file)}\n\n"
                f"각 측점별 고유 표고(Alignment Level)가 반영된 단면도가 생성되었습니다!"
            )
            messagebox.showinfo("단면 추출 성공", res_msg)

        except Exception as e:
            messagebox.showerror("오류 발생", f"단면 추출 중 오류 발생:\n{e}")

    def generate_2d_section_dxf(self, sta_list, params, filename="station_sloped_sections_2d.dxf"):
        L, W, base_lv, slope_permil, offset, H, num_floors, t_wall, t_floor, t_slab = params

        doc = ezdxf.new('R2000')
        msp = doc.modelspace()

        if "SEC_OUTLINE" not in doc.layers: doc.layers.add("SEC_OUTLINE", color=7)
        if "SEC_CONCRETE" not in doc.layers: doc.layers.add("SEC_CONCRETE", color=4)
        if "SEC_CENTER" not in doc.layers: doc.layers.add("SEC_CENTER", color=1)
        if "SEC_TEXT" not in doc.layers: doc.layers.add("SEC_TEXT", color=2)
        if "SEC_HATCH" not in doc.layers: doc.layers.add("SEC_HATCH", color=8)

        half_w = W / 2.0
        drawing_spacing = W * 2.5

        for idx, sta in enumerate(sta_list):
            x_offset = idx * drawing_spacing
            align_lv = self.calc_align_lv(sta, base_lv, slope_permil)

            floor_top_z = align_lv - offset
            floor_bot_z = floor_top_z - t_floor
            roof_top_z = floor_top_z + H
            roof_bot_z = roof_top_z - t_slab

            # 1. 제목 및 STA 표기
            title_text = f"SECTION STA. 0+{int(sta):03d} (SLOPE {slope_permil}‰)"
            msp.add_text(title_text, dxfattribs={'height': 1.0, 'layer': 'SEC_TEXT'}).set_placement(
                (x_offset, roof_top_z + 3.0))

            # 2. 중심선 (CL) 작도
            msp.add_line((x_offset, floor_bot_z - 2.0), (x_offset, roof_top_z + 2.0),
                         dxfattribs={'layer': 'SEC_CENTER'})
            msp.add_text("C.L.", dxfattribs={'height': 0.6, 'layer': 'SEC_TEXT'}).set_placement(
                (x_offset + 0.2, roof_top_z + 1.0))

            # 3. 레벨 마크 및 텍스트 (해당 STA의 경사 표고 반영!)
            msp.add_text(f"Align.L = {align_lv:.2f}m", dxfattribs={'height': 0.5, 'layer': 'SEC_TEXT'}).set_placement(
                (x_offset + half_w + 1.0, align_lv))
            msp.add_line((x_offset - half_w - 0.5, align_lv), (x_offset + half_w + 0.5, align_lv),
                         dxfattribs={'layer': 'SEC_CENTER'})

            # 4. 부재 2D 닫힌 다각형 좌표
            polygons = [
                # 바닥 슬래브
                [(x_offset - half_w, floor_bot_z), (x_offset + half_w, floor_bot_z), (x_offset + half_w, floor_top_z),
                 (x_offset - half_w, floor_top_z)],
                # 천장 슬래브
                [(x_offset - half_w, roof_bot_z), (x_offset + half_w, roof_bot_z), (x_offset + half_w, roof_top_z),
                 (x_offset - half_w, roof_top_z)],
                # 좌측 외벽
                [(x_offset - half_w, floor_top_z), (x_offset - half_w + t_wall, floor_top_z),
                 (x_offset - half_w + t_wall, roof_bot_z), (x_offset - half_w, roof_bot_z)],
                # 우측 외벽
                [(x_offset + half_w - t_wall, floor_top_z), (x_offset + half_w, floor_top_z),
                 (x_offset + half_w, roof_bot_z), (x_offset + half_w - t_wall, roof_bot_z)]
            ]

            story_height = H / num_floors
            for i in range(1, num_floors):
                z_pos = floor_top_z + (i * story_height)
                polygons.append([
                    (x_offset - half_w + t_wall, z_pos - t_slab / 2),
                    (x_offset + half_w - t_wall, z_pos - t_slab / 2),
                    (x_offset + half_w - t_wall, z_pos + t_slab / 2),
                    (x_offset - half_w + t_wall, z_pos + t_slab / 2)
                ])
                msp.add_text(f"B{num_floors - i + 1}F SLAB",
                             dxfattribs={'height': 0.4, 'layer': 'SEC_TEXT'}).set_placement(
                    (x_offset + half_w + 1.0, z_pos))

            for poly_pts in polygons:
                msp.add_lwpolyline(poly_pts, close=True, dxfattribs={'layer': 'SEC_CONCRETE'})
                hatch = msp.add_hatch(color=8, dxfattribs={'layer': 'SEC_HATCH'})
                hatch.set_pattern_fill('ANSI31', scale=0.5)
                path = hatch.paths.add_polyline_path(poly_pts)
                path.closed = True

        doc.saveas(filename)
        return filename

    def create_sloped_box_faces(self, x1, x2, y1, y2, z_bot1, z_bot2, z_top1, z_top2):
        # 종방향 경사를 가지는 6면체(3DFACE) 생성 헬퍼
        p = [
            (x1, y1, z_bot1), (x2, y1, z_bot2), (x2, y2, z_bot2), (x1, y2, z_bot1),  # 바닥 4점
            (x1, y1, z_top1), (x2, y1, z_top2), (x2, y2, z_top2), (x1, y2, z_top1)  # 천장 4점
        ]
        return [
            (p[0], p[1], p[2], p[3]), (p[4], p[7], p[6], p[5]),
            (p[0], p[4], p[5], p[1]), (p[1], p[5], p[6], p[2]),
            (p[2], p[6], p[7], p[3]), (p[3], p[7], p[4], p[0])
        ]

    def create_flat_box_faces(self, x1, x2, y1, y2, z1, z2):
        p = [
            (x1, y1, z1), (x2, y1, z1), (x2, y2, z1), (x1, y2, z1),
            (x1, y1, z2), (x2, y1, z2), (x2, y2, z2), (x1, y2, z2)
        ]
        return [
            (p[0], p[1], p[2], p[3]), (p[4], p[7], p[6], p[5]),
            (p[0], p[4], p[5], p[1]), (p[1], p[5], p[6], p[2]),
            (p[2], p[6], p[7], p[3]), (p[3], p[7], p[4], p[0])
        ]


if __name__ == "__main__":
    root = tk.Tk()
    app = StationMVPAppSlope(root)
    root.mainloop()