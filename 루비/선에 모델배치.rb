require 'sketchup.rb'

# 텍스트 파일에서 좌표를 읽어 배열로 반환하는 메소드
def read_coordinates(file_path)
  coordinates = []
  File.open(file_path, "r") do |file|
    file.each_line do |line|
      # x, y, z 값을 공백을 기준으로 분리하여 배열로 저장
      coords = line.split(',').map(&:to_f)
      coordinates << Geom::Point3d.new(coords[0].m, coords[1].m, coords[2].m) #미터 정상임
    end
  end
  coordinates
end

# yaw 계산: (현재좌표 x, y)와 다음좌표 x, y의 각도
def calculate_yaw(point1, point2)
  delta_x = point2.x - point1.x
  #puts "delta_x Units: #{delta_x}" # 미터로 출력됨
  
  delta_y = point2.y - point1.y # 미터로 계산됨
  #puts "delta_Y Units: #{delta_y}" # 미터로 계산됨
  #puts "point2.y (meters): #{point2.y}" # 미터 단위
  
  yaw = Math.atan2(delta_y, delta_x) # 라디안 단위
  #puts "yaw: #{yaw} (radians)"
  yaw
end


# pitch 계산: (현재좌표 y, z)와 다음좌표 y, z의 각도
def calculate_pitch(point1, point2)
  delta_y = point2.y - point1.y
  delta_z = point2.z - point1.z
  pitch = Math.atan2(delta_z, delta_y) # 라디안 단위
  pitch
end

# 메인 함수: 좌표를 읽고 선을 그린 후 컴포넌트를 배치
def create_path_with_components(file_path, component_definition)
  model = Sketchup.active_model
  entities = model.active_entities
  coordinates = read_coordinates(file_path)
  model = Sketchup.active_model
  units = model.options["UnitsOptions"]["LengthUnit"]
  puts "Model Units: #{units}"
  # 첫 번째 좌표부터 시작하여 선을 그리기
  coordinates.each_cons(2) do |point1, point2|
    # 선을 그리기
    line = entities.add_line(point1, point2)
    # 컴포넌트를 배치 (yaw, pitch에 맞게 회전)
    component_instance = entities.add_instance(component_definition, point1)
    yaw = calculate_yaw(point1, point2)
	pitch = calculate_pitch(point1, point2)
    # yaw (z축 회전)와 pitch (y축 회전) 적용
    transformation = Geom::Transformation.rotation(point1, Z_AXIS, yaw - Math::PI/2) # 90도를 빼야 올바르게 적용됨
    transformation *= Geom::Transformation.rotation(point1, X_AXIS, pitch) # 그대로
    
    component_instance.transform!(transformation) # 변환을 적용
  end
end


# 예시 사용법
file_path = "C:/temp/bve_coordinates.txt" # 파일 경로 수정
component_definition = Sketchup.active_model.definitions["자갈도상표준단면도 - 신선"] # 컴포넌트 정의 가져오기
create_path_with_components(file_path, component_definition)
