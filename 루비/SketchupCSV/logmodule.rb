# logger_setup.rb
require 'logger'

# 전역 로거 설정
$logger = Logger.new(STDOUT)
$logger.level = Logger::INFO
