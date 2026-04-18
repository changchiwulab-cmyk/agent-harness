#!/usr/bin/env ruby
# frozen_string_literal: true

require 'yaml'
require 'date'

errors = []

ALLOWED_STATUS = %w[pending in_progress checkpoint review done failed].freeze
ALLOWED_RISK = %w[low medium high critical].freeze
ALLOWED_SKILL = %w[research writing ops review analysis].freeze
REQUIRED_FIELDS = %w[
  task_id
  date
  status
  goal
  definition_of_done
  expected_output
  risk_level
  approval_needed
  skill_type
].freeze
REQUIRED_OUTPUT_FIELDS = %w[format location filename].freeze
SKILL_POLICY_FILES = {
  'tasks/TASK_CARD_TEMPLATE.yaml' => /skill_type:\s*""\s*#\s*(.+)$/,
  'system/GATE_POLICY.yaml' => /skill_type 為有效值（(.+)）/,
  'system/EXECUTION_LOG_SCHEMA.yaml' => /skill_type:\s*""\s*#\s*(.+)$/
}.freeze

TOOLS_CATALOG_PATH = 'system/TOOLS_CATALOG.yaml'
COST_POLICY_PATH = 'system/COST_POLICY.md'
MODEL_REVIEW_MAX_AGE_DAYS = 7

TASK_ID_PATTERN = /\A\d{8}-[A-Za-z]*\d+\z/
DATE_PATTERN = /\A\d{4}-\d{2}-\d{2}\z/

def parse_iso_date(value)
  return value if value.is_a?(Date)
  return nil unless value.is_a?(String) && value.match?(DATE_PATTERN)

  Date.strptime(value, '%Y-%m-%d')
rescue ArgumentError
  nil
end

def extract_skill_values_from_text(path, pattern)
  text = File.read(path, encoding: 'UTF-8')
  match = text.match(pattern)
  return nil unless match

  match[1].split('/').map(&:strip).reject(&:empty?)
end


if __FILE__ == $PROGRAM_NAME

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

# 1.5) skill_type 允許值跨檔一致性檢查
skill_sets = {}
SKILL_POLICY_FILES.each do |path, pattern|
  unless File.exist?(path)
    errors << "missing skill policy file: #{path}"
    next
  end

  values = extract_skill_values_from_text(path, pattern)
  if values.nil? || values.empty?
    errors << "#{path}: failed to parse skill_type allowed values"
    next
  end
  skill_sets[path] = values.sort
end

unless skill_sets.empty?
  expected = ALLOWED_SKILL.sort
  skill_sets.each do |path, values|
    errors << "#{path}: skill_type set mismatch #{values.inspect} != #{expected.inspect}" unless values == expected
  end
end

