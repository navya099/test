import os
import json


class ConfigManager:
    def __init__(self, file=None):
        self.file = file
        self.config = self.load_config()
        self.default_values = self.get_default_values()
        self.file_paths = self.get_file_paths()


    def load_config(self):
        if not os.path.exists(self.file):
            print("⚠️ 설정 파일이 없습니다. config.json을 만들어주세요.")
            return None
        with open(self.file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_default_values(self):
        return self.config.get("default_values", {})

    def get_file_paths(self):
        return self.config.get("file-path", {})

    def validate_config(self):
        # 값 검사
        self.validate_choice(self.default_values["DESIGNSPEED"], [150, 250, 350], "DESIGNSPEED")
        self.validate_choice(self.default_values["LINECOUNT"], [1, 2], "LINECOUNT")
        self.validate_positive_float(self.default_values["LINEOFFSET"], "LINEOFFSET")
        self.validate_choice(self.default_values["POLE_direction"], [-1, 1], "POLE_direction")
        self.validate_choice(self.default_values["curve"], ["곡선", "직선"], "curve")

        # current_airjoint 값 검사 (AirJoint 멤버 검사)
        if self.default_values["current_airjoint"] not in ['일반개소', 'START', 'POINT_2', 'MIDDLE', 'POINT_4', 'END']:
            raise ValueError("current_airjoint는 AirJoint 멤버 중 하나여야 합니다.")

        # pitch 값 검사
        self.validate_positive_float(self.default_values["pitch"], "pitch")

        # file-path 유효성 검사
        for key in ["curve_info", "pitch_info", "coord_filepath"]:
            if key not in self.file_paths:
                raise ValueError(f"{key} 파일 경로가 설정되지 않았습니다.")
            if not self.file_paths[key].endswith(".txt"):
                raise ValueError(f"{key} 파일은 .txt 확장자를 가져야 합니다.")

        return True

    def validate_positive_float(self, value, field_name):
        try:
            f_value = float(value)
            if f_value <= 0:
                raise ValueError(f"{field_name}는 양의 실수여야 합니다.")
            return f_value
        except ValueError:
            raise ValueError(f"{field_name}는 실수로 입력되어야 합니다.")

    def validate_choice(self, value, valid_choices, field_name):
        if value not in valid_choices:
            raise ValueError(f"{field_name}는 {', '.join(map(str, valid_choices))} 중 하나여야 합니다.")

    def check_config(self):
        # 필수 키 확인 (기본 값 부분)
        required_default_keys = [
            "DESIGNSPEED", "LINECOUNT", "LINEOFFSET", "POLE_direction",
            "post_number", "pos", "next_pos", "current_type", "next_type",
            "current_structure", "next_structure", "curve", "current_airjoint", "pitch"
        ]
        for key in required_default_keys:
            if key not in self.default_values:
                raise ValueError(f"❌ {key} 값이 설정에 없습니다.")

        # 파일 경로가 설정되어 있는지 확인
        required_file_keys = ["curve_info", "pitch_info", "coord_filepath"]
        for key in required_file_keys:
            if key not in self.file_paths:
                raise ValueError(f"❌ {key} 파일 경로가 설정에 없습니다.")

        return True

    def get_params(self):
        return {key: value for key, value in self.config.items()}
