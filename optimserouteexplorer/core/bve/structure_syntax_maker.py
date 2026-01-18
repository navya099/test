from Structure.bridge import Bridge
from Structure.structurecollection import StructureCollection
from Structure.tunnel import Tunnel
from core.bve.commnd_genmerator import BVECommandGenerator


class BVEStructureSyntaxMaker:
    @staticmethod
    def create_structure_syntax(structure_collection: StructureCollection) -> list[str]:
        output = []
        for structure in structure_collection:
            if isinstance(structure, Tunnel):
                output.extend(BVEStructureSyntaxMaker.create_tunnel_syntax(structure))
            elif isinstance(structure, Bridge):
                output.extend(BVEStructureSyntaxMaker.create_bridge_syntax(structure))
        return output

    @staticmethod
    def create_bridge_syntax(structure) -> list[str]:
        return [
            f',;{structure.name}',
            BVECommandGenerator.make_command(structure.startsta, 'wall', 0, -1, 28),
            BVECommandGenerator.make_command(structure.startsta, 'dikeend', 0),
            BVECommandGenerator.make_command(structure.endsta, 'wallend', 0),
            BVECommandGenerator.make_command(structure.endsta, 'dike', 0, 0, 32),
            ""  # 구조물 간 빈 줄
        ]
    @staticmethod
    def create_tunnel_syntax(structure) -> list[str]:
        return [
            f',;{structure.name}',
            BVECommandGenerator.make_command(structure.startsta, 'wall', 0, -1, 51),
            BVECommandGenerator.make_command(structure.startsta, 'dikeend', 0),
            BVECommandGenerator.make_command(structure.endsta, 'wallend', 0),
            BVECommandGenerator.make_command(structure.endsta, 'dike', 0, 0, 32),
            ""  # 구조물 간 빈 줄
        ]