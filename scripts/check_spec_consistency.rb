#!/usr/bin/env ruby
# frozen_string_literal: true

require 'yaml'
require 'date'

errors = []

ALLOWED_STATUS = %w[pending in_progress checkpoint review done failed].freeze
ALLOWED_RISK = %w[low medium high critical].freeze
ALLOWED_SKILL = %w[research writing ops review analysis].freeze
# 與 system/validate_task_card.py 的 REQUIRED_FIELDS 同步；
# parity 由 scripts/test_check_spec_consistency.rb 在 CI 保證。
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
  allowed_tools
].freeze
REQUIRED_OUTPUT_FIELDS = %w[format location filename].freeze

TASK_ID_PATTERN = /\A\d{8}-[A-Za-z]*\d+\z/
DATE_PATTERN = /\A\d{4}-\d{2}-\d{2}\z/

# --- logs/ schema lint 常數（R2: 20260529-005）---
ALLOWED_RUN_STATUS = %w[completed failed partial cancelled].freeze
REQUIRED_RUN_FIELDS = %w[run_id task_id status gate_results].freeze
ALLOWED_APPROVAL_METHOD = %w[human_confirm draft_first].freeze
ALLOWED_APPROVAL_STATUS = %w[approved rejected superseded].freeze
REQUIRED_APPROVAL_FIELDS = %w[approval_id task_id date action approval_method status approved_by].freeze
ALLOWED_ERROR_TYPE = %w[tool_failure rule_violation schema_failure timeout unknown].freeze

def parse_iso_date(value)
  return value if value.is_a?(Date)
  return nil unless value.is_a?(String) && value.match?(DATE_PATTERN)

  Date.strptime(value, '%Y-%m-%d')
rescue ArgumentError
  nil
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

  if task.key?('allowed_tools') && !task['allowed_tools'].is_a?(Array)
    errors << "#{task_file}: allowed_tools must be an array"
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

# 4) logs/runs/*.yaml — execution log schema（R2: 20260529-005）
Dir.glob('logs/runs/*.yaml').sort.each do |run_file|
  doc = YAML.load_file(run_file)
  unless doc.is_a?(Hash)
    errors << "#{run_file}: root must be mapping"
    next
  end
  log = doc['execution_log'].is_a?(Hash) ? doc['execution_log'] : doc
  REQUIRED_RUN_FIELDS.each do |field|
    value = log[field]
    empty = value.nil? || (value.is_a?(String) && value.strip.empty?) || (value.respond_to?(:empty?) && value.empty?)
    errors << "#{run_file}: missing required field #{field}" if empty
  end
  if log.key?('status') && !ALLOWED_RUN_STATUS.include?(log['status'])
    errors << "#{run_file}: invalid run status #{log['status']} (allowed: #{ALLOWED_RUN_STATUS.join('/')})"
  end
end

# 5) logs/approvals/*.yaml — approval record schema（R2；跳過 TEMPLATE）
Dir.glob('logs/approvals/*.yaml').sort.each do |appr_file|
  next if File.basename(appr_file).include?('TEMPLATE')

  doc = YAML.load_file(appr_file)
  records = (doc.is_a?(Hash) && doc['approval_records'].is_a?(Array)) ? doc['approval_records'] : nil
  if records.nil?
    errors << "#{appr_file}: must contain an 'approval_records' list"
    next
  end
  errors << "#{appr_file}: 'approval_records' must not be empty" if records.empty?
  records.each_with_index do |rec, i|
    unless rec.is_a?(Hash)
      errors << "#{appr_file}: approval_records[#{i}] must be mapping"
      next
    end
    REQUIRED_APPROVAL_FIELDS.each do |field|
      value = rec[field]
      empty = value.nil? || (value.is_a?(String) && value.strip.empty?)
      errors << "#{appr_file}: approval_records[#{i}] missing #{field}" if empty
    end
    if rec.key?('approval_method') && !ALLOWED_APPROVAL_METHOD.include?(rec['approval_method'])
      errors << "#{appr_file}: approval_records[#{i}] invalid approval_method #{rec['approval_method']}"
    end
    if rec.key?('status') && !ALLOWED_APPROVAL_STATUS.include?(rec['status'])
      errors << "#{appr_file}: approval_records[#{i}] invalid status #{rec['status']}"
    end
  end
end

# 6) logs/errors/*.md — error_type 枚舉（R2；抽 yaml 區塊，跳過 TEMPLATE）
Dir.glob('logs/errors/*.md').sort.each do |err_file|
  next if File.basename(err_file).include?('TEMPLATE')

  content = File.read(err_file, encoding: 'UTF-8')
  m = content.match(/```yaml\n(.*?)```/m)
  unless m
    errors << "#{err_file}: no ```yaml block found"
    next
  end
  begin
    block = YAML.load(m[1])
  rescue StandardError => e
    errors << "#{err_file}: yaml block parse error: #{e.message}"
    next
  end
  unless block.is_a?(Hash)
    errors << "#{err_file}: yaml block must be a mapping"
    next
  end
  etype = block['error_type']
  if etype.nil? || etype.to_s.strip.empty?
    errors << "#{err_file}: missing error_type"
  elsif !ALLOWED_ERROR_TYPE.include?(etype)
    errors << "#{err_file}: invalid error_type #{etype} (allowed: #{ALLOWED_ERROR_TYPE.join('/')})"
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
