# config.py

import copy


DEFAULT_EFFICIENCY_TABLE = {
    "보총뎀": {
        "value": 40,
        "final": 5.350,
    },
    "마력": {
        "value": 30,
        "final": 0.823,
    },
    "마력%": {
        "value": 12,
        "final": 5.192,
    },
    "크뎀": {
        "value": 8,
        "final": 3.082,
    },
    "방무(300)": {
        "value": 40,
        "final": 0.763,
    },
    "방무(380)": {
        "value": 40,
        "final": 0.971,
    },
    "INT": {
        "value": 30,
        "final": 0.282,
    },
    "INT%": {
        "value": 12,
        "final": 1.247,
    },
    "%미반영 INT": {
        "value": 200,
        "final": 0.364,
    },
    "LUK": {
        "value": 30,
        "final": 0.025,
    },
    "LUK%": {
        "value": 12,
        "final": 0.163,
    },
    "%미반영 LUK": {
        "value": 200,
        "final": 0.091,
    },
    "올스탯%": {
        "value": 9,
        "final": 1.057,
    },
}


DEFAULT_EQUIPMENT_NAMES = [
    "귀고리",
    "펜던트",
    "반지",
    "눈장",
    "얼장",
    "견장",
    "망토",
    "모자",
    "상의",
    "하의",
    "장갑",
    "신발",
    "무기",
]


def create_default_efficiency_table():
    """
    캐릭터마다 독립적인 효율표를 생성한다.
    deepcopy를 사용하는 것이 중요하다.
    """
    return copy.deepcopy(DEFAULT_EFFICIENCY_TABLE)