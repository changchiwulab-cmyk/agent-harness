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

# --- evals / taxonomy lint 常數（M1 eval 架構 / M2 安全架構）---
ALLOWED_RUBRIC_SCOPE = %w[head full].freeze
REQUIRED_SEC_IDS = %w[SEC-01 SEC-02 SEC-03 SEC-04 SEC-05].freeze

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

# 7) evals/rubrics/*.yaml — rubric schema lint（M1 eval 架構）
Dir.glob('evals/rubrics/*.yaml').sort.each do |rf|
  doc = YAML.load_file(rf)
  rubric = doc.is_a?(Hash) ? doc['rubric'] : nil
  unless rubric.is_a?(Hash)
    errors << "#{rf}: top-level 'rubric' mapping required"
    next
  end
  errors << "#{rf}: invalid rubric.skill #{rubric['skill'].inspect}" unless ALLOWED_SKILL.include?(rubric['skill'])
  ac = rubric['auto_checks']
  if !ac.is_a?(Array) || ac.empty?
    errors << "#{rf}: rubric.auto_checks must be a non-empty list"
  else
    ac.each_with_index do |c, i|
      ok = c.is_a?(Hash) && !c['id'].to_s.strip.empty? &&
           c['any_markers'].is_a?(Array) && !c['any_markers'].empty? &&
           ALLOWED_RUBRIC_SCOPE.include?(c['scope'].to_s)
      errors << "#{rf}: auto_checks[#{i}] needs id + non-empty any_markers + scope(head/full)" unless ok
    end
  end
  jc = rubric['judge_checks']
  if jc.is_a?(Array)
    jc.each_with_index do |c, i|
      ok = c.is_a?(Hash) && !c['id'].to_s.strip.empty? && !c['desc'].to_s.strip.empty?
      errors << "#{rf}: judge_checks[#{i}] needs id + desc" unless ok
    end
  end
end

# 8) evals/rubrics 必須覆蓋全部 skill（M1）
existing_rubric_skills = Dir.glob('evals/rubrics/*.yaml').map { |p| File.basename(p, '.yaml') }
(ALLOWED_SKILL - existing_rubric_skills).each do |missing|
  errors << "evals/rubrics: missing rubric for skill '#{missing}'"
end

# 9) evals/regression/manifest.yaml — regression set lint（M1）
manifest = 'evals/regression/manifest.yaml'
if File.exist?(manifest)
  doc = YAML.load_file(manifest)
  rs = doc.is_a?(Hash) ? doc['regression_set'] : nil
  cases = rs.is_a?(Hash) ? rs['cases'] : nil
  if !cases.is_a?(Array) || cases.empty?
    errors << "#{manifest}: regression_set.cases must be a non-empty list"
  else
    cases.each_with_index do |c, i|
      unless c.is_a?(Hash)
        errors << "#{manifest}: cases[#{i}] must be mapping"
        next
      end
      errors << "#{manifest}: cases[#{i}] missing case_id" if c['case_id'].to_s.strip.empty?
      errors << "#{manifest}: cases[#{i}] invalid skill #{c['skill'].inspect}" unless ALLOWED_SKILL.include?(c['skill'])
      op = c['output_path']
      if op.to_s.strip.empty?
        errors << "#{manifest}: cases[#{i}] missing output_path"
      elsif !File.exist?(op)
        errors << "#{manifest}: cases[#{i}] output_path not found: #{op}"
      end
    end
  end
end

# 10) FAILURE_TAXONOMY.yaml — security 類枚舉與必填欄位（M2 安全架構）
taxonomy = 'system/FAILURE_TAXONOMY.yaml'
if File.exist?(taxonomy)
  doc = YAML.load_file(taxonomy)
  cats = doc.is_a?(Hash) ? doc['categories'] : nil
  sec = cats.is_a?(Hash) ? cats['security'] : nil
  if !sec.is_a?(Array) || sec.empty?
    errors << "#{taxonomy}: categories.security must be a non-empty list"
  else
    sec_ids = sec.map { |e| e.is_a?(Hash) ? e['id'] : nil }
    REQUIRED_SEC_IDS.each do |id|
      errors << "#{taxonomy}: missing security failure mode #{id}" unless sec_ids.include?(id)
    end
    sec.each do |e|
      next unless e.is_a?(Hash)

      %w[id name description mitigation].each do |f|
        errors << "#{taxonomy}: security #{e['id'] || '?'} missing #{f}" if e[f].to_s.strip.empty?
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
