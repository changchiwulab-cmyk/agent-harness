#!/usr/bin/env ruby
# frozen_string_literal: true

# Docs Parity Check
# 依據：deep-research-report-2.md P0「docs parity gate」
#
# 規則：skill_type 的「合法值集合」必須在四處一致：
#   1. scripts/check_spec_consistency.rb 的 ALLOWED_SKILL
#   2. README.md 快速上手段（"請使用：" 列舉）
#   3. tasks/TASK_CARD_TEMPLATE.yaml skill_type 欄位的註解
#   4. system/ROUTING_RULES.md 的 skill table 欄
#
# exit 0 = 四處一致；exit 1 = 任一處 drift

require 'set'

CANONICAL_SKILLS = %w[research analysis writing ops review].freeze

def extract_validator_skills(path)
  return nil unless File.exist?(path)

  content = File.read(path, encoding: 'UTF-8')
  m = content.match(/ALLOWED_SKILL\s*=\s*%w\[([^\]]+)\]/)
  return nil unless m

  m[1].split(/\s+/).reject(&:empty?)
end

def extract_readme_skills(path)
  return nil unless File.exist?(path)

  content = File.read(path, encoding: 'UTF-8')
  m = content.match(/skill_type[^\n]*?請使用[：:][^\n]*?`([^`]+)`(?:\s*\/\s*`([^`]+)`)*[^\n]*/)
  return nil unless m

  line = content.lines.find { |l| l.include?('skill_type') && l.include?('請使用') }
  return nil unless line

  line.scan(/`([a-z]+)`/).flatten
end

def extract_template_skills(path)
  return nil unless File.exist?(path)

  content = File.read(path, encoding: 'UTF-8')
  line = content.lines.find { |l| l =~ /^\s*skill_type:/ }
  return nil unless line

  line.scan(/\b(research|analysis|writing|ops|review)\b/).flatten.uniq
end

def extract_routing_skills(path)
  return nil unless File.exist?(path)

  content = File.read(path, encoding: 'UTF-8')
  rows = content.lines.select { |l| l =~ /^\|\s*[一-鿿]/ }
  rows.map do |row|
    cells = row.split('|').map(&:strip)
    cells[2]
  end.compact.reject(&:empty?).select { |s| s.match?(/\A[a-z]+\z/) }.uniq
end

def report_source(label, skills)
  if skills.nil?
    "  #{label}: <unable to parse>"
  else
    "  #{label}: [#{skills.join(', ')}]"
  end
end

if __FILE__ == $PROGRAM_NAME
  validator = extract_validator_skills('scripts/check_spec_consistency.rb')
  readme = extract_readme_skills('README.md')
  template = extract_template_skills('tasks/TASK_CARD_TEMPLATE.yaml')
  routing = extract_routing_skills('system/ROUTING_RULES.md')

  sources = {
    'scripts/check_spec_consistency.rb (ALLOWED_SKILL)' => validator,
    'README.md (skill_type list)' => readme,
    'tasks/TASK_CARD_TEMPLATE.yaml (skill_type comment)' => template,
    'system/ROUTING_RULES.md (skill table)' => routing
  }

  puts 'Docs parity check — skill_type set:'
  sources.each { |label, skills| puts report_source(label, skills) }
  puts "  CANONICAL: [#{CANONICAL_SKILLS.join(', ')}]"

  errors = []
  canonical_set = CANONICAL_SKILLS.to_set

  sources.each do |label, skills|
    if skills.nil?
      errors << "#{label}: failed to extract skill list"
      next
    end

    actual_set = skills.to_set
    missing = canonical_set - actual_set
    extra = actual_set - canonical_set
    errors << "#{label}: missing #{missing.to_a.inspect}" unless missing.empty?
    errors << "#{label}: unexpected #{extra.to_a.inspect}" unless extra.empty?
  end

  if errors.empty?
    puts 'OK: skill_type set is consistent across all four sources'
    exit 0
  end

  puts 'FAILED: docs parity issues:'
  errors.each { |e| puts "- #{e}" }
  exit 1
end
