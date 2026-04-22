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
            faces_pv = np.hstack([[3, *f] for f in faces])
            pv_mesh = pv.PolyData(vertices, faces_pv)
            plotter.add_mesh(pv_mesh, color=color, show_edges=True, opacity=0.7, label=name)

        plotter.add_legend()
        plotter.show()
