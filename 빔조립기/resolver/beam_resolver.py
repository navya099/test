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

            # 길이 계산 (X축 기준)
            start_x = start.base_rail.coord.x + start.xoffset
            end_x = end.base_rail.coord.x + end.xoffset
            beam.length = end_x - start_x
            beam.length_m = round(beam.length, 3)

            beam.iscustom = not beam.length_m.is_integer()
            name = BeamNameBuilder.build(beam)
            beam.name = name

            # 인덱스 조회
            index = idxlib.get_index(name)
            if index is None:
                # 이미 같은 이름이 등록되어 있으면 기존 인덱스 재사용
                existing = [k for k, v in BeamResolver.index_dic.items() if v == name]
                if existing:
                    index = existing[0]
                else:
                    while BeamResolver.next_index in BeamResolver.indexes:
                        BeamResolver.next_index += 1
                    index = BeamResolver.next_index
                    BeamResolver.index_dic[index] = name  # ✅ beam.name 저장
                    BeamResolver.indexes.add(index)
                    BeamResolver.next_index += 1

            beam.index = index
            beam.ref_start_pole = start
            beam.ref_end_pole = end
