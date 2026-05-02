#!/usr/bin/env ruby
# frozen_string_literal: true

require 'yaml'

allowed = %w[A B C D].freeze

files = if ARGV.empty?
          Dir.glob('logs/runs/RUN-*-DUAL*.yaml').sort
        else
          ARGV
        end

if files.empty?
  puts 'OK: no dual-path run files found (logs/runs/RUN-*-DUAL*.yaml)'
  exit 0
end

all_errors = []

files.each do |file|
  begin
    data = YAML.load_file(file)
  rescue StandardError => e
    all_errors << "#{file}: cannot parse (#{e.class})"
    next
  end

  status = data.dig('execution_log', 'status')
  results = data.dig('execution_log', 'comparison_results')
  unless results.is_a?(Array) && results.length == 10
    all_errors << "#{file}: comparison_results must be an array of length 10"
    next
  end

  results.each do |row|
    idx = row['index']
    cat = row['diff_category']
    py = row['python_result']
    fb = row['fallback_result']

    all_errors << "#{file} index #{idx}: diff_category must be one of #{allowed.join('/')}" unless allowed.include?(cat)

    if status == 'completed' && (py == 'pending' || fb == 'pending')
      all_errors << "#{file} index #{idx}: completed status cannot contain pending python_result/fallback_result"
    end
  end
end

if all_errors.empty?
  puts "OK: dual-path category checks passed (#{files.length} file(s))"
  exit 0
end

puts 'FAILED: dual-path category checks found issues:'
all_errors.each { |e| puts "- #{e}" }
exit 1
