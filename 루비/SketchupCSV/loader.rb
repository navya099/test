require 'sketchup.rb'
require_relative 'import_csv.rb'
require_relative 'csv.rb'

module SketchupCSV
  module Loader

    def self.load_importer
      cmdImport = UI::Command.new("OpenBVE Importer") {
        file_path = UI.openpanel("Select CSV File", "", "CSV Files|*.csv||")
        if file_path && File.extname(file_path) == ".csv"
            begin
                csv_object = SketchupCSV::CSV::CsvObject.new
                csv_object.load_csv(file_path)
            rescue => e
                UI.messagebox("Error loading CSV: #{e.message}")
            end
          else
            UI.messagebox("Invalid file. Please select a CSV file.")
          end
      }
      cmdImport.tooltip = "Import OpenBVE CSV"

      menu = UI.menu("Plugins").add_submenu("OpenBVE Import CSV")
      menu.add_item(cmdImport)
    end

  end
end

# 마지막에 호출
SketchupCSV::Loader.load_importer
