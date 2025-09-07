require 'sketchup.rb'
require 'uri'

module BVE
  module Importer

    class Vertex
      attr_accessor :x, :y, :z
      def initialize(x, y, z)
        @x, @y, @z = x, y, z
      end
      # 원본 좌표 그대로 SketchUp에 사용
      def to_point
        Geom::Point3d.new(@x.m, @y.m, @z.m) 
      end
    end

    class FaceData
      attr_accessor :vertex_indices, :double_sided, :uv_coords, :material, :line_number, :line_text
      def initialize(vertex_indices, double_sided=false)
        @vertex_indices = vertex_indices
        @double_sided = double_sided
        @uv_coords = {}
        @material = nil
        @line_number = nil
        @line_text = nil
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

      def parse_file(filepath)
        @csv_dir = File.dirname(filepath)
        File.foreach(filepath).with_index do |line, i|
          stripped = line.strip
          next if stripped.empty? || stripped.start_with?(';')
          begin
            parse_line(stripped, i+1)
          rescue => e
            puts "[Line #{i+1}] Error: #{e.message} | Text: #{line}"
          end
        end
      end

      def parse_line(line, line_number)
        tokens = line.split(',').map(&:strip)
        return if tokens.empty?
        cmd = tokens[0]

        case cmd
        when "CreateMeshBuilder"
          @current_mesh = MeshBuilder.new
          @meshes << @current_mesh
        when "AddVertex"
          coords = tokens[1..3].map(&:to_f)
          @current_mesh.vertices << Vertex.new(*coords)
        when "AddFace"
          indices = tokens[1..].map(&:to_i)
          face = FaceData.new(indices)
          face.line_number = line_number
          face.line_text = line
          @current_mesh.faces << face
        when "AddFace2"
          indices = tokens[1..].map(&:to_i)
          face = FaceData.new(indices, true)
          face.line_number = line_number
          face.line_text = line
          @current_mesh.faces << face
        when "SetColor"
          r, g, b, a = tokens[1..4].map(&:to_i)
          mat = BVE::Importer.material_cache(r, g, b, a)
          @current_face&.material = mat
          @current_mesh.material ||= mat
        when "SetColorAll"
          r, g, b, a = tokens[1..4].map(&:to_i)
          mat = BVE::Importer.material_cache(r, g, b, a)
          @meshes.each {|mesh| mesh.material = mat}
        when "LoadTexture"
          texture_file = tokens[1]
          full_path = File.join(@csv_dir, texture_file)
          if File.exist?(full_path)
            mat_name = File.basename(texture_file, ".*")
            mat = Sketchup.active_model.materials[mat_name] || Sketchup.active_model.materials.add(mat_name)
            mat.texture = full_path.encode("UTF-8")
            mat.alpha = 1.0
            @current_face&.material = mat
            @current_mesh.material ||= mat
          end
        when "SetTextureCoordinates"
          if @current_face
            idx = tokens[1].to_i
            u, v = tokens[2..3].map(&:to_f)
            @current_face.uv_coords[idx] = [u, v]
          end
        end
      end
    end

    # Material 캐시
    def self.material_cache(r, g, b, a)
      @material_cache ||= {}
      key = "#{r}_#{g}_#{b}_#{a}"
      return @material_cache[key] if @material_cache[key]

      mat_name = "Color_#{r}_#{g}_#{b}"
      mat = Sketchup.active_model.materials[mat_name] || Sketchup.active_model.materials.add(mat_name)
      mat.color = Sketchup::Color.new(r, g, b, a)
      @material_cache[key] = mat
      mat
    end

    def self.import_bve_object
      filepath = UI.openpanel("Open BVE .CSV File", "", "BVE Object (*.csv)|*.csv||")
      return unless filepath

      start_time = Time.now
      parser = ObjectParser.new
      parser.parse_file(filepath)

      model = Sketchup.active_model
      entities = model.active_entities

      model.start_operation("Import BVE Object", true)
      total_faces = 0
      skipped_faces = 0

      parser.meshes.each_with_index do |mesh, mesh_idx|
        group = entities.add_group
        mesh_entities = group.entities
        points = mesh.vertices.map(&:to_point)

        mesh.faces.each_with_index do |face, face_idx|
          begin
            face_points = face.vertex_indices.map {|i| points[i]}
            skp_face = mesh_entities.add_face(face_points)
            next if skp_face.nil?

            # Material 적용
            mat = face.material || mesh.material
            if mat
              skp_face.material = mat
              skp_face.back_material = mat if face.double_sided
            end

            # UVHelper 최소화
            unless face.uv_coords.empty?
              uv_helper = skp_face.get_UVHelper(true, true, 0)
              face.vertex_indices.each do |vi|
                if uv = face.uv_coords[vi]
                  uv_helper.set_front_uv(points[vi].to_point, uv)
                end
              end
            end

            total_faces += 1
          rescue => e
            skipped_faces += 1
            puts "[Mesh #{mesh_idx}, Face #{face_idx}] 예외 발생: #{e.message}"
          end
        end

        # 전체 그룹에 축 스왑 적용: 예) Y↔Z
        trans = Geom::Transformation.scaling(1) *
                Geom::Transformation.new([0,0,0]) # 단순 YZ 교환 구현 가능
        # 실제로 Y↔Z 스왑하려면 아래와 같이 변환
       # 올바른 코드 (16개 값 나열)
      mat_swap = Geom::Transformation.new([
        1,0,0,0,
        0,0,1,0,
        0,1,0,0,
        0,0,0,1
      ])
        group.transform!(mat_swap)
      end

      model.commit_operation
      elapsed = Time.now - start_time

      UI.messagebox("✅ Import complete: #{parser.meshes.size} mesh(es), #{total_faces} face(s) 생성 완료.\n" +
                    "#{skipped_faces} face(s) 생성 실패.\n" +
                    "소요 시간: #{elapsed.round(2)}초")
      puts "=== BVE Import Summary ==="
      puts "Meshes: #{parser.meshes.size}, Faces created: #{total_faces}, Faces skipped: #{skipped_faces}"
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