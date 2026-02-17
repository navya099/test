from xref_module.filefinder import FileLocator
from xref_module.path_resolver import PathResolver
from xref_module.preview.category import PreviewCategory
from xref_module.preview.previe_assembler import PreviewAssembler
from xref_module.preview.preview_item import PreviewItem
from xref_module.objmodel.transform import Transform
from xref_module.preview.preview_result import PreviewBuildResult
from xref_module.vector3.vector3 import Vector3


class PreviewService:
    def __init__(self):
        self.locator = FileLocator(PathResolver.BASE_PATH)

    def build(self, pole, trackidx, distnace=4.3, direction=1, mode='single'):
        items = []
        missing = []
        distnace *= direction
        if trackidx == 0:
            pivot = Vector3(0,0,0)
        else:
            pivot = Vector3(distnace, 0, 0)

        if not pole:
            return PreviewBuildResult(objects=[], missing=["pole이 None입니다"])

        # 2. 기둥
        try:
            mast = pole.mast
            if mast:
                path = self.locator.find(mast.name)
                if path:
                    items.append(
                        PreviewItem(
                            path=path,
                            transform=Transform(x=mast.offset, z=0, rotation=mast.rotation,pivot=pivot),
                            category=PreviewCategory.POLE
                        )
                    )
                else:
                    missing.append(mast.name)
        except Exception as e:
            print(f"[Mast 처리 오류] {e}")
            missing.append("mast 처리 실패")

        # 3. 브래킷
        for br in getattr(pole, "brackets", []):
            try:
                if br:
                    path = self.locator.find(br.bracket_name)
                    if path:
                        items.append(
                            PreviewItem(
                                path=path,
                                transform=Transform(x=br.offset[0], z=br.offset[1], rotation=br.rotation,pivot=pivot),
                                category=PreviewCategory.BRACKET
                            )
                        )
                    else:
                        missing.append(br.bracket_name)

                    # 브래킷 피팅류
                    for f in getattr(br, "fittings", []):
                        try:
                            if f:
                                path = self.locator.find(f.label)
                                if path:
                                    items.append(
                                        PreviewItem(
                                            path=path,
                                            transform=Transform(x=f.offset[0], z=f.offset[1],rotation=f.rotation,pivot=pivot),
                                            category=PreviewCategory.BRACKET
                                        )
                                    )
                                else:
                                    missing.append(f.label)
                        except Exception as e:
                            print(f"[Fitting 처리 오류] {e}")
                            missing.append("fitting 처리 실패")
            except Exception as e:
                print(f"[Bracket 처리 오류] {e}")
                missing.append("bracket 처리 실패")

        # 4. 레일 (임시 하드코딩)
        items.append(
            PreviewItem(
                path=r"D:/BVE/루트/Railway/Object/철도표준라이브러리/궤도/표준단면/자갈도상/일반철도/5M레일_신선_전차선X.csv",
                transform=Transform(x=0, z=0, rotation=0,pivot=pivot),
                category=PreviewCategory.TRACK
            )
        )

        # 5. 장비들
        for equip in getattr(pole, "equipments", []):
            try:
                if equip:
                    path = self.locator.find(equip.name)
                    if path:
                        items.append(
                            PreviewItem(
                                path=path,
                                transform=Transform(x=equip.offset[0], z=equip.offset[1], rotation=equip.rotation,pivot=pivot),
                                category=PreviewCategory.FEEDER
                            )
                        )
                    else:
                        missing.append(equip.name)
            except Exception as e:
                print(f"[Equipment 처리 오류] {e}")
                missing.append("equipment 처리 실패")

        # 6. 구조물
        try:
            if pole.structure == "교량":
                if mode == 'single':
                    path = r"D:/BVE/루트/Railway/Object/철도표준라이브러리/노반/교량/psc거더교_단선.csv"
                else:
                    if trackidx == 0:
                        path = r"E:\백업\C\Documents\배포용\가상 달빛내륙선 배포용\railway\object\전라선\노반\교량\psc빔 복선.csv"
                    else:
                        path = r'D:\BVE\루트\Railway\Object\abcdefg\dummy.csv'
            elif pole.structure == "터널":
                if mode == 'single':
                    path = r"D:/BVE/루트/Railway/Object/동해선/노반/터널/natm.csv"
                else:
                    if trackidx == 0:
                        path = r"D:/BVE/루트/Railway/Object/호남선\노반\구조물\터널\4.3m터널.csv"
                    else:
                        path = r'D:\BVE\루트\Railway\Object\abcdefg\dummy.csv'
            else:
                if mode == 'single':
                    path = r"D:/BVE/루트/Railway/Object/동해선/노반/토공/표준횡단면도.csv"
                else:
                    if trackidx == 0:
                        path = r"D:/BVE/루트/Railway/Object/중앙선/노반/토공/6공구복선노반l.csv"
                    else:
                        path = r'D:\BVE\루트\Railway\Object\abcdefg\dummy.csv'
            items.append(
                PreviewItem(
                    path=path,
                    transform=Transform(x=0, z=0, rotation=0,pivot=pivot),
                    category=PreviewCategory.STRUCTURE
                )
            )
        except Exception as e:
            print(f"[Structure 처리 오류] {e}")
            missing.append("structure 처리 실패")

        # 최종 조립
        objects = PreviewAssembler.load_items(items)
        return PreviewBuildResult(objects=objects, missing=missing)

