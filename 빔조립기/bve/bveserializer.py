class BVETextBuilder:

    @staticmethod
    def to_text(dto) -> str:

        text = ''

        text += f',;{dto.pole_number}\n'
        text += f'{dto.station}\n'
        text += ',;급전선지지설비\n'

        # 고정 오브젝트
        text += '.freeobj 0;1119;0;,;전주대용물1선\n'
        text += '.freeobj 1;1119;0;,;전주대용물1선\n'

        # ----------------
        # 기둥
        # ----------------
        text += ',;기둥\n'
        for pole in dto.poles:

            text += (
                f'.freeobj {pole.base_rail_index};{pole.obj_index};'
                f'{pole.xoffset};0;0;,;{pole.display_name}\n'
            )

        # ----------------
        # 빔
        # ----------------
        text += ',;빔\n'
        for beam in dto.beams:
            first_pole = dto.poles[0]
            text += (
                f'.freeobj 0;{beam.index};'
                f'{first_pole.xoffset};0;0;,;{beam.name}\n'
            )

        # ----------------
        # 브래킷
        # ----------------
        text += ',;브래킷\n'

        for rail in dto.rails:
            brackets = rail.brackets
            n = len(brackets)
            s = 1
            offs = BVETextBuilder.offsets(n, s)

            for i, br in enumerate(brackets):
                offset = offs[i]
                station = dto.station + offset

                text += f'{station}\n'
                text += f',;{rail.name}\n'
                text += (
                    f'.freeobj {br.rail_no};{br.index};'
                    f'{br.xoffset};{br.yoffset};{br.rotation};,;{br.type}\n'
                )

        return text

    @staticmethod
    def offsets(n, s):
        if n == 1:
            return [0.0]
        if n == 2:
            return [-s * 0.5, s * 0.5]
        return [(i - (n - 1) / 2) * s * 0.5 for i in range(n)]
