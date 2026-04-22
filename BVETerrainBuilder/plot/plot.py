import numpy as np
import pyvista as pv

class MeshPlotter:
    @staticmethod
    def plot_multiple_meshes(meshes_with_colors):
        """
        meshes_with_colors: [(vertices, faces, color, name), ...]
        """
        plotter = pv.Plotter()

        for vertices, faces, color, name in meshes_with_colors:
            # PyVista faces 형식으로 변환
            n_faces = faces.shape[0]
            faces_pv = np.hstack([np.full((n_faces, 1), 3), faces]).flatten()
            pv_mesh = pv.PolyData(vertices, faces_pv)
            plotter.add_mesh(pv_mesh, color=color, show_edges=True, opacity=0.7, label=name)

        plotter.add_legend()
        plotter.show_bounds()  # 좌표 범위 표시
        show_edges = True #삼각엣지 표시
        plotter.show()
