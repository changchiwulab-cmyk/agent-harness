#!/usr/bin/env ruby
# frozen_string_literal: true

# Context budget check — 驗證 CLAUDE.md + GLOBAL_RULES.md 加總不超過 3,000 tokens。
# 依據：CLAUDE.md「Context 硬限制」段落。
#
# 估算法（language-aware，保守上界）：
#   - ASCII 字元（codepoint < 128）：每 4 個字元 ≈ 1 token（英文/程式碼經驗值）
#   - 非 ASCII 字元（CJK、emoji、全形符號）：每個字元 ≈ 1 token（保守上界）
#   此做法避免 char/4 對中文嚴重低估造成假陰性。
#
# exit 0 = 通過；exit 1 = 超限或檔案缺失。

TOKEN_BUDGET = 3_000
ASCII_CHARS_PER_TOKEN = 4
TARGET_FILES = [
  'CLAUDE.md',
  'system/GLOBAL_RULES.md'
].freeze

def estimate_tokens(path)
  return nil unless File.exist?(path)

  content = File.read(path, encoding: 'UTF-8')
  ascii_count = 0
  non_ascii_count = 0
  content.each_char do |ch|
    if ch.ord < 128
      ascii_count += 1
    else
      non_ascii_count += 1
    end
  end

  ((ascii_count.to_f / ASCII_CHARS_PER_TOKEN) + non_ascii_count).ceil
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

  puts 'Context budget estimate (ASCII / 4 + non-ASCII × 1):'
  per_file.each { |path, tokens| puts format('  %-28s  ~%d tokens', path, tokens) }
  puts format('  %-28s  ~%d tokens (budget %d)', 'TOTAL', total, TOKEN_BUDGET)

  if total > TOKEN_BUDGET
    warn "FAILED: context budget exceeded (~#{total} > #{TOKEN_BUDGET})"
    exit 1
  end

  puts 'OK: context budget within limit'
  exit 0
end
