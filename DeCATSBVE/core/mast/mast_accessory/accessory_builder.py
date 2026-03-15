from core.mast.mast_accessory.mast_accessory import MastAccessory


class AccessoryBuilder:
    @staticmethod
    def build(dataprocessor, idxlib, band_type, size, structure, rotation, gauge) -> list[MastAccessory]:
        band_dict = dataprocessor.get_mast_band_index(band_type=band_type, size=size)
        offset_dict = dataprocessor.get_mast_band_offset(band_type=band_type, current_structure=structure)

        accessories = []
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
            return accessories
        else:
            return accessories
