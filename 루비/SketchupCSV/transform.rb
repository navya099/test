module SketchupCSV
    module Transform
        def self.swap_coordinate_system(group, is_swap)
            # Swap 매트릭스 정의
            swap_mat = Geom::Transformation.new([
                1, 0, 0, 0,
                0, 0, 1, 0,
                0, 1, 0, 0,
                0, 0, 0, 1
            ])
        
            # 그룹 안의 엔티티 가져오기
            entities = group.entities
        
            # 버텍스 전부 수정
            entities.grep(Sketchup::Face).each do |face|
                face.vertices.each do |vertex|
                    point = vertex.position
        
                    # is_swap일 경우, Y <-> Z 변환
                    if is_swap
                        point = Geom::Point3d.new(
                        point.x,
                        point.z,
                        point.y
                        )
                    end
        
                    # group 변환 매트릭스를 적용 (이건 optional: SketchUp은 기본 좌표계 기준이야)
                    vertex.position = point
                end
        
                # 면 노멀 뒤집기 (is_swap이면)
                if is_swap
                    face.reverse!
                end
            end
        
            # 전체 그룹에 swap_mat 적용 (transform!)
            if is_swap
                group.transform!(swap_mat)
            end
        end
    end
end
  