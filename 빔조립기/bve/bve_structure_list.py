from resolver.beam_resolver import BeamResolver
from resolver.pole_resolver import PoleResolver

class BVEStrurctureList:
    @staticmethod
    def to_text():
        lines = [",; 커스텀 빔 목록 ====================="]
        for index, name in BeamResolver.index_dic.items():
            line = f".freeobj({index}) 동해선\\전차선\\월포정거장\\빔\\{name}.csv"
            lines.append(line)

        lines.append(",; 커스텀 기둥 목록 =====================")
        for index, name in PoleResolver.index_dic.items():
            line = f".freeobj({index}) 동해선\\전차선\\월포정거장\\기둥\\{name}.csv"
            lines.append(line)

        return "\n".join(lines)