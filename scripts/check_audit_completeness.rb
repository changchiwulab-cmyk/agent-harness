#!/usr/bin/env ruby
# frozen_string_literal: true

# Audit Completeness Check
# 依據：deep-research-report-2.md P0「audit completeness as merge gate」
#
# 規則：tasks/*.yaml 中 status=done|failed 的每一張 Task Card，
# 在 logs/AUDIT_LOG.md 必須有對應的 task_id 紀錄；缺漏即 fail。
#
# exit 0 = 全部對齊；exit 1 = 有缺漏（列出 task_id）

require 'yaml'

TERMINAL_STATUSES = %w[done failed].freeze
DEFAULT_TASKS_GLOB = 'tasks/**/*.yaml'
DEFAULT_AUDIT_LOG = 'logs/AUDIT_LOG.md'

def collect_terminal_task_ids(glob)
  ids = []
  Dir.glob(glob).sort.each do |task_file|
    next if File.basename(task_file).include?('TEMPLATE')
    next if task_file.include?('archived/') || task_file.include?('examples/')

    task = YAML.load_file(task_file)
    next unless task.is_a?(Hash)
    next unless TERMINAL_STATUSES.include?(task['status'])
    next if task['task_id'].nil? || task['task_id'].to_s.strip.empty?

    ids << { task_id: task['task_id'].to_s, file: task_file, status: task['status'] }
  end
  ids
end

def extract_audit_task_ids(audit_path)
  return [] unless File.exist?(audit_path)

  ids = []
  File.read(audit_path, encoding: 'UTF-8').each_line do |line|
    if (m = line.match(/^\s*-?\s*task_id:\s*"([^"]+)"\s*$/))
      ids << m[1]
    end
  end
  ids.reject { |id| id.empty? }
end

def find_missing(task_records, audit_ids)
  audit_set = audit_ids.to_set if audit_ids.respond_to?(:to_set)
  audit_set ||= audit_ids.uniq
  task_records.reject { |r| audit_set.include?(r[:task_id]) }
end

if __FILE__ == $PROGRAM_NAME
  require 'set'

  task_records = collect_terminal_task_ids(DEFAULT_TASKS_GLOB)
  audit_ids = extract_audit_task_ids(DEFAULT_AUDIT_LOG)
  missing = find_missing(task_records, audit_ids.to_set)

  total = task_records.length
  audited = total - missing.length

  puts "Audit completeness: #{audited}/#{total}"

  if missing.empty?
    puts 'OK: all terminal-status tasks have audit entries'
    exit 0
  end

  puts 'FAILED: terminal-status tasks missing from AUDIT_LOG.md:'
  missing.each do |r|
    puts "- #{r[:task_id]} (status=#{r[:status]}) from #{r[:file]}"
  end
  exit 1
end
