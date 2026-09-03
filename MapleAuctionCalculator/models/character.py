# ============================================================
# Character
# ============================================================
import copy

from config import create_default_efficiency_table
from models.equipment import Equipment


class Character:
    def __init__(self, name):
        self.name = name

        # ★ 캐릭터별 독립 효율표
        self.efficiency_table = create_default_efficiency_table()

        # 실제 사용하는 장비만 생성
        self.equipments = {}

    # --------------------------------------------------------
    # 장비
    # --------------------------------------------------------

    def add_equipment(self, name):
        if name in self.equipments:
            return False

        self.equipments[name] = Equipment(name)
        return True

    def remove_equipment(self, name):
        if name not in self.equipments:
            return False

        del self.equipments[name]
        return True

    def get_equipment(self, name):
        return self.equipments.get(name)

    def get_equipment_names(self):
        return list(self.equipments.keys())

    # --------------------------------------------------------
    # 효율표
    # --------------------------------------------------------

    def reset_efficiency_table(self):
        self.efficiency_table = create_default_efficiency_table()

    def set_efficiency_table(self, table):
        self.efficiency_table = copy.deepcopy(table)

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    def to_dict(self):
        return {
            "efficiency_table": copy.deepcopy(
                self.efficiency_table
            ),
            "equipments": {
                name: equipment.to_dict()
                for name, equipment in self.equipments.items()
            },
        }

    @classmethod
    def from_dict(cls, name, data):
        character = cls(name)

        # v3 효율표
        saved_table = data.get("efficiency_table")

        if saved_table:
            character.efficiency_table = (
                cls._merge_efficiency_table(saved_table)
            )

        # 장비
        for equipment_name, equipment_data in (
            data.get("equipments", {}).items()
        ):
            character.equipments[equipment_name] = (
                Equipment.from_dict(
                    equipment_name,
                    equipment_data
                )
            )

        return character

    @staticmethod
    def _merge_efficiency_table(saved_table):
        """
        저장파일에 일부 항목이 없더라도
        기본값을 사용해서 안전하게 복원한다.
        """

        default_table = create_default_efficiency_table()

        for stat_name, stat_data in saved_table.items():

            if stat_name not in default_table:
                # 앞으로 새로운 스탯을 추가했을 때도 유지
                default_table[stat_name] = copy.deepcopy(stat_data)
                continue

            if isinstance(stat_data, dict):
                if "value" in stat_data:
                    default_table[stat_name]["value"] = (
                        float(stat_data["value"])
                    )

                if "final" in stat_data:
                    default_table[stat_name]["final"] = (
                        float(stat_data["final"])
                    )

        return default_table