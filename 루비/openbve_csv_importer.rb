require 'sketchup.rb'
require 'extensions.rb'

module SketchupCSV
	module Main
  
	  EXTENSION_NAME = "OPENBVE Import CSV"
	  EXTENSION_VERSION = "1.0.0"
	  EXTENSION_CREATOR = "dger"
	  EXTENSION_DESCRIPTION = "OPENBVE Import CSV"
  
	  def self.load_extension
		filepath = File.dirname(__FILE__)
		filepath.force_encoding("UTF-8") if filepath.respond_to?(:force_encoding)
		loader = File.join(filepath, "SketchupCSV", "loader.rb")
  
		extension = SketchupExtension.new(EXTENSION_NAME, loader)
		extension.description = EXTENSION_DESCRIPTION
		extension.version = EXTENSION_VERSION
		extension.creator = EXTENSION_CREATOR
		extension.copyright = ""
  
		Sketchup.register_extension(extension, true)
	  	end
  
	end
end
  
SketchupCSV::Main.load_extension
  