# ============================================================
# CharacterManager
# ============================================================
from models.character import Character


class CharacterManager:
    SAVE_VERSION = 3

    def __init__(self):
        self.characters = {}

    # --------------------------------------------------------
    # 캐릭터
    # --------------------------------------------------------

    def add_character(self, name):
        if not name:
            return False

        if name in self.characters:
            return False

        self.characters[name] = Character(name)

        return True

    def remove_character(self, name):
        if name not in self.characters:
            return False

        del self.characters[name]

        return True

    def get_character(self, name):
        return self.characters.get(name)

    def get_names(self):
        return list(self.characters.keys())

    # --------------------------------------------------------
    # JSON 데이터
    # --------------------------------------------------------

    def to_dict(self):
        return {
            "version": self.SAVE_VERSION,
            "characters": {
                name: character.to_dict()
                for name, character in self.characters.items()
            },
        }

    def load_dict(self, data):
        version = data.get("version", 2)

        self.characters.clear()

        # v2 / v3 모두 읽을 수 있음
        if version not in (2, 3):
            raise ValueError(
                f"지원하지 않는 저장파일 버전입니다: {version}"
            )

        for name, character_data in (
            data.get("characters", {}).items()
        ):
            self.characters[name] = Character.from_dict(
                name,
                character_data
            )