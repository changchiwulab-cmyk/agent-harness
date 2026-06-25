#!/usr/bin/env ruby
# frozen_string_literal: true
#
# Unit tests for check_decision_revisit.rb (R4: 20260529-007)
# 使用標準 minitest，無需額外安裝。

require 'minitest/autorun'
require 'json'

SCRIPT = File.join(__dir__, 'check_decision_revisit.rb')

class TestDecisionRevisit < Minitest::Test
  def setup
    @out = `ruby #{SCRIPT}`.force_encoding('UTF-8')
    @status = $?.exitstatus
    @json_raw = `ruby #{SCRIPT} --json`.force_encoding('UTF-8')
  end

  def test_exits_zero
    assert_equal 0, @status, "script should exit 0 (read-only report)"
  end

  def test_lists_all_eight_decisions
    %w[
      20260403-D001 20260403-D002 20260415-D003 20260415-D004
      20260415-D005 20260424-D006 20260509-D007 20260625-D008
    ].each { |id| assert_includes @out, id, "missing decision #{id}" }
  end

  def test_reports_summary_line
    assert_match(/summary: DUE=\d+ OK=\d+ MANUAL=\d+/, @out)
  end

  def test_quantitative_triggers_are_evaluated
    # D001（並行任務數）與 D006（runs 數）必須被量化評估，而非落入 MANUAL
    assert_includes @out, '進行中任務'      # D001 detail
    assert_includes @out, 'logs/runs 現有'  # D006 detail
  end

  def test_json_is_parseable_with_eight_decisions
    data = JSON.parse(@json_raw)
    assert data['decisions'].is_a?(Array)
    assert_equal 8, data['decisions'].length
    assert data.key?('metrics')
  end
end
