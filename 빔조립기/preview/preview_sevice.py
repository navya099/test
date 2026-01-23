from controller.filefinder import FileLocator
from controller.path_resolver import PathResolver
from preview.previe_assembler import PreviewAssembler
from preview.preview_item import PreviewItem
from preview.preview_result import PreviewBuildResult
from model.objmodel.transform import Transform

class PreviewService:
    @staticmethod
    def build_from_install(install):
        items = []
        missing = []

        locator = FileLocator(PathResolver.BASE_PATH)

        # 1. 빔
        beam_path = locator.find(install.beam.name)
        if beam_path:

            items.append(
                PreviewItem(
                    path=beam_path,
                    transform=Transform(
                        x=install.beam.x,
                        z=install.beam.y,
                        rotation=install.beam.rotation,
                    )
                )
            )
        else:
            missing.append(install.beam.name)

        # 2. 기둥
        for col in install.columns:
            path = locator.find(col.name)
            if path:
                items.append(
                    PreviewItem(
                        path=path,
                        transform=Transform(
                            x=col.xoffset,
                            z=col.yoffset,
                            rotation=0
                        )
                    )
                )
            else:
                missing.append(col.name)

        # 3. 브래킷
        for br in install.brackets:
            path = locator.find(br.type)
            if path:
                items.append(
                    PreviewItem(
                        path=path,
                        transform=Transform(
                            x=br.xoffset,
                            z=br.yoffset,
                            rotation=br.rotation
                        )
                    )
                )
            else:
                missing.append(br.type)

        objects = PreviewAssembler.load_items(items)

        return PreviewBuildResult(objects=objects, missing=missing)

