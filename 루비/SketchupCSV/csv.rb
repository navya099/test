require_relative 'logmodule'

module SketchupCSV 
  module CSV
    class CsvMesh
      attr_accessor :name,
                    :vertex_list,
                    :normals_list,
                    :use_add_face2,
                    :faces_list,
                    :diffuse_color,
                    :use_emissive_color,
                    :emissive_color,
                    :blend_mode,
                    :glow_half_distance,
                    :glow_attenuation_mode,
                    :daytime_texture_file,
                    :nighttime_texture_file,
                    :use_transparent_color,
                    :transparent_color,
                    :texcoords_list
  
      def initialize
        @name = ""
        @vertex_list = []         # Array of [x, y, z]
        @normals_list = []        # Array of [nx, ny, nz]
        @use_add_face2 = false
        @faces_list = []          # Array of [i0, i1, i2, ...]
        @diffuse_color = [255, 255, 255, 255]  # RGBA
        @use_emissive_color = false
        @emissive_color = [0, 0, 0]            # RGB
        @blend_mode = "Normal"
        @glow_half_distance = 0
        @glow_attenuation_mode = "DivideExponent4"
        @daytime_texture_file = ""
        @nighttime_texture_file = ""
        @use_transparent_color = false
        @transparent_color = [0, 0, 0]         # RGB
        @texcoords_list = []      # Array of [vertex_index, u, v]
      end
    end

    class CsvObject
      def is_potential_path(line)
        images = [".bmp", ".gi", ".jpg", ".jpeg", ".png"]

        images.each do |image|
          return true if line.index(image)
        end

        false
      end

      def create_cube(mesh, sx, sy, sz)
        v = mesh.vertex_list.length

        mesh.vertex_list << [sx, sy, -sz]
        mesh.vertex_list << [sx, -sy, -sz]
        mesh.vertex_list << [-sx, -sy, -sz]
        mesh.vertex_list << [-sx, sy, -sz]
        mesh.vertex_list << [sx, sy, sz]
        mesh.vertex_list << [sx, -sy, sz]
        mesh.vertex_list << [-sx, -sy, sz]
        mesh.vertex_list << [-sx, sy, sz]

        mesh.faces_list << [v + 0, v + 1, v + 2, v + 3]
        mesh.faces_list << [v + 0, v + 4, v + 5, v + 1]
        mesh.faces_list << [v + 0, v + 3, v + 7, v + 4]
        mesh.faces_list << [v + 6, v + 5, v + 4, v + 7]
        mesh.faces_list << [v + 6, v + 7, v + 3, v + 2]
        mesh.faces_list << [v + 6, v + 2, v + 1, v + 5]
      end

      def create_cylinder(mesh, n, r1, r2, h)
        # Parameters
        uppercap = r1 > 0.0
        lowercap = r2 > 0.0
        m = (uppercap ? 1 : 0) + (lowercap ? 1 : 0)
        r1 = r1.abs
        r2 = r2.abs

        # Initialization
        v = mesh.vertex_list.length
        d = 2.0 * Math::PI / n.to_f
        g = 0.5 * h
        t = 0.0

        # Vertices
        n.times do
          dx = Math.cos(t)
          dz = Math.sin(t)
          lx = dx * r2
          lz = dz * r2
          ux = dx * r1
          uz = dz * r1
          mesh.vertex_list << [ux, g, uz]
          mesh.vertex_list << [lx, -g, lz]
          t += d
        end

        # Side Faces
        n.times do |i|
          i0 = (2 * i + 2) % (2 * n)
          i1 = (2 * i + 3) % (2 * n)
          i2 = 2 * i + 1
          i3 = 2 * i
          mesh.faces_list << [v + i0, v + i1, v + i2, v + i3]
        end

        # Caps
        m.times do |i|
          face = []

          n.times do |j|
            if i == 0 && lowercap
              # Lower cap
              face << (v + 2 * j + 1)
            else
              # Upper cap
              face << (v + 2 * (n - j - 1))
            end
          end

          mesh.faces_list << face
        end
      end

      def apply_translation(mesh, x, y, z)
          mesh.vertex_list.each_with_index do |v, i|
            mesh.vertex_list[i] = [v[0] + x, v[1] + y, v[2] + z]
          end
      end
  
      def apply_scale(mesh, x, y, z)
        mesh.vertex_list.each_with_index do |v, i|
          mesh.vertex_list[i] = [v[0] * x, v[1] * y, v[2] * z]
        end

        if x * y * z < 0.0
          mesh.faces_list.each_with_index do |face, i|
            mesh.faces_list[i] = face.reverse
          end
        end
      end
  
      def apply_rotation(mesh, r, angle)
        cosine_of_angle = Math.cos(angle)
        sine_of_angle = Math.sin(angle)
        cosine_complement = 1.0 - cosine_of_angle

        mesh.vertex_list.each_with_index do |v, i|
          x = (cosine_of_angle + cosine_complement * r[0] * r[0]) * v[0] +
              (cosine_complement * r[0] * r[1] - sine_of_angle * r[2]) * v[1] +
              (cosine_complement * r[0] * r[2] + sine_of_angle * r[1]) * v[2]
          y = (cosine_of_angle + cosine_complement * r[1] * r[1]) * v[1] +
              (cosine_complement * r[0] * r[1] + sine_of_angle * r[2]) * v[0] +
              (cosine_complement * r[1] * r[2] - sine_of_angle * r[0]) * v[2]
          z = (cosine_of_angle + cosine_complement * r[2] * r[2]) * v[2] +
              (cosine_complement * r[0] * r[2] - sine_of_angle * r[1]) * v[0] +
              (cosine_complement * r[1] * r[2] + sine_of_angle * r[0]) * v[1]
          mesh.vertex_list[i] = [x, y, z]
        end
      end
  
      def apply_shear(mesh, d, s, r)
        mesh.vertex_list.each_with_index do |v, i|
          n = r * (d[0] * v[0] + d[1] * v[1] + d[2] * v[2])
          mesh.vertex_list[i] = [v[0] + s[0] * n, v[1] + s[1] * n, v[2] + s[2] * n]
        end
      end
  
      def apply_mirror(mesh, vx, vy, vz)
        mesh.vertex_list.each_with_index do |v, i|
          x = vx ? v[0] * -1.0 : v[0]
          y = vy ? v[1] * -1.0 : v[1]
          z = vz ? v[2] * -1.0 : v[2]
          mesh.vertex_list[i] = [x, y, z]
        end

        num_flips = [vx, vy, vz].count(true)

        if num_flips.odd?
          mesh.faces_list.each_with_index do |face, i|
            mesh.faces_list[i] = face.reverse
          end
        end
      end

      def normalize(v)
        norm = v[0] * v[0] + v[1] * v[1] + v[2] * v[2]

        return v if norm == 0.0

        factor = 1.0 / Math.sqrt(norm)
        [v[0] * factor, v[1] * factor, v[2] * factor]
      end
      

      def load_csv(option, file_path)
        meshes_list = []

        logger = Logger.new(STDOUT)
        logger.info("Loading file: #{file_path}")

        # Open CSV file
        begin
          binary = File.binread(file_path)
          detected = CharDet.detect(binary)
          encoding = detected['encoding'] || 'UTF-8'
          csv_text = binary.force_encoding(encoding).encode('UTF-8').lines.map(&:chomp)
        rescue => e
          logger.fatal(e)
          return meshes_list
        end

        # Parse CSV file
        comment_started = false

        csv_text.each_with_index do |line, i|
          # Strip OpenBVE original standard comments (;)
          j = line.index(";")
          if j
            csv_text[i] = line[0...j]
            line = csv_text[i]
          end
        
          # Strip double backslash comments (//)
          k = line.index("//")
          if k
            if is_potential_path(line)
              # HACK: Handles malformed potential paths (이미지를 경로로 오해한 경우는 무시)
              next
            end
            csv_text[i] = line[0...k]
            line = csv_text[i]
          end
        
          # Strip star-backslash comments (/* */)
          if !comment_started
            m = line.index("/*")
            if m
              comment_started = true
              part1 = line[0...m]
              part2 = ""
        
              n = line.index("*/")
              if n
                comment_started = false
                part2 = line[(n + 2)..-1]
              end
        
              csv_text[i] = part1 + part2
              line = csv_text[i]
            end
          else
            m = line.index("*/")
            if m
              comment_started = false
              if m + 2 != line.length
                csv_text[i] = line[(m + 2)..-1]
              else
                csv_text[i] = ""
              end
            else
              csv_text[i] = ""
            end
          end
        end
        # paser lines      
        mesh = nil
            

        csv_text.each_with_index do |line, i|
          # Collect arguments
          arguments = line.split(",").map(&:strip)
        
          command = arguments.shift  # Pop the first element and remove from array
        
          next if command.empty?
        
          # Parse terms
          case command.downcase
          when "createmeshbuilder"
            if arguments.any?
              logger.warn("0 arguments are expected in #{command} at line #{i + 1}")
            end
        
            if mesh
              meshes_list << mesh
            end
        
            mesh = CsvMesh.new
            
            if mesh.nil?
              logger.error("#{command} before the first CreateMeshBuilder are ignored at line #{i + 1}")
            end
        
          when "addvertex"
            if arguments.length > 6
              logger.warn("At most 6 arguments are expected in #{command} at line #{i + 1}")
            end
          
            begin
              vx = arguments[0].to_f
            rescue
              logger.error("Invalid argument vX in #{command} at line #{i + 1}")
              vx = 0.0
            end
          
            begin
              vy = arguments[1].to_f
            rescue
              logger.error("Invalid argument vY in #{command} at line #{i + 1}")
              vy = 0.0
            end
          
            begin
              vz = arguments[2].to_f
            rescue
              logger.error("Invalid argument vZ in #{command} at line #{i + 1}")
              vz = 0.0
            end
          
            if arguments.length >= 4
              logger.info("This add-on ignores nX, nY and nZ in #{command} at line #{i + 1}")
            end
          
            mesh.vertex_list << [vx, vy, vz]
    
          when "addface", "addface2"
            if arguments.length < 3
              logger.error("At least 3 arguments are required in #{command} at line #{i + 1}")
            else
              q = true
              a = []
          
              arguments.each_with_index do |arg, j|
                begin
                  a << arg.to_i
                rescue => ex
                  logger.error("v#{j} is invalid in #{command} at line #{i + 1}")
                  q = false
                  break
                end
          
                if a[j] < 0 || a[j] >= mesh.vertex_list.length
                  logger.error("v#{j} references a non-existing vertex in #{command} at line #{i + 1}")
                  q = false
                  break
                end
          
                if a[j] > 65535
                  logger.error("v#{j} indexes a vertex above 65535 which is not currently supported in #{command} at line #{i + 1}")
                  q = false
                  break
                end
              end
          
              if q
                mesh.faces_list << a
          
                if command.downcase == "addface2"
                  if option.use_split_add_face2
                    mesh.faces_list << a.reverse
                  else
                    mesh.use_add_face2 = true
                  end
                end
              end
            end

          when "cube"
            if arguments.length > 3
              logger.warning("At most 3 arguments are expected in #{command} at line #{i + 1}")
            end
          
            begin
              x = arguments[0].to_f
            rescue => ex
              if ex.is_a?(IndexError)
                x = 1.0
              else
                logger.error("Invalid argument HalfWidth in #{command} at line #{i + 1}")
                x = 1.0
              end
            end
          
            begin
              y = arguments[1].to_f
            rescue => ex
              if ex.is_a?(IndexError)
                y = 1.0
              else
                logger.error("Invalid argument HalfHeight in #{command} at line #{i + 1}")
                y = 1.0
              end
            end
          
            begin
              z = arguments[2].to_f
            rescue => ex
              if ex.is_a?(IndexError)
                z = 1.0
              else
                logger.error("Invalid argument HalfDepth in #{command} at line #{i + 1}")
                z = 1.0
              end
            end
          
            create_cube(mesh, x, y, z)

          when "cylinder"
            if arguments.length > 4
              logger.warning("At most 4 arguments are expected in #{command} at line #{i + 1}")
            end
          
            # Set default values
            n = 8
            r1 = 1.0
            r2 = 1.0
            h = 1.0
          
            # Parse n (integer)
            begin
              n = Integer(arguments[0])
            rescue StandardError => ex
              logger.error("Invalid argument n in #{command} at line #{i + 1}")
            end
          
            # Validate n
            if n < 2
              logger.error("n is expected to be at least 2 in #{command} at line #{i + 1}")
              n = 8
            end
          
            # Parse r1 (upper radius)
            begin
              r1 = Float(arguments[1])
            rescue StandardError => ex
              logger.error("Invalid argument UpperRadius in #{command} at line #{i + 1}")
            end
          
            # Parse r2 (lower radius)
            begin
              r2 = Float(arguments[2])
            rescue StandardError => ex
              logger.error("Invalid argument LowerRadius in #{command} at line #{i + 1}")
            end
          
            # Parse h (height)
            begin
              h = Float(arguments[3])
            rescue StandardError => ex
              logger.error("Invalid argument Height in #{command} at line #{i + 1}")
            end
          
            # Call the method to create the cylinder
            create_cylinder(mesh, n, r1, r2, h)
          
          when "translate" , "translateall"
            if arguments.length > 3
              logger.warning("At most 3 arguments are expected in #{command} at line #{i + 1}")
            end
          
            # Set default values
            x = 0.0
            y = 0.0
            z = 0.0
          
            # Parse x
            begin
              x = Float(arguments[0])
            rescue StandardError => ex
              logger.error("Invalid argument X in #{command} at line #{i + 1}")
            end
          
            # Parse y
            begin
              y = Float(arguments[1])
            rescue StandardError => ex
              logger.error("Invalid argument Y in #{command} at line #{i + 1}")
            end
          
            # Parse z
            begin
              z = Float(arguments[2])
            rescue StandardError => ex
              logger.error("Invalid argument Z in #{command} at line #{i + 1}")
            end
          
            # Apply translation to the current mesh
            apply_translation(mesh, x, y, z)
          
            # If TranslateAll, apply translation to all meshes
            if command.downcase == "translateall"
              meshes_list.each do |other_mesh|
                apply_translation(other_mesh, x, y, z)
              end
            end

          when "scale" , "scaleall"
            if arguments.length > 3
              logger.warning("At most 3 arguments are expected in #{command} at line #{i + 1}")
            end
          
            # Set default values
            x = 1.0
            y = 1.0
            z = 1.0
          
            # Parse x
            begin
              x = Float(arguments[0])
            rescue StandardError => ex
              logger.error("Invalid argument X in #{command} at line #{i + 1}")
            end
          
            # Ensure x is not zero
            if x == 0.0
              logger.error("X is required to be different from zero in #{command} at line #{i + 1}")
              x = 1.0
            end
          
            # Parse y
            begin
              y = Float(arguments[1])
            rescue StandardError => ex
              logger.error("Invalid argument Y in #{command} at line #{i + 1}")
            end
          
            # Ensure y is not zero
            if y == 0.0
              logger.error("Y is required to be different from zero in #{command} at line #{i + 1}")
              y = 1.0
            end
          
            # Parse z
            begin
              z = Float(arguments[2])
            rescue StandardError => ex
              logger.error("Invalid argument Z in #{command} at line #{i + 1}")
            end
          
            # Ensure z is not zero
            if z == 0.0
              logger.error("Z is required to be different from zero in #{command} at line #{i + 1}")
              z = 1.0
            end
          
            # Apply scaling to the current mesh
            apply_scale(mesh, x, y, z)
          
            # If ScaleAll, apply scaling to all meshes
            if command.downcase == "scaleall"
              meshes_list.each do |other_mesh|
                apply_scale(other_mesh, x, y, z)
              end
            end
            

          when  "rotate" , "rotateall"
            if arguments.length > 4
              logger.warning("At most 4 arguments are expected in #{command} at line #{i + 1}")
            end
          
            # Set default values
            rx = 0.0
            ry = 0.0
            rz = 0.0
            angle = 0.0
          
            # Parse rx
            begin
              rx = Float(arguments[0])
            rescue StandardError => ex
              logger.error("Invalid argument X in #{command} at line #{i + 1}")
            end
          
            # Parse ry
            begin
              ry = Float(arguments[1])
            rescue StandardError => ex
              logger.error("Invalid argument Y in #{command} at line #{i + 1}")
            end
          
            # Parse rz
            begin
              rz = Float(arguments[2])
            rescue StandardError => ex
              logger.error("Invalid argument Z in #{command} at line #{i + 1}")
            end
          
            # Parse angle
            begin
              angle = Float(arguments[3])
            rescue StandardError => ex
              logger.error("Invalid argument Angle in #{command} at line #{i + 1}")
            end
          
            # Calculate magnitude of rotation axis
            t = rx * rx + ry * ry + rz * rz
          
            # If the axis is zero, default to (0, 0, 1)
            if t == 0.0
              rz = 1.0
              ry = 0.0
              rx = 0.0
              t = 1.0
            end
          
            # If angle is non-zero, normalize axis and apply rotation
            if angle != 0.0
              t = 1.0 / Math.sqrt(t)
              rx *= t
              ry *= t
              rz *= t
              angle *= Math::PI / 180.0
          
              # Apply rotation to the current mesh
              apply_rotation(mesh, [rx, ry, rz], angle)
          
              # If RotateAll, apply rotation to all meshes
              if command.downcase == "rotateall"
                meshes_list.each do |other_mesh|
                  apply_rotation(other_mesh, [rx, ry, rz], angle)
                end
              end
            end
            

          when "shear" , "shearall"
            if arguments.length > 7
              logger.warning("At most 7 arguments are expected in #{command} at line #{i + 1}")
            end
          
            # Set default values
            dx = 0.0
            dy = 0.0
            dz = 0.0
            sx = 0.0
            sy = 0.0
            sz = 0.0
            r = 0.0
          
            # Parse dx
            begin
              dx = Float(arguments[0])
            rescue StandardError => ex
              logger.error("Invalid argument dX in #{command} at line #{i + 1}")
            end
          
            # Parse dy
            begin
              dy = Float(arguments[1])
            rescue StandardError => ex
              logger.error("Invalid argument dY in #{command} at line #{i + 1}")
            end
          
            # Parse dz
            begin
              dz = Float(arguments[2])
            rescue StandardError => ex
              logger.error("Invalid argument dZ in #{command} at line #{i + 1}")
            end
          
            # Parse sx
            begin
              sx = Float(arguments[3])
            rescue StandardError => ex
              logger.error("Invalid argument sX in #{command} at line #{i + 1}")
            end
          
            # Parse sy
            begin
              sy = Float(arguments[4])
            rescue StandardError => ex
              logger.error("Invalid argument sY in #{command} at line #{i + 1}")
            end
          
            # Parse sz
            begin
              sz = Float(arguments[5])
            rescue StandardError => ex
              logger.error("Invalid argument sZ in #{command} at line #{i + 1}")
            end
          
            # Parse r (ratio)
            begin
              r = Float(arguments[6])
            rescue StandardError => ex
              logger.error("Invalid argument Ratio in #{command} at line #{i + 1}")
            end
          
            # Normalize displacement and shear vectors
            d = normalize([dx, dy, dz])
            s = normalize([sx, sy, sz])
          
            # Apply shear to the current mesh
            apply_shear(mesh, d, s, r)
          
            # If ShearAll, apply shear to all meshes
            if command.downcase == "shearall"
              meshes_list.each do |other_mesh|
                apply_shear(other_mesh, d, s, r)
              end
            end

          when "mirror" , "mirrorall"
            if arguments.length > 6
              logger.warning("At most 6 arguments are expected in #{command} at line #{i + 1}")
            end
          
            # Set default values
            vx = 0.0
            vy = 0.0
            vz = 0.0
          
            # Parse vx
            begin
              vx = Float(arguments[0])
            rescue StandardError => ex
              logger.error("Invalid argument vX in #{command} at line #{i + 1}")
            end
          
            # Parse vy
            begin
              vy = Float(arguments[1])
            rescue StandardError => ex
              logger.error("Invalid argument vY in #{command} at line #{i + 1}")
            end
          
            # Parse vz
            begin
              vz = Float(arguments[2])
            rescue StandardError => ex
              logger.error("Invalid argument vZ in #{command} at line #{i + 1}")
            end
          
            # Log info if additional arguments are provided
            if arguments.length >= 4
              logger.info("This add-on ignores nX, nY, and nZ in #{command} at line #{i + 1}")
            end
          
            # Apply mirror transformation to the current mesh
            apply_mirror(mesh, vx != 0.0, vy != 0.0, vz != 0.0)
          
            # If MirrorAll, apply mirror to all meshes
            if command.downcase == "mirrorall"
              meshes_list.each do |other_mesh|
                apply_mirror(other_mesh, vx != 0.0, vy != 0.0, vz != 0.0)
              end
            end
            

          when "setcolor"
            if arguments.length > 4
              logger.warning("At most 4 arguments are expected in #{command} at line #{i + 1}")
            end
          
            # Set default values for colors
            red = 0
            green = 0
            blue = 0
            alpha = 0
          
            # Parse red value
            begin
              red = Integer(arguments[0])
            rescue StandardError => ex
              logger.error("Invalid argument Red in #{command} at line #{i + 1}")
            end
          
            # Validate red value
            if red < 0 || red > 255
              logger.error("Red is required to be within the range from 0 to 255 in #{command} at line #{i + 1}")
              red = red < 0 ? 0 : 255
            end
          
            # Parse green value
            begin
              green = Integer(arguments[1])
            rescue StandardError => ex
              logger.error("Invalid argument Green in #{command} at line #{i + 1}")
            end
          
            # Validate green value
            if green < 0 || green > 255
              logger.error("Green is required to be within the range from 0 to 255 in #{command} at line #{i + 1}")
              green = green < 0 ? 0 : 255
            end
          
            # Parse blue value
            begin
              blue = Integer(arguments[2])
            rescue StandardError => ex
              logger.error("Invalid argument Blue in #{command} at line #{i + 1}")
            end
          
            # Validate blue value
            if blue < 0 || blue > 255
              logger.error("Blue is required to be within the range from 0 to 255 in #{command} at line #{i + 1}")
              blue = blue < 0 ? 0 : 255
            end
          
            # Parse alpha value
            begin
              alpha = Integer(arguments[3])
            rescue StandardError => ex
              logger.error("Invalid argument Alpha in #{command} at line #{i + 1}")
            end
          
            # Validate alpha value
            if alpha < 0 || alpha > 255
              logger.error("Alpha is required to be within the range from 0 to 255 in #{command} at line #{i + 1}")
              alpha = alpha < 0 ? 0 : 255
            end
          
            # Set color to mesh
            mesh.diffuse_color = [red, green, blue, alpha]

          when "setemissivecolor"
            if arguments.length > 3
              logger.warning("At most 3 arguments are expected in #{command} at line #{i + 1}")
            end
          
            # Set default values for colors
            red = 0
            green = 0
            blue = 0
          
            # Parse red value
            begin
              red = Integer(arguments[0])
            rescue StandardError => ex
              logger.error("Invalid argument Red in #{command} at line #{i + 1}")
            end
          
            # Validate red value
            if red < 0 || red > 255
              logger.error("Red is required to be within the range from 0 to 255 in #{command} at line #{i + 1}")
              red = red < 0 ? 0 : 255
            end
          
            # Parse green value
            begin
              green = Integer(arguments[1])
            rescue StandardError => ex
              logger.error("Invalid argument Green in #{command} at line #{i + 1}")
            end
          
            # Validate green value
            if green < 0 || green > 255
              logger.error("Green is required to be within the range from 0 to 255 in #{command} at line #{i + 1}")
              green = green < 0 ? 0 : 255
            end
          
            # Parse blue value
            begin
              blue = Integer(arguments[2])
            rescue StandardError => ex
              logger.error("Invalid argument Blue in #{command} at line #{i + 1}")
            end
          
            # Validate blue value
            if blue < 0 || blue > 255
              logger.error("Blue is required to be within the range from 0 to 255 in #{command} at line #{i + 1}")
              blue = blue < 0 ? 0 : 255
            end
          
            # Set emissive color to mesh
            mesh.use_emissive_color = true
            mesh.emissive_color = [red, green, blue]
              
          when "setdecaltransparentcolor"
            if arguments.length > 3
              logger.warning("At most 3 arguments are expected in #{command} at line #{i + 1}")
            end
          
            # Set default values for colors
            red = 0
            green = 0
            blue = 0
          
            # Parse red value
            begin
              red = Integer(arguments[0])
            rescue StandardError => ex
              logger.error("Invalid argument Red in #{command} at line #{i + 1}")
            end
          
            # Validate red value
            if red < 0 || red > 255
              logger.error("Red is required to be within the range from 0 to 255 in #{command} at line #{i + 1}")
              red = red < 0 ? 0 : 255
            end
          
            # Parse green value
            begin
              green = Integer(arguments[1])
            rescue StandardError => ex
              logger.error("Invalid argument Green in #{command} at line #{i + 1}")
            end
          
            # Validate green value
            if green < 0 || green > 255
              logger.error("Green is required to be within the range from 0 to 255 in #{command} at line #{i + 1}")
              green = green < 0 ? 0 : 255
            end
          
            # Parse blue value
            begin
              blue = Integer(arguments[2])
            rescue StandardError => ex
              logger.error("Invalid argument Blue in #{command} at line #{i + 1}")
            end
          
            # Validate blue value
            if blue < 0 || blue > 255
              logger.error("Blue is required to be within the range from 0 to 255 in #{command} at line #{i + 1}")
              blue = blue < 0 ? 0 : 255
            end
          
            # Set transparent color to mesh
            mesh.use_transparent_color = true
            mesh.transparent_color = [red, green, blue]
          
            

          when "setblendmode" , "setblendingmode"
            if arguments.length > 3
              logger.warning("At most 3 arguments are expected in #{command} at line #{i + 1}")
            end
          
            # Set the blend mode based on the first argument
            begin
              case arguments[0].downcase
              when "normal"
                mesh.blend_mode = "Normal"
              when "additive", "glow"
                mesh.blend_mode = "Additive"
              else
                logger.error("The given BlendMode is not supported in #{command} at line #{i + 1}")
                mesh.blend_mode = "Normal"
              end
            rescue StandardError
              mesh.blend_mode = "Normal"
            end
          
            # Set the glow half distance
            begin
              mesh.glow_half_distance = Integer(arguments[1])
            rescue StandardError
              logger.error("Invalid argument GlowHalfDistance in #{command} at line #{i + 1}")
              mesh.glow_half_distance = 0
            end
          
            # Set the glow attenuation mode
            begin
              case arguments[2].downcase
              when "divideexponent2"
                mesh.glow_attenuation_mode = "DivideExponent2"
              when "divideexponent4"
                mesh.glow_attenuation_mode = "DivideExponent4"
              else
                logger.error("The given GlowAttenuationMode is not supported in #{command} at line #{i + 1}")
                mesh.glow_attenuation_mode = "DivideExponent4"
              end
            rescue StandardError
              mesh.glow_attenuation_mode = "DivideExponent4"
            end
            

          when "loadtexture"
            if arguments.length > 2
              logger.warning("At most 2 arguments are expected in #{command} at line #{i + 1}")
            end
          
            # Load the daytime texture
            begin
              mesh.daytime_texture_file = (Pathname.new(file_path) + ".." + arguments[0]).realpath.to_s
            rescue StandardError => ex
              logger.error("Invalid argument DaytimeTexture in #{command} at line #{i + 1}")
              mesh.daytime_texture_file = ""
            end
          
            # Load the nighttime texture
            begin
              mesh.nighttime_texture_file = (Pathname.new(file_path) + ".." + arguments[1]).realpath.to_s
            rescue StandardError => ex
              logger.error("Invalid argument NighttimeTexture in #{command} at line #{i + 1}")
              mesh.nighttime_texture_file = ""
            end
            
          when "settexturecoordinates"
            if arguments.length > 3
              logger.warning("At most 3 arguments are expected in #{command} at line #{i + 1}")
            end
          
            # Set the vertex index
            begin
              j = Integer(arguments[0])
            rescue StandardError => ex
              logger.error("Invalid argument VertexIndex in #{command} at line #{i + 1}")
              j = 0
            end
          
            # Set the X texture coordinate
            begin
              x = Float(arguments[1])
            rescue StandardError => ex
              logger.error("Invalid argument X in #{command} at line #{i + 1}")
              x = 0.0
            end
          
            # Set the Y texture coordinate
            begin
              y = Float(arguments[2])
            rescue StandardError => ex
              logger.error("Invalid argument Y in #{command} at line #{i + 1}")
              y = 0.0
            end
          
            # Checkif the vertex index is valid
            if j >= 0 && j < mesh.vertex_list.length
              mesh.texcoords_list << [j, x, y]
            else
              logger.error("VertexIndex references a non-existing vertex in #{command} at line #{i + 1}")
            end
            
          else
            logger.error("The command #{command} is not supported at line #{i + 1}")
          end
        end  

        # Finalize
        if mesh != nil
          meshes_list << mesh
        end

        return meshes_list
      end
    end
  end
end

