require 'csv'

def meters_to_inches(meters)
  inches_per_meter = 39.3701
  meters * inches_per_meter
end

def read_points_from_csv(csv_path)
  polylines = []
  points = []
  File.foreach(csv_path) do |line|
    if line.strip.empty?
      # 빈 줄이 나타나면 지금까지 읽은 좌표들로 폴리라인을 그리고, 컴포넌트를 배치합니다.
      polylines << points
      points = []
    else
      # 각 줄에서 좌표를 읽어옵니다.
      x, y, z = line.split(',')
      points << Geom::Point3d.new(meters_to_inches(x.to_f), meters_to_inches(y.to_f), meters_to_inches(z.to_f))
    end
  end

  # 마지막 폴리라인을 그리고, 컴포넌트를 배치합니다.
  polylines << points
  place_components(polylines)
end

def place_components(polylines)
  # 컴포넌트를 불러옵니다.
  component_definition = Sketchup.active_model.definitions.load('c:/temp/component.skp')

  # 각 폴리라인에 대해 컴포넌트를 배치하고 회전합니다.
  polylines.each do |points|
    # 좌표를 따라 폴리라인을 그립니다.
    draw_polyline(points)

    # 컴포넌트를 배치합니다.
    instances = []
    points[0..-2].each_with_index do |point, i|
      instance = Sketchup.active_model.entities.add_instance(component_definition, point)
      instances << instance

      # 컴포넌트를 회전합니다.
      if i < points.length - 1
        angle = get_angle(point, points[i+1])
        rotation = Geom::Transformation.rotation(point, [0, 0, 1], angle.degrees)
        instance.transform!(rotation)
      end
    end
  end
end

def get_angle(start, ending)
  dy = ending.y - start.y
  dx = ending.x - start.x

  angle1 = Math.atan2(dy, dx) * (180.0 / Math::PI)
  angle2 = angle1 - 90
  return angle2
end

def draw_polyline(points)
  # 폴리라인을 그립니다.
  Sketchup.active_model.entities.add_edges(points)
end

def draw_polylines_from_csv(csv_path)
  # CSV 파일에서 좌표를 읽어옵니다.
  read_points_from_csv(csv_path)
end

# 코드 실행
draw_polylines_from_csv('c:/temp/coord.csv')