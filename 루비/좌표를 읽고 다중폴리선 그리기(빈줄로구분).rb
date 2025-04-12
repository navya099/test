require 'csv'

def meters_to_inches(meters)
  inches_per_meter = 39.3701
  meters * inches_per_meter
end

def draw_polyline_from_csv(csv_path)
  # CSV 파일에서 좌표를 읽어옵니다.
  points = []
  File.foreach(csv_path) do |line|
    if line.strip.empty?
      # 빈 줄이 나타나면 지금까지 읽은 좌표들로 폴리라인을 그립니다.
      draw_polyline(points)
      points = []
    else
      # 각 줄에서 좌표를 읽어옵니다.
      x, y, z = line.split(',')
      points << Geom::Point3d.new(meters_to_inches(x.to_f), meters_to_inches(y.to_f), meters_to_inches(z.to_f))
    end
  end
end

def draw_polyline(points)
  # 폴리라인을 그립니다.
  Sketchup.active_model.entities.add_edges(points)
end

#코드 실행
draw_polyline_from_csv('c:/temp/coord.csv')