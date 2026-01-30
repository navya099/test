from controller.filefinder import FileLocator
from controller.path_resolver import PathResolver
from preview.category import PreviewCategory
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
        beam_path = locator.find(install.beam_assembly.beam.name)
        if beam_path:

            items.append(
                PreviewItem(
                    path=beam_path,
                    transform=Transform(
                        x=install.beam_assembly.beam.x,
                        z=install.beam_assembly.beam.y,
                        rotation=install.beam_assembly.beam.rotation,
                    ),
                    category=PreviewCategory.BEAM

                )
            )
        else:
            missing.append(install.beam_assembly.beam.name)

        # 2. 기둥
        for col in install.beam_assembly.columns:
            path = locator.find(col.name)
            if path:
                items.append(
                    PreviewItem(
                        path=path,
                        transform=Transform(
                            x=col.xoffset,
                            z=col.yoffset,
                            rotation=0
                        ),
                    category=PreviewCategory.POLE
                    )
                )
            else:
                missing.append(col.name)

        # 3. 브래킷
        for rail in install.rails:
            for br in rail.brackets:
                path = locator.find(br.type)
                if path:
                    items.append(
                        PreviewItem(
                            path=path,
                            transform=Transform(
                                x=br.xoffset,
                                z=br.yoffset,
                                rotation=br.rotation,
                                pivot=rail.coord
                            ),
                            category=PreviewCategory.BRACKET
                        )
                    )
                else:
                    missing.append(br.type)
        #4 레일
        for rail in install.rails:
            items.append(
                PreviewItem(
                    path=r'D:/BVE/루트/Railway/Object/철도표준라이브러리/궤도/표준단면/자갈도상/일반철도/5M레일_신선_전차선X.csv',#현재 임시로 하드코딩
                    transform=Transform(
                        x=0,
                        z=0,
                        rotation=0,
                        pivot=rail.coord
                    ),
                    category=PreviewCategory.TRACK
                )
            )
        objects = PreviewAssembler.load_items(items)

        return PreviewBuildResult(objects=objects, missing=missing)

