from utils.beamnamer import BeamNameBuilder
class BeamResolver:
    index_dic = {}
    indexes = set()
    next_index = 1502

    @staticmethod
    def resolve(beams, idxlib, rail_map, pole_map):
        for beam in beams:
            start = pole_map[beam.start_pole]
            end = pole_map[beam.end_pole]

            # 2D 평면 X좌표 기준 길이 계산
            start_x = start.base_rail.coord.x + start.xoffset
            end_x = end.base_rail.coord.x + end.xoffset
            beam.length = end_x - start_x
            beam.length_m = round(beam.length, 3)

            beam.iscustom = not beam.length_m.is_integer()
            name = BeamNameBuilder.build(beam)
            beam.name = name
            index = idxlib.get_index(name)
            if index is None:
                while BeamResolver.next_index in BeamResolver.indexes:
                    BeamResolver.next_index += 1
                index = BeamResolver.next_index
                BeamResolver.index_dic[index] = beam.length_m
                BeamResolver.indexes.add(index)
                BeamResolver.next_index += 1
            beam.index = index
            beam.ref_start_pole = start
            beam.ref_end_pole = end
