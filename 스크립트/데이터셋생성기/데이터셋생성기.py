
import json
from dataclasses import asdict

from CONFIG_150 import config_150
from CONFIG_250 import config_250
from CONFIG_350 import config_350
from CONFIG_CUSTOM import config_custom

configs = {
    150: config_150,
    250: config_250,
    350: config_350,
    'custom': config_custom
}

def save_configs(configs, path="c:/temp"):
    for speed, cfg in configs.items():
        with open(f"{path}/railway_{speed}.json", "w", encoding="utf-8") as f:

            json.dump(asdict(cfg), f, ensure_ascii=False, indent=2)

# 필요할 때 꺼내쓰기
if __name__ == "__main__":
    save_configs(configs)