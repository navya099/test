require_relative 'transform'
require_relative 'csv'
require_relative 'logmodule'

module SketchupCSV
    module ImportCSV
        class ImportCSV
            INV255 = 1.0 / 255.0

            def initialize
                @file_path = ""
                @option = CSV::ImportOption.new
            end

            def import_model(file_path)
                @file_path = file_path
                meshes_list = SketchupCSV::CSV::CsvObject.new.load_csv(@option, file_path)

                UI.messagebox("Loaded meshes: #{meshes_list.length}")

                model = Sketchup.active_model
                entities = model.active_entities

                obj_base_name = File.basename(@file_path, ".*")

                meshes_list.each_with_index do |csv_mesh, i|
                group = entities.add_group
                group.name = "#{obj_base_name} - #{i}"
                group_entities = group.entities

                # Vertex 등록
                vertices = csv_mesh.vertex_list.map do |v|
                    Geom::Point3d.new(v[0], v[1], v[2])
                end

                # Face 생성
                csv_mesh.faces_list.each do |face_indices|
                    begin
                    face_vertices = face_indices.map { |idx| vertices[idx] }
                    group_entities.add_face(face_vertices)
                    rescue => e
                    UI.messagebox("Failed to create face: #{e}")
                    end
                end

                # Transform 처리 (좌표계 변환)
                Transform.swap_coordinate_system(group, @option.use_transform_coords)

                # Material 및 Texture 처리
                create_material(csv_mesh, group)

                # 추가 속성 설정 (emissive, transparent 등)
                set_custom_properties(group, csv_mesh)
                end
            end

            def create_material(csv_mesh, group)
                model = Sketchup.active_model
                materials = model.materials

                mat_name = if csv_mesh.daytime_texture_file != ""
                File.basename(csv_mesh.daytime_texture_file, ".*")
                else
                group.name
                end

                material = materials[mat_name] || materials.add(mat_name)

                # Diffuse 색상 설정
                color = Sketchup::Color.new(
                (csv_mesh.diffuse_color[0] * INV255 * 255).to_i,
                (csv_mesh.diffuse_color[1] * INV255 * 255).to_i,
                (csv_mesh.diffuse_color[2] * INV255 * 255).to_i,
                (csv_mesh.diffuse_color[3] * INV255 * 255).to_i
                )
                material.color = color

                # 텍스처가 있다면 텍스처도 설정
                if csv_mesh.daytime_texture_file != ""
                material.texture = csv_mesh.daytime_texture_file
                end

                group.material = material
            end

            def set_custom_properties(group, csv_mesh)
                group.set_attribute("CSV", "use_emissive_color", csv_mesh.use_emissive_color)
                group.set_attribute("CSV", "emissive_color", [
                csv_mesh.emissive_color[0] * INV255,
                csv_mesh.emissive_color[1] * INV255,
                csv_mesh.emissive_color[2] * INV255
                ])
                group.set_attribute("CSV", "blend_mode", csv_mesh.blend_mode)
                group.set_attribute("CSV", "glow_half_distance", csv_mesh.glow_half_distance)
                group.set_attribute("CSV", "glow_attenuation_mode", csv_mesh.glow_attenuation_mode)
                group.set_attribute("CSV", "use_transparent_color", csv_mesh.use_transparent_color)
                group.set_attribute("CSV", "transparent_color", [
                csv_mesh.transparent_color[0] * INV255,
                csv_mesh.transparent_color[1] * INV255,
                csv_mesh.transparent_color[2] * INV255
                ])
            end
        end
    end
end
