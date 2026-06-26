#!/usr/bin/env ruby
# frozen_string_literal: true

# Unit tests for check_spec_consistency.rb
# 使用標準 minitest，無需額外安裝

require 'minitest/autorun'
require 'tmpdir'
require 'yaml'
require 'date'

# ── 直接 load 受測函式（跳過主程式邏輯）──────────────────────────────────────
# 將 parse_iso_date 和常數從原腳本引入
# check_spec_consistency.rb 裡的 parse_iso_date 是頂層 def，直接 load 即可取得
load File.join(__dir__, 'check_spec_consistency.rb')

# ── 測試 parse_iso_date ────────────────────────────────────────────────────────
class TestParseIsoDate < Minitest::Test
  def test_valid_date_string
    result = parse_iso_date('2026-04-15')
    assert_equal Date.new(2026, 4, 15), result
  end

  def test_invalid_format_returns_nil
    assert_nil parse_iso_date('20260415')
    assert_nil parse_iso_date('15-04-2026')
    assert_nil parse_iso_date('')
  end

  def test_invalid_calendar_returns_nil
    assert_nil parse_iso_date('2026-13-01')  # 月份 13 不存在
    assert_nil parse_iso_date('2026-02-30')  # 二月沒有 30 日
  end

  def test_date_object_passes_through
    d = Date.new(2026, 4, 15)
    assert_equal d, parse_iso_date(d)
  end

  def test_nil_returns_nil
    assert_nil parse_iso_date(nil)
  end
end

# ── 測試常數定義 ───────────────────────────────────────────────────────────────
class TestConstants < Minitest::Test
  def test_allowed_skill_includes_analysis
    assert_includes ALLOWED_SKILL, 'analysis'
  end

  def test_allowed_skill_has_five_types
    assert_equal 5, ALLOWED_SKILL.length
    assert_equal %w[research writing ops review analysis], ALLOWED_SKILL
  end

  def test_task_id_pattern_accepts_numeric
    assert_match TASK_ID_PATTERN, '20260415-001'
  end

  def test_task_id_pattern_accepts_letter_prefix
    assert_match TASK_ID_PATTERN, '20260404-RV01'
    assert_match TASK_ID_PATTERN, '20260404-W01'
    assert_match TASK_ID_PATTERN, '20260404-R01'
  end

  def test_task_id_pattern_rejects_invalid
    refute_match TASK_ID_PATTERN, '2026-04-15-001'  # 錯誤分隔符
    refute_match TASK_ID_PATTERN, '20260415'         # 缺少序號
    refute_match TASK_ID_PATTERN, 'YYYYMMDD-001'     # 非數字日期
  end

  def test_allowed_risk_levels
    assert_equal %w[low medium high critical], ALLOWED_RISK
  end

  def test_allowed_status_values
    assert_includes ALLOWED_STATUS, 'pending'
    assert_includes ALLOWED_STATUS, 'done'
    assert_includes ALLOWED_STATUS, 'failed'
    assert_includes ALLOWED_STATUS, 'in_progress'
    assert_includes ALLOWED_STATUS, 'checkpoint'
    assert_includes ALLOWED_STATUS, 'review'
  end
end

# ── 測試 TASK_ID_PATTERN 邊界條件 ─────────────────────────────────────────────
class TestTaskIdPattern < Minitest::Test
  def test_only_letters_no_digits_suffix_rejected
    refute_match TASK_ID_PATTERN, '20260415-ABC'  # 必須有至少一個數字結尾
  end

  def test_empty_suffix_rejected
    refute_match TASK_ID_PATTERN, '20260415-'
  end
end

# ── 測試 R2 logs schema lint 常數 ─────────────────────────────────────────────
class TestLogsSchemaLintConstants < Minitest::Test
  def test_run_status_enum
    assert_equal %w[completed failed partial cancelled], ALLOWED_RUN_STATUS
  end

  def test_required_run_fields
    assert_equal %w[run_id task_id status gate_results], REQUIRED_RUN_FIELDS
  end

  def test_approval_method_enum
    assert_equal %w[human_confirm draft_first], ALLOWED_APPROVAL_METHOD
  end

  def test_approval_status_enum
    assert_equal %w[approved rejected superseded], ALLOWED_APPROVAL_STATUS
  end

  def test_required_approval_fields_core
    %w[approval_id task_id date action approval_method status approved_by].each do |f|
      assert_includes REQUIRED_APPROVAL_FIELDS, f
    end
  end

  def test_error_type_enum_matches_template
    assert_includes ALLOWED_ERROR_TYPE, 'schema_failure'
    assert_includes ALLOWED_ERROR_TYPE, 'tool_failure'
    assert_equal 5, ALLOWED_ERROR_TYPE.length
  end
end

# ── 測試 v2.1 治理層硬化常數（信任邊界 + eval harness）─────────────────────────
class TestV21Constants < Minitest::Test
  def test_required_sec_ids
    assert_equal %w[SEC-05 SEC-06 SEC-07], REQUIRED_SEC_IDS
  end

  def test_allowed_rubric_check_types
    assert_includes ALLOWED_RUBRIC_CHECK_TYPES, 'required_heading'
    assert_includes ALLOWED_RUBRIC_CHECK_TYPES, 'heading_order'
    assert_includes ALLOWED_RUBRIC_CHECK_TYPES, 'forbidden_regex'
    assert_equal 5, ALLOWED_RUBRIC_CHECK_TYPES.length
  end
end
