from xref_module.filefinder import FileLocator
from xref_module.path_resolver import PathResolver
from xref_module.preview.category import PreviewCategory
from xref_module.preview.previe_assembler import PreviewAssembler
from xref_module.preview.preview_item import PreviewItem
from xref_module.objmodel.transform import Transform
from xref_module.preview.preview_result import PreviewBuildResult


class PreviewService:
    def __init__(self):
        pass
    def build(self, pole):
        items = []
        missing = []
        locator = FileLocator(PathResolver.BASE_PATH)
        # 2. 기둥
        mast = pole.mast
        path = locator.find(mast.name)
        if path:
            items.append(
                PreviewItem(
                    path=path,
                    transform=Transform(
                        x=mast.offset,
                        z=0,
                        rotation=0,
                    ),
                category=PreviewCategory.POLE
                )
            )
        else:
            missing.append(mast.name)

        # 3. 브래킷
        for br in pole.brackets:
            path = locator.find(br.bracket_name)
            if path:
                items.append(
                    PreviewItem(
                        path=path,
                        transform=Transform(
                            x=br.offset[0],
                            z=br.offset[1],
                        ),
                        category=PreviewCategory.BRACKET
                    )
                )
            else:
                missing.append(br.bracket_name)
        #4 브래킷 피팅
        for br in pole.brackets:
            for f in br.fittings:
                path = locator.find(f.label)
                if path:
                    items.append(
                        PreviewItem(
                            path=path,
                            transform=Transform(
                                x=f.offset[0],
                                z=f.offset[1],
                            ),
                            category=PreviewCategory.BRACKET
                        )
                    )
                else:
                    missing.append(f.label)
        #4 레일
        items.append(
            PreviewItem(
                path=r'D:/BVE/루트/Railway/Object/철도표준라이브러리/궤도/표준단면/자갈도상/일반철도/5M레일_신선_전차선X.csv',#현재 임시로 하드코딩
                transform=Transform(
                    x=0,
                    z=0,
                    rotation=0,
                ),
                category=PreviewCategory.TRACK
            )
        )

        #5 장비들
        for equip in pole.equipments:
            path = locator.find(equip.name)
            if path:
                items.append(
                    PreviewItem(
                        path=path,
                        transform=Transform(
                            x=equip.offset[0],
                            z=equip.offset[1],
                            rotation=equip.rotation,
                        ),
                        category=PreviewCategory.FEEDER
                    )
                )
            else:
                missing.append(equip.name)
        #6구조물
        if pole.structure == '교량':
            path = r'D:/BVE/루트/Railway/Object/철도표준라이브러리/노반/교량/psc거더교_단선.csv'
        elif pole.structure == '터널':
            path = r'D:/BVE/루트/Railway/Object/동해선/노반/터널/natm.csv'
        else:
            path = r'D:/BVE/루트/Railway/Object/동해선/노반/토공/표준횡단면도.csv'

        items.append(
            PreviewItem(
                path=path,
                transform=Transform(
                    x=0,
                    z=0,
                    rotation=0,
                ),
                category=PreviewCategory.STRUCTURE
            )
        )
        objects = PreviewAssembler.load_items(items)

        return PreviewBuildResult(objects=objects, missing=missing)

