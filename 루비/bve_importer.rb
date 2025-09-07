require 'sketchup.rb'
require 'uri'

module BVE
  module Importer

    class Vertex
      attr_accessor :x, :y, :z
      def initialize(x, y, z)
        @x, @y, @z = x, y, z
      end

      def to_point
        Geom::Point3d.new(@x.m, @z.m, @y.m) # BVE(X,Z,Y) -> SU(X,Y,Z)
      end
    end

    class FaceData
      attr_accessor :vertex_indices, :double_sided, :uv_coords, :material
      def initialize(vertex_indices, double_sided=false)
        @vertex_indices = vertex_indices
        @double_sided = double_sided
        @uv_coords = {} # {vertex_index => [u,v]}
        @material = nil
      end
    end

    class MeshBuilder
      attr_accessor :vertices, :faces, :material
      def initialize
        @vertices = []
        @faces = []
        @material = nil
      end
    end

    class ObjectParser
      attr_reader :meshes
      def initialize
        @meshes = []
        @current_mesh = nil
        @current_face = nil
      end

      def safe_path(path)
        path.encode("UTF-8")
      end

      def parse_file(filepath)
        @csv_dir = File.dirname(filepath)
        File.foreach(filepath).with_index do |line,i|
          stripped = line.strip
          next if stripped.empty? || stripped.start_with?(';')
          begin
            parse_line(stripped)
          rescue => e
            puts "[Line #{i+1}] Error: #{e.message}"
          end
        end
      end

      def parse_line(line)
        tokens = line.split(',').map(&:strip)
        return if tokens.empty?
        command = tokens[0]

        case command
        when "CreateMeshBuilder"
          @current_mesh = MeshBuilder.new
          @meshes << @current_mesh
        when "AddVertex"
          coords = tokens[1..3].map(&:to_f)
          @current_mesh.vertices << Vertex.new(*coords)
        when "AddFace"
          indices = tokens[1..].map(&:to_i)
          @current_face = FaceData.new(indices, false)
          @current_mesh.faces << @current_face
        when "AddFace2"
          indices = tokens[1..].map(&:to_i)
          @current_face = FaceData.new(indices, true)
          @current_mesh.faces << @current_face
        when "SetColor"
          r, g, b, a = tokens[1..4].map(&:to_i)
          mat_name = "Color_#{r}_#{g}_#{b}"
          mat = Sketchup.active_model.materials[mat_name] || Sketchup.active_model.materials.add(mat_name)
          mat.color = Sketchup::Color.new(r,g,b,a)
          @current_face&.material = mat
          @current_mesh.material ||= mat
        when "SetColorAll"
          r, g, b, a = tokens[1..4].map(&:to_i)
          mat_name = "Color_#{r}_#{g}_#{b}"
          mat = Sketchup.active_model.materials[mat_name] || Sketchup.active_model.materials.add(mat_name)
          mat.color = Sketchup::Color.new(r,g,b,a)
          @meshes.each {|mesh| mesh.material = mat}
        when "LoadTexture"
          texture_file = tokens[1]
          full_path = File.join(@csv_dir, texture_file)
          if File.exist?(full_path)
            safe_full_path = safe_path(full_path)
            mat_name = File.basename(texture_file, ".*")
            mat = Sketchup.active_model.materials[mat_name] || Sketchup.active_model.materials.add(mat_name)
            mat.texture = safe_full_path
            mat.alpha = 1.0
            @current_face&.material = mat
            @current_mesh.material ||= mat
            puts "[LoadTexture] 재질 생성 완료: #{mat_name} -> #{safe_full_path}"
          else
            puts "[LoadTexture] 파일 없음: #{full_path}"
          end
        when "SetTextureCoordinates"
          if @current_face
            idx = tokens[1].to_i
            u,v = tokens[2..3].map(&:to_f)
            @current_face.uv_coords[idx] = [u,v]
          end
        end
      end
    end

    def self.import_bve_object
      filepath = UI.openpanel("Open BVE .b3d File", "", "BVE Object (*.csv)|*.csv||")
      return unless filepath

      start_time = Time.now
      parser = ObjectParser.new
      parser.parse_file(filepath)

      model = Sketchup.active_model
      entities = model.active_entities

      model.start_operation("Import BVE Object", true)
      total_meshes = parser.meshes.size
      total_faces = 0
      skipped_faces = 0

      parser.meshes.each_with_index do |mesh, mesh_idx|
        group = entities.add_group
        mesh_entities = group.entities
        points = mesh.vertices.map(&:to_point)

        mesh.faces.each_with_index do |face, face_idx|
          begin
            face_points = face.vertex_indices.map {|i| points[i]}
            skp_face = mesh_entities.add_face(face_points.reverse)
            if skp_face.nil?
              skipped_faces += 1
              puts "[Mesh #{mesh_idx}, Face #{face_idx}] Face 생성 실패: #{face.vertex_indices.inspect}"
              next
            end

            skp_face.reverse! if skp_face.normal.z < 0

            # Material 적용 우선순위: Face > Mesh > 기본 흰색
            material_to_apply = face.material || mesh.material
            if material_to_apply
              skp_face.material = material_to_apply
              skp_face.back_material = material_to_apply if face.double_sided
              puts "[Mesh #{mesh_idx}, Face #{face_idx}] 재질 적용 완료: #{material_to_apply.name}"
            else
              puts "[Mesh #{mesh_idx}, Face #{face_idx}] 재질 없음, 기본 흰색 적용"
            end

            # UV 좌표 적용
            unless face.uv_coords.empty?
              uv_helper = skp_face.get_UVHelper(true, true, 0)
              face.vertex_indices.each do |vi|
                if face.uv_coords[vi]
                  u,v = face.uv_coords[vi]
                  pt = points[vi]
                  uv_helper.set_front_uv(pt.to_point, [u,v])
                end
              end
            end

            total_faces += 1
          rescue => e
            skipped_faces += 1
            puts "[Mesh #{mesh_idx}, Face #{face_idx}] 예외 발생: #{e.message}"
          end
        end
      end

      model.commit_operation

      elapsed = Time.now - start_time
      UI.messagebox("✅ Import complete: #{total_meshes} mesh(es), #{total_faces} face(s) 생성 완료.\n" +
                    "#{skipped_faces} face(s) 생성 실패.\n" +
                    "소요 시간: #{elapsed.round(2)}초")
      puts "=== BVE Import Summary ==="
      puts "Meshes: #{total_meshes}, Faces created: #{total_faces}, Faces skipped: #{skipped_faces}"
      puts "Elapsed time: #{elapsed.round(2)} seconds"
    end

    unless file_loaded?(__FILE__)
      UI.menu("Plugins").add_item("Import BVE Object (.csv)") {
        self.import_bve_object
      }
      file_loaded(__FILE__)
    end

  end
end
