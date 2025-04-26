# 개발용 리로드 스크립트

module SketchupCSV
    module DevLoader
  
      # SketchupCSV 폴더 경로 지정
      PLUGIN_DIR = File.join(
        Sketchup.find_support_file("Plugins"), "SketchupCSV"
      )
  
      def self.reload
        # 모든 .rb 파일을 다시 load
        Dir.glob(File.join(PLUGIN_DIR, "**", "*.rb")).each do |file|
          begin
            load file
          rescue => e
            UI.messagebox("Error loading #{file}:\n#{e.message}")
          end
        end
        UI.messagebox("SketchupCSV 플러그인 리로드 완료!")
      end
  
    end
  end
  
  # SketchUp 메뉴에 등록
  unless file_loaded?(__FILE__)
    UI.menu("Plugins").add_item("Reload SketchupCSV") {
      SketchupCSV::DevLoader.reload
    }
    file_loaded(__FILE__)
  end
  