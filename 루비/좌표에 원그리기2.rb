def draw_circle(center)
  radius = 10.0 # 미터 단위의 반지름
  segments = 24 # 원을 구성하는 선분의 개수

  # 중심점을 인치 단위로 변환합니다.
  center_in_inches = meters_to_inches(center)

  # 원을 그립니다.
  circle = Sketchup.active_model.entities.add_circle(center_in_inches, [0, 0, 1], radius, segments)
  face = Sketchup.active_model.entities.add_face(circle)
  face.pushpull(-10) # 깊이를 설정합니다.
end

def meters_to_inches(meters)
  inches_per_meter = 39.3701
  if meters.is_a?(Numeric)
    return meters * inches_per_meter
  elsif meters.is_a?(Geom::Point3d)
    return Geom::Point3d.new(meters.x * inches_per_meter, meters.y * inches_per_meter, meters.z * inches_per_meter)
  end
end

# 사용자로부터 점 좌표를 입력받습니다.
input = UI.inputbox(['X,Y,Z'], ['0,0,0'], 'Enter center point coordinates')
center = Geom::Point3d.new(input.first.split(',').map(&:to_f))

# 입력받은 좌표를 중심으로 하는 원을 그립니다.
draw_circle(center)