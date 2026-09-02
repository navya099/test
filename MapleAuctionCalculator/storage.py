# storage.py

import json


class JsonStorage:

    @staticmethod
    def save(manager, filepath):
        data = manager.to_dict()

        with open(
            filepath,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=4
            )

    @staticmethod
    def load(manager, filepath):

        with open(
            filepath,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        manager.load_dict(data)