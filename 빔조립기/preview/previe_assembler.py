from controller.file_controler import FileController
from controller.temp_parser import CSVObjectParser
from model.objmodel.object_modifyer import ObjectModifier
from preview.preview_item import PreviewItem
from world.convert import CoordinateConverter
from world.coordinatesystem import CoordinateSystem


class PreviewAssembler:
    @staticmethod
    def load_items(items: list[PreviewItem]):
        objects = []
        filecontroller = FileController()
        coordsystemconvertor = CoordinateConverter()
        for item in items:
            filecontroller.set_path(item.path)
            filecontroller.load()

            csvobj = CSVObjectParser(
                filecontroller.get_lines()
            ).parse()
            ## 좌표계는 항상 WORLD 기준으로 ObjectModifier 적용
            coordsystemconvertor.convert(csvobj, CoordinateSystem.WORLD)
            modifier = ObjectModifier(csvobj)
            modifier.set_pivot(item.transform.pivot)
            modifier.rotate_z(item.transform.rotation)
            modifier.translate_local(
                item.transform.x,
                item.transform.y,
                item.transform.z
            )
            modifier.apply()

            objects.append(csvobj)

        return objects

