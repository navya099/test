require 'csv'

def meters_to_inches(meters)
  inches_per_meter = 39.3701
  meters * inches_per_meter
end

def draw_polyline_from_csv(csv_path)
  # CSV 파일에서 좌표를 읽어옵니다.
  points = read_points_from_csv(csv_path)

  # 좌표 단위를 미터에서 인치로 변환합니다.
  points = points.map { |point| Geom::Point3d.new(meters_to_inches(point.x), meters_to_inches(point.y), meters_to_inches(point.z)) }

  # 좌표를 따라 폴리라인을 그립니다.
  draw_polyline(points)
end

def read_points_from_csv(csv_path)
  points = []
  CSV.foreach(csv_path) do |row|
    # CSV 파일에서 좌표를 읽어옵니다. 각 행은 x, y, z 좌표를 갖습니다.
    point = Geom::Point3d.new(row[0].to_f, row[1].to_f, row[2].to_f)
    points << point
  end
  return points
end

def draw_polyline(points)
  # 폴리라인을 그립니다.
  Sketchup.active_model.entities.add_edges(points)
end

#코드 실행
draw_polyline_from_csv('c:/temp/coord.csv')