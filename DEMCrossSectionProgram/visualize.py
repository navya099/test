import pyvista as pv
import numpy as np
import meshio


class SectionVisualizer:
    def __init__(self):
        """PyVista를 활용한 토공 단면 및 3D 메쉬 정밀 검증 시각화 도구"""
        # 정점 플로팅을 위한 스타일 정의
        self.point_style = dict(render_points_as_spheres=True, point_size=12)

    def _meshio_to_pyvista(self, meshio_mesh):
        """meshio.Mesh 객체를 PyVista.PolyData로 안전하게 변환"""
        if meshio_mesh is None or len(meshio_mesh.points) == 0:
            return None

        # meshio의 정점 데이터 확보 (N, 3)
        points = np.array(meshio_mesh.points)

        # meshio의 triangle cells를 pyvista의 순서 포맷([3, v0, v1, v2, 3, v0, ...])으로 패킹
        faces_list = []
        for cell in meshio_mesh.cells:
            if cell.type == "triangle":
                for tri in cell.data:
                    faces_list.append([3, tri[0], tri[1], tri[2]])

        if not faces_list:
            return pv.PolyData(points)

        faces = np.hstack(faces_list)
        return pv.PolyData(points, faces)

    def verify_section_3d(self, section_data, terrain_mesh, slope_left_mesh, slope_right_mesh):
        """
        SectionProvider가 리턴한 2D/3D 결과 데이터가 
        실제 3D 공간 메쉬와 완벽히 정렬되었는지 가시화 검증
        """
        # 1. 시각화 윈도우(Plotter) 생성 및 배경 설정
        pl = pv.Plotter(title=f"3D Section Verification [Station: {section_data['station']}]")
        pl.background_color = "white"

        # 2. 원지반(Terrain) 메쉬 시각화 (반투명 회색조 지형)
        pv_terrain = self._meshio_to_pyvista(terrain_mesh)
        if pv_terrain:
            pl.add_mesh(pv_terrain, color="#d3d3d3", opacity=0.6, show_edges=True,
                        edge_color="#a9a9a9", label="Exist Ground Mesh")

        # 3. 좌/우 설계 사면 메쉬 시각화
        pv_slope_l = self._meshio_to_pyvista(slope_left_mesh)
        pv_slope_r = self._meshio_to_pyvista(slope_right_mesh)

        if pv_slope_l:
            pl.add_mesh(pv_slope_l, color="#b0c4de", opacity=0.7, show_edges=True,
                        edge_color="#4682b4", label="Left Slope Mesh")
        if pv_slope_r:
            pl.add_mesh(pv_slope_r, color="#f4a460", opacity=0.7, show_edges=True,
                        edge_color="#d2691e", label="Right Slope Mesh")

        # 4. 주요 구조적 좌표 복원 (3D 절대좌표 복안 연산)
        # 횡단면 변수 추출
        center_xyz = np.array(section_data['center'])
        left_edge_xyz = np.array(section_data['left'])
        right_edge_xyz = np.array(section_data['right'])

        # 3D 사면 끝점 좌표 복원
        # SectionProvider 내부에서 매칭한 포인트와 완벽히 동일한 인덱스를 추적합니다.
        n_half_l = len(slope_left_mesh.points) // 2
        n_half_r = len(slope_right_mesh.points) // 2

        # 데이터 정합성 확인을 위해 메쉬 내부의 3D 실좌표를 직접 찍어봅니다.
        # 이 점이 메쉬의 맨 바깥쪽 라인 테두리에 칼같이 얹혀야 성공입니다.
        current_local_idx = np.argmin(np.linalg.norm(slope_left_mesh.points[:n_half_l] - left_edge_xyz, axis=1))

        actual_left_end_3d = slope_left_mesh.points[n_half_l + current_local_idx]
        actual_right_end_3d = slope_right_mesh.points[n_half_r + current_local_idx]

        # 5. 핵심 기하점들을 3D 공간에 Spheres로 마킹
        pl.add_mesh(pv.PolyData(center_xyz), color="black", label="Track Center", **self.point_style)
        pl.add_mesh(pv.PolyData(left_edge_xyz), color="purple", label="Track Left Edge", **self.point_style)
        pl.add_mesh(pv.PolyData(right_edge_xyz), color="red", label="Track Right Edge", **self.point_style)
        pl.add_mesh(pv.PolyData(actual_left_end_3d), color="blue", label="Calculated Left Catch Point",
                    **self.point_style)
        pl.add_mesh(pv.PolyData(actual_right_end_3d), color="darkorange", label="Calculated Right Catch Point",
                    **self.point_style)

        # 6. 설계 횡단선 라인 연결 (선로 에지 -> 사면 끝점)
        left_slope_line = pv.Line(left_edge_xyz, actual_left_end_3d)
        right_slope_line = pv.Line(right_edge_xyz, actual_right_end_3d)
        track_bed_line = pv.Line(left_edge_xyz, right_edge_xyz)

        pl.add_mesh(left_slope_line, color="blue", line_width=5)
        pl.add_mesh(right_slope_line, color="darkorange", line_width=5)
        pl.add_mesh(track_bed_line, color="black", line_width=6)

        # 7. 카메라 포커스를 현재 측점 중심으로 자동 조준
        pl.camera.position = (center_xyz[0] + 30, center_xyz[1] + 30, center_xyz[2] + 40)
        pl.camera.focal_point = center_xyz
        pl.camera.up = (0, 0, 1)

        # 축 및 범례 추가 후 랜더링
        pl.add_axes()
        pl.add_legend(bcolor=None, face="circle")
        pl.show()