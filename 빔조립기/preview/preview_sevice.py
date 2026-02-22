from bve.beam_builder import TempleteBeamBuilder
from bve.pole_builder import TempletePoleBuilder
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
        beam_cache = {}
        pole_cache = {}
        locator = FileLocator(PathResolver.BASE_PATH)

        # 1. 빔
        for beam in install.beams:
            if beam.iscustom:

                if beam.length not in beam_cache:
                    builder = TempleteBeamBuilder(beam.length)
                    beam_cache[beam.length] = builder.build()

                path = beam_cache[beam.length]
            else:
                path = locator.find(beam.name)
            if path:

                items.append(
                    PreviewItem(
                        path=path,
                        transform=Transform(
                            x=beam.ref_start_pole.xoffset,
                            y=install.station,
                            z=0,
                            rotation=0,
                            pivot=beam.ref_start_pole.base_rail.coord
                        ),
                        category=PreviewCategory.BEAM

                    )
                )
            else:
                missing.append(beam.name)

        # 2. 기둥
        for col in install.poles:
            if col.iscustom:
                if col.length not in pole_cache:
                    builder = TempletePoleBuilder(col.length, col.width)
                    pole_cache[col.length] = builder.build()

                path = pole_cache[col.length]
            else:
                path = locator.find(col.display_name)
            if path:
                items.append(
                    PreviewItem(
                        path=path,
                        transform=Transform(
                            x=col.xoffset,
                            y=install.station,
                            z=0,
                            rotation=0,
                            pivot=col.base_rail.coord
                        ),
                    category=PreviewCategory.POLE
                    )
                )
            else:
                missing.append(col.display_name)

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
                                y=install.station,
                                z=br.yoffset,
                                rotation=br.rotation,
                                pivot=rail.coord
                            ),
                            category=PreviewCategory.BRACKET
                        )
                    )
                else:
                    missing.append(br.type)
                #3-1 브래킷 피팅
                # 브래킷 하위 피팅들
                for f in getattr(br, "fittings", []):  # 기존 데이터 호환 위해 getattr 사용
                    fpath = locator.find(f.label)
                    if fpath:
                        items.append(
                            PreviewItem(
                                path=fpath,
                                transform=Transform(
                                    x=f.xoffset,
                                    y=install.station,
                                    z=f.yoffset,
                                    rotation=f.rotation,
                                    pivot=rail.coord
                                ),
                                category=PreviewCategory.BRACKET
                            )
                        )
                    else:
                        missing.append(f.label)

        #4 레일
        for rail in install.rails:
            items.append(
                PreviewItem(
                    path=r'D:/BVE/루트/Railway/Object/철도표준라이브러리/궤도/표준단면/자갈도상/일반철도/5M레일_신선_전차선X.csv',#현재 임시로 하드코딩
                    transform=Transform(
                        x=0,
                        y=install.station,
                        z=0,
                        rotation=0,
                        pivot=rail.coord
                    ),
                    category=PreviewCategory.TRACK
                )
            )

        #5 장비들
        for equip in install.equips:
            items.append(
                PreviewItem(
                    path=locator.find(equip.name),
                    transform=Transform(
                        x=equip.xoffset,
                        y=install.station,
                        z=equip.yoffset,
                        rotation=equip.rotation,
                        pivot=equip.base_rail.coord
                    ),
                    category=PreviewCategory.FEEDER
                )
            )
        objects = PreviewAssembler.load_items(items)

        return PreviewBuildResult(objects=objects, missing=missing)

