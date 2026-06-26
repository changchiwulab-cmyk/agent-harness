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

TASK_ID_PATTERN = /\A\d{8}-[A-Za-z]*\d+\z/
DATE_PATTERN = /\A\d{4}-\d{2}-\d{2}\z/

# --- logs/ schema lint 常數（R2: 20260529-005）---
ALLOWED_RUN_STATUS = %w[completed failed partial cancelled].freeze
REQUIRED_RUN_FIELDS = %w[run_id task_id status gate_results].freeze
ALLOWED_APPROVAL_METHOD = %w[human_confirm draft_first].freeze
ALLOWED_APPROVAL_STATUS = %w[approved rejected superseded].freeze
REQUIRED_APPROVAL_FIELDS = %w[approval_id task_id date action approval_method status approved_by].freeze
ALLOWED_ERROR_TYPE = %w[tool_failure rule_violation schema_failure timeout unknown].freeze

# --- v2.1 治理層硬化：信任邊界 + eval harness schema 常數 ---
REQUIRED_SEC_IDS = %w[SEC-05 SEC-06 SEC-07].freeze
ALLOWED_RUBRIC_CHECK_TYPES = %w[required_heading required_regex forbidden_regex heading_order heading_nonempty].freeze
RUBRIC_CHECK_REQUIRED_FIELDS = {
  'required_heading' => %w[token],
  'heading_nonempty' => %w[token],
  'required_regex' => %w[pattern],
  'forbidden_regex' => %w[pattern],
  'heading_order' => %w[before after]
}.freeze

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

# 7) system/TRUST_BOUNDARY.yaml — 信任邊界 schema（v2.1）
tb_path = 'system/TRUST_BOUNDARY.yaml'
if File.exist?(tb_path)
  tb = YAML.load_file(tb_path)
  if tb.is_a?(Hash)
    tiers = tb['trust_tiers']
    if tiers.is_a?(Hash)
      %w[trusted semi_trusted untrusted].each do |t|
        ok = tiers[t].is_a?(Hash) && tiers[t]['sources'].is_a?(Array) && !tiers[t]['sources'].empty?
        errors << "#{tb_path}: trust_tiers.#{t} must have non-empty sources" unless ok
      end
    else
      errors << "#{tb_path}: missing trust_tiers mapping"
    end
    unless tb['core_rules'].is_a?(Array) && !tb['core_rules'].empty?
      errors << "#{tb_path}: core_rules must be a non-empty list"
    end
    unless tb.dig('lethal_trifecta', 'legs', 'exfiltration_vector', 'status')
      errors << "#{tb_path}: missing lethal_trifecta.legs.exfiltration_vector.status"
    end
  else
    errors << "#{tb_path}: root must be mapping"
  end
else
  errors << "missing file: #{tb_path}"
end

# 8) system/FAILURE_TAXONOMY.yaml — 必含注入模式 SEC-05~07（v2.1）
ft_path = 'system/FAILURE_TAXONOMY.yaml'
if File.exist?(ft_path)
  ft = YAML.load_file(ft_path)
  sec = ft.is_a?(Hash) ? ft.dig('categories', 'security') : nil
  if sec.is_a?(Array)
    ids = sec.map { |item| item.is_a?(Hash) ? item['id'] : nil }
    REQUIRED_SEC_IDS.each do |sid|
      errors << "#{ft_path}: missing #{sid} in security taxonomy" unless ids.include?(sid)
    end
  else
    errors << "#{ft_path}: categories.security must be a list"
  end
end

# 9) skills/*/rubric.yaml — eval rubric schema（v2.1）
Dir.glob('skills/*/rubric.yaml').sort.each do |rb_file|
  rb = YAML.load_file(rb_file)
  unless rb.is_a?(Hash)
    errors << "#{rb_file}: root must be mapping"
    next
  end
  errors << "#{rb_file}: missing skill" if rb['skill'].to_s.strip.empty?
  pt = rb['pass_threshold']
  unless pt.is_a?(Numeric) && pt >= 0 && pt <= 1
    errors << "#{rb_file}: pass_threshold must be a number in [0,1]"
  end
  checks = rb['checks']
  if checks.is_a?(Array) && !checks.empty?
    checks.each_with_index do |c, i|
      unless c.is_a?(Hash)
        errors << "#{rb_file}: checks[#{i}] must be mapping"
        next
      end
      errors << "#{rb_file}: checks[#{i}] missing id" if c['id'].to_s.strip.empty?
      ctype = c['type']
      if ALLOWED_RUBRIC_CHECK_TYPES.include?(ctype)
        # 依 type 驗必填參數，避免 malformed check 在 runtime 被靜默當失敗
        required = RUBRIC_CHECK_REQUIRED_FIELDS[ctype] || []
        required.each do |fld|
          if c[fld].nil? || c[fld].to_s.strip.empty?
            errors << "#{rb_file}: checks[#{i}] type #{ctype} missing '#{fld}'"
          end
        end
      else
        errors << "#{rb_file}: checks[#{i}] invalid type #{ctype} (allowed: #{ALLOWED_RUBRIC_CHECK_TYPES.join('/')})"
      end
    end
  else
    errors << "#{rb_file}: checks must be a non-empty list"
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
