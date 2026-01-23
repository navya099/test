from controller.file_controler import FileController
from controller.obj_builder import FaceBuilder
from controller.temp_parser import parse_sketchup_csv_lines
from model.objmodel.csvobject import BracketObject3D
from model.objmodel.object_modifyer import ObjectModifier
from preview.preview_item import PreviewItem
from world.coordinatesystem import sketchup_to_world


class PreviewAssembler:
    @staticmethod
    def load_items(items: list[PreviewItem]):
        objects = []
        filecontroller = FileController()
        transformer = ObjectModifier()
        for item in items:
            filecontroller.set_path(item.path)
            filecontroller.load()
            meshes = parse_sketchup_csv_lines(
                filecontroller.get_lines()
            )

            for vertices, faces in meshes:
                vertices = sketchup_to_world(vertices)
                transformer.set_vertices(vertices)
                transformer.rotate_z(item.transform.rotation)
                transformer.translate(
                    item.transform.x,
                    item.transform.y,
                    item.transform.z
                )

                edges = FaceBuilder.build_edges_from_faces(faces)
                objects.append(BracketObject3D(transformer.vertices, edges))

        return objects

