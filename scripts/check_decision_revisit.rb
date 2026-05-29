#!/usr/bin/env ruby
# frozen_string_literal: true
#
# Decision revisit tracker (R4: Task Card 20260529-007)
#
# 唯讀報告工具：掃描 memory/active_projects/**/decisions/*.yaml，列出每筆決策的
# status 與 revisit_trigger；對「可量化」的觸發（並行任務數 / logs/runs 累積數 /
# 原生重疊度 %）比對當前值並標記 DUE / OK；無法量化者標 MANUAL（待 RETRO 人工判斷）。
#
# 不修改任何檔案。設計為 RETRO 週期手動執行（自我評估 roadmap R4）。
#
# 用法：
#   ruby scripts/check_decision_revisit.rb          # markdown 報告
#   ruby scripts/check_decision_revisit.rb --json   # JSON 輸出

require 'yaml'
require 'json'

ROOT = File.expand_path('..', __dir__)
DECISIONS_GLOB = File.join(ROOT, 'memory', 'active_projects', '*', 'decisions', '*.yaml')

def load_yaml(path)
  data = YAML.load_file(path)
  data.is_a?(Hash) ? data : {}
rescue StandardError
  {}
end

# 當前可量化指標（皆由 repo 實況計算）
def current_metrics
  statuses = Dir.glob(File.join(ROOT, 'tasks', '20*.yaml')).map { |f| load_yaml(f)['status'].to_s }
  {
    open_tasks: statuses.count { |s| %w[pending in_progress].include?(s) },
    backlog: statuses.count { |s| !s.empty? && !%w[done failed].include?(s) },
    runs: Dir.glob(File.join(ROOT, 'logs', 'runs', '*.yaml')).length,
    overlap_pct: load_yaml(File.join(ROOT, 'system', 'NATIVE_OVERLAP.yaml'))['aggregate_estimate_pct'].to_i
  }
end

# 回傳 [verdict, detail]；verdict ∈ DUE / OK / MANUAL
def evaluate(trigger, m)
  t = trigger.to_s.gsub(/\s+/, ' ').strip
  return ['MANUAL', '無 revisit_trigger'] if t.empty?

  if (t =~ /並行任務|平行任務|concurrent/) && (n = t[/(\d+)/, 1])
    cur = m[:open_tasks]
    return [cur >= n.to_i ? 'DUE' : 'OK', "進行中任務 #{cur} / 門檻 #{n}（未完成 backlog #{m[:backlog]}）"]
  end
  if (t =~ /runs/) && (n = (t[/(\d+)\s*筆?\s*runs/, 1] || t[/累積\s*(\d+)/, 1]))
    cur = m[:runs]
    return [cur >= n.to_i ? 'DUE' : 'OK', "logs/runs 現有 #{cur} / 門檻 #{n}"]
  end
  if (t =~ /重疊|aggregate|overlap/) && (n = t[/(\d+)\s*%/, 1])
    cur = m[:overlap_pct]
    return [cur >= n.to_i ? 'DUE' : 'OK', "原生重疊 #{cur}% / 門檻 #{n}%"]
  end

  ['MANUAL', '觸發條件非量化，需 RETRO 人工判斷']
end

metrics = current_metrics
rows = Dir.glob(DECISIONS_GLOB).sort.map do |path|
  d = load_yaml(path)
  verdict, detail = evaluate(d['revisit_trigger'], metrics)
  {
    'decision_id' => d['decision_id'] || File.basename(path, '.yaml'),
    'date' => d['date'],
    'status' => d['status'],
    'verdict' => verdict,
    'detail' => detail,
    'revisit_trigger' => d['revisit_trigger'].to_s.gsub(/\s+/, ' ').strip
  }
end

counts = Hash.new(0)
rows.each { |r| counts[r['verdict']] += 1 }
summary = "DUE=#{counts['DUE']} OK=#{counts['OK']} MANUAL=#{counts['MANUAL']}"

if ARGV.include?('--json')
  puts JSON.pretty_generate(
    'generated' => Time.now.strftime('%Y-%m-%d'),
    'summary' => summary,
    'metrics' => metrics,
    'decisions' => rows
  )
  exit 0
end

puts "# Decision Revisit Tracker — #{Time.now.strftime('%Y-%m-%d')}"
puts
puts "掃描 #{rows.length} 筆決策。summary: #{summary}"
puts "當前量化指標：進行中任務 #{metrics[:open_tasks]} / backlog #{metrics[:backlog]} / logs-runs #{metrics[:runs]} / 原生重疊 #{metrics[:overlap_pct]}%"
puts
puts '| decision_id | status | verdict | 評估 | revisit_trigger |'
puts '|-------------|--------|:-------:|------|-----------------|'
rows.each do |r|
  trig = r['revisit_trigger']
  trig = "#{trig[0, 58]}…" if trig.length > 58
  puts "| #{r['decision_id']} | #{r['status']} | #{r['verdict']} | #{r['detail']} | #{trig} |"
end
puts
puts '> DUE = 觸發已達標，建議本次 RETRO 重新檢視；MANUAL = 非量化觸發，需人工判斷。'
exit 0
