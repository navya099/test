import json
from dataclasses import asdict
from model.pole_install import PoleInstall
from vector3 import Vector3

from vector3 import Vector3

def vector3_to_dict(v: Vector3):
    return {
        "__type__": "Vector3",
        "x": v.x,
        "y": v.y,
        "z": v.z,
    }

def dict_to_vector3(d: dict):
    return Vector3(d["x"], d["y"], d["z"])

class PoleInstallSerializer:

    @staticmethod
    def normalize(obj):
        if isinstance(obj, Vector3):
            return vector3_to_dict(obj)

        if isinstance(obj, list):
            return [PoleInstallSerializer.normalize(v) for v in obj]

        if isinstance(obj, dict):
            return {
                k: PoleInstallSerializer.normalize(v)
                for k, v in obj.items()
            }

        return obj

    @staticmethod
    def denormalize(obj):
        if isinstance(obj, dict):
            if obj.get("__type__") == "Vector3":
                return dict_to_vector3(obj)

            return {
                k: PoleInstallSerializer.denormalize(v)
                for k, v in obj.items()
            }

        if isinstance(obj, list):
            return [PoleInstallSerializer.denormalize(v) for v in obj]

        return obj

    @staticmethod
    def to_dict(install: PoleInstall):
        raw = asdict(install)
        return PoleInstallSerializer.normalize(raw)

    @staticmethod
    def save(install: PoleInstall, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                PoleInstallSerializer.to_dict(install),
                f,
                ensure_ascii=False,
                indent=2
            )

    @staticmethod
    def load(path: str) -> PoleInstall:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        data = PoleInstallSerializer.denormalize(data)
        return PoleInstall(**data)
