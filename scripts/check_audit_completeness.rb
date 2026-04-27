#!/usr/bin/env ruby
# frozen_string_literal: true

# Audit log integrity check
# 驗證每張 status ∈ {done, failed, partial} 的 Task Card 都有對應的 AUDIT_LOG.md 條目。
#
# 邏輯：
#   1. 掃描 tasks/**/*.yaml（排除 TEMPLATE 與 examples/）
#   2. 對 status ∈ COMPLETION_STATUSES 的任務蒐集 task_id（需符合 TASK_ID_PATTERN）
#   3. 從 logs/AUDIT_LOG.md 抽出所有非空 task_id
#   4. 報告：完成但未記錄者（task → audit 缺漏）
#
# 反向（audit 有但 task 沒有）僅作為資訊輸出，不視為錯誤，避免歷史紀錄與目前 task 狀態
# 的小幅不一致造成 CI 噪音。
#
# exit 0 = 通過；exit 1 = 有缺漏

require 'yaml'

AUDIT_LOG_PATH = 'logs/AUDIT_LOG.md'
COMPLETION_STATUSES = %w[done failed partial].freeze
TASK_ID_PATTERN = /\A\d{8}-[A-Za-z]*\d+\z/
AUDIT_TASK_ID_REGEX = /task_id:\s*["']([^"']+)["']/

def collect_completed_task_ids(glob = 'tasks/**/*.yaml')
  result = []
  Dir.glob(glob).sort.each do |path|
    next if File.basename(path).include?('TEMPLATE')
    next if path.include?('/examples/')

    task = YAML.load_file(path)
    next unless task.is_a?(Hash)
    next unless COMPLETION_STATUSES.include?(task['status'])

    tid = task['task_id']
    next unless tid.is_a?(String) && tid.match?(TASK_ID_PATTERN)

    result << { task_id: tid, status: task['status'], path: path }
  end
  result
end

def collect_audit_log_task_ids(audit_path = AUDIT_LOG_PATH)
  return [] unless File.exist?(audit_path)

  content = File.read(audit_path, encoding: 'UTF-8')
  content.scan(AUDIT_TASK_ID_REGEX).flatten.uniq
end

if __FILE__ == $PROGRAM_NAME
  unless File.exist?(AUDIT_LOG_PATH)
    warn "FAILED: missing #{AUDIT_LOG_PATH}"
    exit 1
  end

  completed = collect_completed_task_ids
  audit_ids = collect_audit_log_task_ids
  missing = completed.reject { |t| audit_ids.include?(t[:task_id]) }

  puts 'Audit log integrity check:'
  puts "  Completed Task Cards (done/failed/partial): #{completed.length}"
  puts "  AUDIT_LOG entries (unique task_id):         #{audit_ids.length}"

  if missing.empty?
    puts 'OK: every completed Task Card has an AUDIT_LOG entry'
    exit 0
  end

  puts "FAILED: #{missing.length} Task Card(s) missing from AUDIT_LOG:"
  missing.each do |t|
    puts "  - #{t[:task_id]} (status=#{t[:status]}, file=#{t[:path]})"
  end
  exit 1
end
