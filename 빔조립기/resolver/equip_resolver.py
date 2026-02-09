
class EquipmentResolver:
    @staticmethod
    def resolve(equips, idxlib, rail_map, pole_map):

        for equip in equips:
            equip.objindex = idxlib.get_index(equip.name)
            equip.base_rail = rail_map[equip.base_rail_index]
