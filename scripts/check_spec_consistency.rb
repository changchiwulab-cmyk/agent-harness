#!/usr/bin/env ruby
# frozen_string_literal: true

require 'yaml'

errors = []

# 1) README 宣告的重要目錄是否存在
required_dirs = [
  'logs/runs',
  'logs/approvals',
  'logs/errors',
  'outputs/drafts',
  'outputs/reports',
  'memory/active_projects'
]

required_dirs.each do |dir|
  errors << "missing directory: #{dir}" unless Dir.exist?(dir)
end

# 2) 範例 Task Card 的 input_data 路徑是否存在（僅檢查 repo 內相對路徑）
Dir.glob('tasks/examples/*.yaml').sort.each do |task_file|
  task = YAML.load_file(task_file)

  Array(task['input_data']).each do |path|
    next unless path.is_a?(String)
    next if path.start_with?('http://', 'https://')

    errors << "#{task_file}: missing input_data path #{path}" unless File.exist?(path)
  end

  location = task.dig('expected_output', 'location')
  if location.is_a?(String) && !location.empty?
    errors << "#{task_file}: missing expected_output.location directory #{location}" unless Dir.exist?(location)
  end
end

if errors.empty?
  puts 'OK: spec consistency checks passed'
  exit 0
end

puts 'FAILED: spec consistency checks found issues:'
errors.each { |e| puts "- #{e}" }
exit 1
