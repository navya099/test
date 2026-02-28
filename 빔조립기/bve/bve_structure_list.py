from resolver.beam_resolver import BeamResolver


class BVEStrurctureList:
    @staticmethod
    def to_text():
        lines = [",; 커스텀 빔 목록 ====================="]
        for index, name in BeamResolver.index_dic.items():
            line = f".freeobj({index}) 동해선\\전차선\\월포정거장\\빔\\custom_beam_{name}m.csv"
            lines.append(line)
        return "\n".join(lines)