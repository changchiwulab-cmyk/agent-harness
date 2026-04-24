#!/usr/bin/env ruby
# frozen_string_literal: true

# Context budget check — 驗證 CLAUDE.md + GLOBAL_RULES.md 加總不超過 3,000 tokens。
# 依據：CLAUDE.md「Context 硬限制」段落。
# 粗估：token ≈ 字元數 / 4（中英混合語料經驗值）。
#
# exit 0 = 通過；exit 1 = 超限或檔案缺失。

TOKEN_BUDGET = 3_000
CHARS_PER_TOKEN = 4
TARGET_FILES = [
  'CLAUDE.md',
  'system/GLOBAL_RULES.md'
].freeze

def estimate_tokens(path)
  return nil unless File.exist?(path)

  # 以字元數粗估，排除純 ASCII 空白帶來的低估；統一以 size 為基準
  content = File.read(path, encoding: 'UTF-8')
  (content.length.to_f / CHARS_PER_TOKEN).ceil
end

if __FILE__ == $PROGRAM_NAME
  missing = TARGET_FILES.reject { |p| File.exist?(p) }
  unless missing.empty?
    warn "FAILED: missing target file(s): #{missing.join(', ')}"
    exit 1
  end

  total = 0
  per_file = {}
  TARGET_FILES.each do |path|
    est = estimate_tokens(path)
    per_file[path] = est
    total += est
  end

  puts 'Context budget estimate:'
  per_file.each { |path, tokens| puts format('  %-28s  ~%d tokens', path, tokens) }
  puts format('  %-28s  ~%d tokens (budget %d)', 'TOTAL', total, TOKEN_BUDGET)

  if total > TOKEN_BUDGET
    warn "FAILED: context budget exceeded (~#{total} > #{TOKEN_BUDGET})"
    exit 1
  end

  puts 'OK: context budget within limit'
  exit 0
end
