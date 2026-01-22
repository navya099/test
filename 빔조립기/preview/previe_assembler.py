from controller.file_controler import FileController
from controller.obj_builder import FaceBuilder
from controller.temp_parser import parse_sketchup_csv_lines
from model.objmodel.csvobject import BracketObject3D
from world.coordinatesystem import sketchup_to_world


class PreviewAssembler:
    @staticmethod
    def load_objects(file_paths: list[str]):
        objects = []

        for path in file_paths:
            fm = FileController(path)
            fm.load()

            meshes = parse_sketchup_csv_lines(fm.get_lines())
            for vertices, faces in meshes:
                vertices = sketchup_to_world(vertices)
                edges = FaceBuilder.build_edges_from_faces(faces)

                objects.append(
                    BracketObject3D(vertices, edges)
                )

        return objects
