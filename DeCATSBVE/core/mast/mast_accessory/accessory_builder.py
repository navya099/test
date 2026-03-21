from core.mast.mast_accessory.mast_accessory import MastAccessory


class AccessoryBuilder:
    @staticmethod
    def build(dataprocessor, idxlib, band_type, size, structure, rotation, gauge) -> list[MastAccessory]:
        accessories = []
        if band_type in ["가동브래킷용", "완철용"]:
            band_dict = dataprocessor.get_mast_band_index(band_type=band_type, size=size)
            offset_dict = dataprocessor.get_mast_band_offset(band_type=band_type, current_structure=structure)

            if structure != '터널':
                if isinstance(band_dict, dict):  # 상부/하부 존재
                    for pos in band_dict:
                        idx = band_dict[pos]
                        name = idxlib.get_name(idx)
                        offset = offset_dict[pos]
                        accessories.append(MastAccessory(name=name, index=idx, rotation=rotation, offset=(gauge, offset)))
                else:  # 단일 밴드
                    idx = band_dict
                    name = idxlib.get_name(idx)
                    offset = offset_dict
                    accessories.append(MastAccessory(name=name, index=idx, rotation=rotation, offset=(gauge, offset)))

            # 기타 밴드 타입 처리 (안전하게 확장)
        else:
            extra_band_dict = dataprocessor.get_extra_band_index() or {}
            extra_offset_dict = dataprocessor.get_extra_band_offset() or {}

            for sub_type, sub_dict in extra_band_dict.items():
                offset_sub = extra_offset_dict.get(sub_type, {})
                idx = sub_dict.get(size)# P10/P12 구조
                name = idxlib.get_name(idx)
                offset = offset_sub.get(structure, 0)
                accessories.append(
                    MastAccessory(name=name, index=idx, rotation=rotation, offset=(gauge, offset)))

        return accessories
