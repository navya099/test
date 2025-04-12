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

# CSV 파일을 읽어서 데이터를 처리하는 코드를 작성한다.
CSV.foreach(csv_file_path) do |row|
  # 첫 열의 값이 'AddVertex'인 경우에 대한 처리 로직을 구현한다.
  if row[0] == 'AddVertex'
    # 해당 줄에서 열값이 비어있으면 그 열은 배열에 넣지않는다.
    unless row[1..-1].all?(&:nil?)
      # 해당 줄의 공백을 모두 제거한다.
      row.map! { |data| data&.gsub(/\s+/, '') }
      
      # 2열부터 값을 새로운 배열에 추가한다.
      add_vertex_values = row[1..-1].map { |data| data.nil? ? nil : data.to_f }

      # 배열을 add_vertex_arrays에 추가한다.
      add_vertex_arrays.push(add_vertex_values)
    end
  elsif row[0] == 'AddFace'
    # 해당 줄에서 열값이 비어있으면 그 열은 배열에 넣지않는다.
    unless row[1..-1].all?(&:nil?)
      # 해당 줄의 공백을 모두 제거한다.
      row.map! { |data| data&.gsub(/\s+/, '') }

      # 2열부터 값을 새로운 배열에 추가한다.
      add_face_values = row[1..-1].map { |data| data.nil? ? nil : data.to_i }

      # 배열을 add_face_arrays에 추가한다.
      add_face_arrays.push(add_face_values)
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

# 배열의 내용을 출력한다.
add_vertex_arrays.each_with_index do |values, index|
  #puts "AddVertex_#{index + 1} = #{values}"
end


add_face_arrays.each_with_index do |values, index|
  #puts "AddFace_#{index + 1} = #{values}"
end

# 스케치업에서 점을 생성하고 point 배열에 추가한다.
point_array = []
add_vertex_arrays.each do |vertex|
  x = vertex[0].to_f
  z = vertex[2].to_f
  y = vertex[1].to_f

  point = Geom::Point3d.new(meters_to_inches(x, z, y))
  point_array.push(point)
end

# point 배열의 내용을 출력한다.
point_array.each_with_index do |point, index|
  #puts "Point_#{index + 1}: #{point}"
end

# add_face_arrays 배열을 사용하여 삼각형을 생성하고 스케치업에 그린다.
model = Sketchup.active_model
entities = model.active_entities

# add_face_arrays 배열을 사용하여 삼각형을 생성한다.
# 1. add_face_arrays배열을 flatten하여 1차원배열로 만들기
point = add_face_arrays.flatten.map { |index| point_array[index] }

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
  else
    puts "Failed to create face."
  end
end

# 엔티티들을 그룹으로 묶습니다.
group = model.active_entities.add_group(entities.to_a)