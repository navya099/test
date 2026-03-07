class BVETextBuilder:

    @staticmethod
    def to_text(dto) -> str:

        text = ''

        text += f',;{dto.pole_number}\n'
        text += f'{dto.station}\n'
        # ----------------
        # 기둥
        # ----------------

        for pole in dto.poles:
            if pole:
                text += ',;기둥\n'
                text += (
                    f'.freeobj {pole.base_rail_index};{pole.obj_index};'
                    f'{pole.xoffset};0;0;,;{pole.display_name}\n'
                )
                # 기초
                if pole and pole.base and pole.base.name and pole.base.name != '없음':
                    text += ',;기초\n'
                    text += (
                        f'.freeobj {pole.base_rail_index};{pole.base.index};'
                        f'{pole.xoffset};0;0;,;{pole.base.name}\n'
                    )

        # ----------------
        # 빔
        # ----------------

        for beam in dto.beams:
            if beam:
                text += ',;빔\n'
                text += (
                    f'.freeobj {beam.ref_start_pole.base_rail_index};{beam.index};'
                    f'{beam.ref_start_pole.xoffset};0;0;,;{beam.name}\n'
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
                # --- 브래킷 하위 피팅들 ---
                for f in getattr(br, "fittings", []):  # 호환성 위해 getattr 사용
                    if f:
                        text += ',;브래킷 금구류\n'
                        text += (
                            f'.freeobj {br.rail_no};{f.index};'
                            f'{f.xoffset};{f.yoffset};{f.rotation};,;{f.label}\n'
                        )

        #장비
        text += ',;기타설비\n'
        text += f'{dto.station}\n'
        for eq in dto.equips:
            text += (
                f'.freeobj {eq.base_rail_index};{eq.objindex};{eq.xoffset};{eq.yoffset};{eq.rotation};,;{eq.name}\n'
            )

        return text

    @staticmethod
    def offsets(n, s):
        if n == 1:
            return [0.0]
        if n == 2:
            return [-s * 0.5, s * 0.5]
        return [(i - (n - 1) / 2) * s * 0.5 for i in range(n)]