# 2) Task Card schema 驗證（排除模板）
Dir.glob('tasks/**/*.yaml').sort.each do |task_file|
  next if File.basename(task_file).include?('TEMPLATE')

  task = YAML.load_file(task_file)
  unless task.is_a?(Hash)
    errors << "#{task_file}: root must be mapping"
    next
  end

  REQUIRED_FIELDS.each do |field|
    value = task[field]
    empty = value.nil? || (value.is_a?(String) && value.strip.empty?) || (value.respond_to?(:empty?) && value.empty?)
    errors << "#{task_file}: missing required field #{field}" if empty
  end


  if task.key?('task_id') && task['task_id'].is_a?(String) && !task['task_id'].match?(TASK_ID_PATTERN)
    errors << "#{task_file}: invalid task_id format #{task['task_id']} (expected YYYYMMDD-NNN or YYYYMMDD-XNNN)"
  end

  task_id_date = nil
  if task.key?('task_id') && task['task_id'].is_a?(String) && task['task_id'].match?(TASK_ID_PATTERN)
    y = task['task_id'][0, 4]
    m = task['task_id'][4, 2]
    d = task['task_id'][6, 2]
    task_id_date = parse_iso_date("#{y}-#{m}-#{d}")
    errors << "#{task_file}: invalid calendar date in task_id #{task['task_id']}" if task_id_date.nil?
  end

  task_date = nil
  if task.key?('date') && task['date'].is_a?(String)
    if !task['date'].match?(DATE_PATTERN)
      errors << "#{task_file}: invalid date format #{task['date']} (expected YYYY-MM-DD)"
    else
      task_date = parse_iso_date(task['date'])
      errors << "#{task_file}: invalid calendar date #{task['date']}" if task_date.nil?
    end
  end

  if task_id_date && task_date && task_id_date != task_date
    errors << "#{task_file}: task_id date does not match date field"
  end

  if task.key?('completion_time') && !task['completion_time'].to_s.strip.empty?
    completion_date = parse_iso_date(task['completion_time'])
    errors << "#{task_file}: invalid completion_time #{task['completion_time']} (expected valid YYYY-MM-DD)" if completion_date.nil?
  end

  if task.key?('status') && !ALLOWED_STATUS.include?(task['status'])
    errors << "#{task_file}: invalid status #{task['status']}"
  end


  if %w[done failed].include?(task['status']) && task['completion_time'].to_s.strip.empty?
    errors << "#{task_file}: completion_time is required when status is done/failed"
  end

  if task.key?('risk_level') && !ALLOWED_RISK.include?(task['risk_level'])
    errors << "#{task_file}: invalid risk_level #{task['risk_level']}"
  end

  if task.key?('skill_type') && !ALLOWED_SKILL.include?(task['skill_type'])
    errors << "#{task_file}: invalid skill_type #{task['skill_type']}"
  end

  if task.key?('approval_needed') && ![true, false].include?(task['approval_needed'])
    errors << "#{task_file}: approval_needed must be boolean"
  end

  if task['definition_of_done'].is_a?(Array)
    if task['definition_of_done'].empty? || task['definition_of_done'].any? { |item| !item.is_a?(String) || item.strip.empty? }
      errors << "#{task_file}: definition_of_done must be non-empty string array"
    end
  end

  if task['expected_output'].is_a?(Hash)
    REQUIRED_OUTPUT_FIELDS.each do |field|
      value = task['expected_output'][field]
      errors << "#{task_file}: missing expected_output.#{field}" if value.nil? || value.to_s.strip.empty?
    end
  end
end

# 2.5) allowed_tools 需在工具字典中
unless File.exist?(TOOLS_CATALOG_PATH)
  errors << "missing tools catalog: #{TOOLS_CATALOG_PATH}"
else
  catalog = YAML.load_file(TOOLS_CATALOG_PATH)
  tool_names = Array(catalog['tools']).filter_map { |t| t['name'] if t.is_a?(Hash) }.map(&:to_s).uniq
  if tool_names.empty?
    errors << "#{TOOLS_CATALOG_PATH}: tools list is empty or invalid"
  else
    Dir.glob('tasks/**/*.yaml').sort.each do |task_file|
      next if File.basename(task_file).include?('TEMPLATE')

      task = YAML.load_file(task_file)
      tools = Array(task['allowed_tools'])
      tools.each do |tool|
        next if tool_names.include?(tool)

        errors << "#{task_file}: allowed_tools includes unknown tool '#{tool}' (catalog: #{TOOLS_CATALOG_PATH})"
      end
    end
  end
end

# 3) 範例 Task Card 的 input_data / expected_output.location 路徑檢查
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

# 4) 模型治理 last_reviewed 檢查（避免策略過期）
if !File.exist?(COST_POLICY_PATH)
  errors << "missing cost policy: #{COST_POLICY_PATH}"
else
  policy_text = File.read(COST_POLICY_PATH, encoding: 'UTF-8')
  review_match = policy_text.match(/^last_reviewed:\s*(\d{4}-\d{2}-\d{2})\s*$/)
  if review_match.nil?
    errors << "#{COST_POLICY_PATH}: missing last_reviewed (YYYY-MM-DD)"
  else
    reviewed_on = parse_iso_date(review_match[1])
    if reviewed_on.nil?
      errors << "#{COST_POLICY_PATH}: invalid last_reviewed date #{review_match[1]}"
    else
      age_days = (Date.today - reviewed_on).to_i
      if age_days > MODEL_REVIEW_MAX_AGE_DAYS
        errors << "#{COST_POLICY_PATH}: last_reviewed is stale (#{age_days} days > #{MODEL_REVIEW_MAX_AGE_DAYS})"
      end
    end
  end
end

if errors.empty?
  puts 'OK: spec consistency checks passed'
  exit 0
end

puts 'FAILED: spec consistency checks found issues:'
errors.each { |e| puts "- #{e}" }
exit 1

end # if __FILE__ == $PROGRAM_NAME
