require 'sketchup.rb'

module BVE
  module Importer

    class Vertex
      attr_accessor :x, :y, :z

      def initialize(x, y, z)
        @x = x
        @y = y
        @z = z
      end

      def to_point
        Geom::Point3d.new(@x, @y, @z)
      end
    end

    class FaceData
      attr_accessor :vertex_indices, :double_sided

      def initialize(vertex_indices, double_sided = false)
        @vertex_indices = vertex_indices
        @double_sided = double_sided
      end
    end

    class MeshBuilder
      attr_accessor :vertices, :faces, :color

      def initialize
        @vertices = []
        @faces = []
        @color = nil
      end
    end

    class ObjectParser
      attr_reader :meshes

      def initialize
        @meshes = []
        @current_mesh = nil
      end

      def parse_file(filepath)
        File.foreach(filepath).with_index do |line, i|
          stripped = line.strip
          next if stripped.empty? || stripped.start_with?(';')

          begin
            parse_line(stripped)
          rescue => e
            puts "[Line #{i + 1}] Error: #{e.message}"
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
          @current_mesh.faces << FaceData.new(indices, false)
        when "AddFace2"
          indices = tokens[1..].map(&:to_i)
          @current_mesh.faces << FaceData.new(indices, true)
        when "SetColor"
          r, g, b, a = tokens[1..4].map(&:to_i)
          @current_mesh.color = Sketchup::Color.new(r, g, b, a)
        when "SetColorAll"
          r, g, b, a = tokens[1..4].map(&:to_i)
          color = Sketchup::Color.new(r, g, b, a)
          @meshes.each do |mesh|
            mesh.color = color
          end
        else
          # 기타 명령 무시
        end
      end
    end

    def self.import_bve_object
      filepath = UI.openpanel("Open BVE .b3d File", "", "BVE Object (*.csv)|*.csv||")
      return unless filepath

      parser = ObjectParser.new
      parser.parse_file(filepath)
      model = Sketchup.active_model
      entities = model.active_entities

      parser.meshes.each_with_index do |mesh, idx|
        group = entities.add_group
        mesh_entities = group.entities

        points = mesh.vertices.map(&:to_point)

        mesh.faces.each do |face|
          begin
            face_points = face.vertex_indices.map { |i| points[i] }
            skp_face = mesh_entities.add_face(face_points)

            if mesh.color
              skp_face.material = mesh.color
              skp_face.back_material = mesh.color if face.double_sided
            end
          rescue => e
            puts "Failed to create face: #{e.message}"
          end
        end
      end

      UI.messagebox("✅ Import complete: #{parser.meshes.size} mesh(es) created.")
    end

    unless file_loaded?(__FILE__)
      UI.menu("Plugins").add_item("Import BVE Object (.csv)") {
        self.import_bve_object
      }
      file_loaded(__FILE__)
    end

  end
end
