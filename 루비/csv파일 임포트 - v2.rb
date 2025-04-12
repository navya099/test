require 'csv'

# CSV 파일 경로를 UI.openpanel을 사용하여 얻어온다.
csv_file_path = UI.openpanel('CSV 파일 선택', '', 'CSV 파일 (*.csv)|*.csv||')

def meters_to_inches(x, y, z)
  inches_per_meter = 39.37
  x_inches = x * inches_per_meter
  y_inches = y * inches_per_meter
  z_inches = z * inches_per_meter
  [x_inches, y_inches, z_inches]
end


# 파일이 선택되지 않았을 경우에 대한 예외 처리
if csv_file_path.nil?
  UI.messagebox('CSV 파일이 선택되지 않았습니다.')
  return
end

# AddVertex 데이터를 저장할 배열
add_vertex_arrays = []
# AddFace 데이터를 저장할 배열
add_face_arrays = []
# SetTextureCoordinates 데이터를 저장할 배열
texture_coord_arrays = []

blocks = []
block = []

CSV.foreach(csv_file_path) do |row|
  # CreateMeshBuilder줄을 기준으로 각 블록을 분리합니다.
        if row[0] == 'CreateMeshBuilder'
              unless block.empty?
				blocks.push(block)
				block = []
			end
		else
             block.push(row)
		end
end
unless block.empty?
  blocks.push(block)
end

# 중복 코드를 함수로 추출
def process_data_row(row, data_arrays)
  unless row[1..-1].all?(&:nil?)
    row.map! { |data| data&.gsub(/\s+/, '') }
    values = row[1..-1].map { |data| data.nil? ? nil : data.to_f }
    data_arrays.push(values)
  end
end



blocks.each do |block|
  block.each do |row|
    case row[0]
    when 'AddVertex'
      process_data_row(row, add_vertex_arrays)
    when 'AddFace'
      process_data_row(row, add_face_arrays)
    when 'LoadTexture'
      unless row[1..-1].all?(&:nil?)
        row.map! { |data| data&.gsub(/\s+/, '') }
        texture_filename = row[1]
        
        # 텍스처 파일 경로 생성 및 확인
        texture_path = File.join(File.dirname(csv_file_path), texture_filename)
        if File.exist?(texture_path)
          model = Sketchup.active_model
          materials = model.materials
          material = materials.add(texture_filename)
          material.texture = texture_path
        else
          UI.messagebox("텍스처 파일을 찾을 수 없습니다: #{texture_path}")
        end
      end
    when 'SetTextureCoordinates'
      process_data_row(row, texture_coord_arrays)
    end
  end
end

# 배열 내부에서 문자열 "nil"을 nil 값으로 바꾼다.
add_vertex_arrays.map! do |values|
  values.map { |value| value == "nil" ? nil : value }
end
add_face_arrays.map! do |values|
  values.map { |value| value == "nil" ? nil : value }
end

# 이제 배열에서 nil 값을 제거할 수 있습니다.
add_vertex_arrays.each_with_index do |values, index|
  add_vertex_arrays[index].compact!
end
add_face_arrays.each_with_index do |values, index|
  add_face_arrays[index].compact!
end

# 스케치업에서 점을 생성하고 point 배열에 추가한다.
point_array = []
add_vertex_arrays.each do |vertex|
  x = vertex[0].to_f
  z = vertex[2].to_f
  y = vertex[1].to_f

  point = Geom::Point3d.new(meters_to_inches(x, z, y))
  point_array.push(point)


# add_face_arrays 배열을 사용하여 삼각형을 생성하고 스케치업에 그린다.
model = Sketchup.active_model
entities = model.active_entities

# 2.add_face_index의 값으로 point_array 인덱스에서 값 가져오기.
add_face_arrays.each do |indices|
  # 인덱스에 해당하는 점을 가져옵니다.
  point1 = point_array[indices[0]]
  point2 = point_array[indices[1]]
  point3 = point_array[indices[2]]

  # 삼각형을 생성한다.
  triangle = [point1, point2, point3]
  

  # 삼각형을 스케치업에 그린다.
  face_entity = entities.add_face(triangle)
  if face_entity
    face_entity.reverse! if face_entity.normal.z < 0
    #면에 텍스쳐를 적용한다.
	 # texture_coord_arrays 배열에서 텍스쳐 좌표를 추출한다.
     material = face_entity.material
     if material.nil?
       material = model.materials.add
       face_entity.material = material
     end
	
	
	texture_coords = texture_coord_arrays.shift
    
    # 텍스쳐 좌표를 적용한다.
	
    face_entity.position_material(material, [point1, point2, point3], texture_coords)
  else
	
    puts "Failed to create face."
  end
  group = entities.add_group(face_entity)
end  
end
