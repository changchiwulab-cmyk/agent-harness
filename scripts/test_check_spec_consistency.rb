#!/usr/bin/env ruby
# frozen_string_literal: true

# Unit tests for check_spec_consistency.rb
# 使用標準 minitest，無需額外安裝

require 'minitest/autorun'
require 'tmpdir'
require 'fileutils'
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

# ── 測試雙驗證器 REQUIRED_FIELDS parity ──────────────────────────────────────
# D-O01 決議保留雙驗證器（Ruby CI 全量 + Python 單卡 CLI），欄位清單必須一致。
# 從 system/validate_task_card.py 原始碼抽出 REQUIRED_FIELDS 清單直接比對，
# 任一邊單獨改動都會在 CI 現形。
class TestValidatorParity < Minitest::Test
  PYTHON_VALIDATOR = File.join(__dir__, '..', 'system', 'validate_task_card.py')

  def python_required_fields
    src = File.read(PYTHON_VALIDATOR, encoding: 'UTF-8')
    m = src.match(/REQUIRED_FIELDS\s*=\s*\[(.*?)\]/m)
    refute_nil m, 'validate_task_card.py 找不到 REQUIRED_FIELDS 定義'
    m[1].scan(/"([^"]+)"/).flatten
  end

  def test_required_fields_match_python_validator
    assert_equal REQUIRED_FIELDS.sort, python_required_fields.sort,
                 'Ruby 與 Python 驗證器的 REQUIRED_FIELDS 不同步'
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

# ── 測試 skill / agent frontmatter lint（section 7-8；以 subprocess 在 tmp 跑）──
class TestFrontmatterLint < Minitest::Test
  SCRIPT = File.join(__dir__, 'check_spec_consistency.rb')
  REQUIRED_DIRS = %w[
    logs/runs logs/approvals logs/errors
    outputs/drafts outputs/reports memory/active_projects
  ].freeze

  def run_in(dir)
    out = `cd #{dir} && ruby #{SCRIPT} 2>&1`
    [out, $?.exitstatus]
  end

  def scaffold(root)
    REQUIRED_DIRS.each { |d| FileUtils.mkdir_p(File.join(root, d)) }
  end

  def test_skill_missing_frontmatter_fails
    Dir.mktmpdir do |root|
      scaffold(root)
      FileUtils.mkdir_p(File.join(root, 'skills/research'))
      File.write(File.join(root, 'skills/research/SKILL.md'), "# Research Skill\n")
      out, code = run_in(root)
      refute_equal 0, code
      assert_match(/missing YAML frontmatter/, out)
    end
  end

  def test_skill_good_frontmatter_passes
    Dir.mktmpdir do |root|
      scaffold(root)
      FileUtils.mkdir_p(File.join(root, 'skills/research'))
      File.write(
        File.join(root, 'skills/research/SKILL.md'),
        "---\nname: research\ndescription: x\n---\n\n# Research Skill\n"
      )
      out, code = run_in(root)
      assert_equal 0, code, out
    end
  end

  def test_skill_name_mismatch_fails
    Dir.mktmpdir do |root|
      scaffold(root)
      FileUtils.mkdir_p(File.join(root, 'skills/ops'))
      File.write(
        File.join(root, 'skills/ops/SKILL.md'),
        "---\nname: research\ndescription: x\n---\n"
      )
      out, code = run_in(root)
      refute_equal 0, code
      assert_match(/!= directory/, out)
    end
  end

  def test_agent_bad_model_fails
    Dir.mktmpdir do |root|
      scaffold(root)
      FileUtils.mkdir_p(File.join(root, '.claude/agents'))
      File.write(
        File.join(root, '.claude/agents/x.md'),
        "---\nname: x\ndescription: y\nmodel: gpt-4\n---\n"
      )
      out, code = run_in(root)
      refute_equal 0, code
      assert_match(/invalid model/, out)
    end
  end

  def test_agent_alias_model_passes
    Dir.mktmpdir do |root|
      scaffold(root)
      FileUtils.mkdir_p(File.join(root, '.claude/agents'))
      File.write(
        File.join(root, '.claude/agents/x.md'),
        "---\nname: x\ndescription: y\nmodel: haiku\n---\n"
      )
      out, code = run_in(root)
      assert_equal 0, code, out
    end
  end
end

# ── 測試 G-D state/ resume schema 常數（來自 #118）────────────────────────────
class TestStateSchemaConstants < Minitest::Test
  def test_state_status_enum
    assert_equal %w[active paused done], ALLOWED_STATE_STATUS
  end

  def test_required_state_fields
    assert_equal %w[task_id updated_at status next_action checkpoint_commit], REQUIRED_STATE_FIELDS
  end
end

# ── 測試 R11 批准覆蓋率交叉檢查 ────────────────────────────────────────────────
class TestApprovalCoverage < Minitest::Test
  CUTOFF = Date.new(2026, 7, 1)

  def task(overrides = {})
    {
      'task_id' => '20260701-999',
      'status' => 'done',
      'date' => '2026-07-01',
      'approval_needed' => true,
    }.merge(overrides)
  end

  def test_covered_task_on_cutoff_passes
    errors = check_approval_coverage([['t.yaml', task]], ['20260701-999'], CUTOFF)
    assert_empty errors
  end

  def test_uncovered_task_on_cutoff_fails
    errors = check_approval_coverage([['t.yaml', task]], [], CUTOFF)
    assert_equal 1, errors.length
    assert_includes errors.first, '20260701-999'
  end

  def test_uncovered_task_before_cutoff_is_grandfathered
    errors = check_approval_coverage(
      [['t.yaml', task('date' => '2026-06-30')]], [], CUTOFF
    )
    assert_empty errors
  end

  def test_approval_needed_false_is_never_checked
    errors = check_approval_coverage(
      [['t.yaml', task('approval_needed' => false)]], [], CUTOFF
    )
    assert_empty errors
  end

  def test_non_terminal_status_is_not_checked_yet
    %w[pending in_progress checkpoint review].each do |status|
      errors = check_approval_coverage(
        [['t.yaml', task('status' => status)]], [], CUTOFF
      )
      assert_empty errors, "status=#{status} should not require approval coverage yet"
    end
  end

  def test_failed_status_is_checked_like_done
    errors = check_approval_coverage(
      [['t.yaml', task('status' => 'failed')]], [], CUTOFF
    )
    assert_equal 1, errors.length
  end

  def test_malformed_date_does_not_crash_and_is_skipped
    errors = check_approval_coverage(
      [['t.yaml', task('date' => 'not-a-date')]], [], CUTOFF
    )
    assert_empty errors
  end

  def test_end_to_end_rejected_only_record_does_not_cover_task
    # Codex review: a task with only a rejected/superseded approval record
    # must NOT be treated as covered — otherwise the gate is bypassable.
    entries = [
      ['a.yaml', 0, { 'task_id' => '20260701-999', 'status' => 'rejected' }],
      ['a.yaml', 1, { 'task_id' => '20260701-999', 'status' => 'superseded' }],
    ]
    errors = check_approval_coverage([['t.yaml', task]], approved_task_ids(entries), CUTOFF)
    assert_equal 1, errors.length
  end

  def test_end_to_end_approved_record_covers_task
    entries = [['a.yaml', 0, { 'task_id' => '20260701-999', 'status' => 'approved' }]]
    errors = check_approval_coverage([['t.yaml', task]], approved_task_ids(entries), CUTOFF)
    assert_empty errors
  end
end

# ── 測試 approved_task_ids 篩選（R12 review fix）───────────────────────────────
class TestApprovedTaskIds < Minitest::Test
  def test_only_approved_status_counts
    entries = [
      ['a.yaml', 0, { 'task_id' => 'X', 'status' => 'approved' }],
      ['a.yaml', 1, { 'task_id' => 'Y', 'status' => 'rejected' }],
      ['a.yaml', 2, { 'task_id' => 'Z', 'status' => 'superseded' }],
    ]
    assert_equal ['X'], approved_task_ids(entries)
  end

  def test_one_approved_among_multiple_records_for_same_task_still_counts
    entries = [
      ['a.yaml', 0, { 'task_id' => 'X', 'status' => 'rejected' }],
      ['a.yaml', 1, { 'task_id' => 'X', 'status' => 'approved' }],
    ]
    assert_equal ['X'], approved_task_ids(entries)
  end

  def test_empty_entries_returns_empty
    assert_empty approved_task_ids([])
  end
end

# ── 測試 R12 跨檔案參照完整性 ──────────────────────────────────────────────────
class TestReferentialIntegrity < Minitest::Test
  def test_run_task_id_matches_known_task_passes
    errors = check_run_task_references(
      [['run.yaml', { 'task_id' => '20260701-001' }]], ['20260701-001']
    )
    assert_empty errors
  end

  def test_run_task_id_broken_link_fails
    errors = check_run_task_references(
      [['run.yaml', { 'task_id' => '99990101-999' }]], ['20260701-001']
    )
    assert_equal 1, errors.length
    assert_includes errors.first, '99990101-999'
  end

  def test_run_without_task_id_is_skipped
    errors = check_run_task_references([['run.yaml', {}]], [])
    assert_empty errors
  end

  def test_approval_linked_run_matches_known_run_passes
    rec = { 'linked_run' => 'RUN-20260701-001' }
    errors = check_approval_run_references(
      [['appr.yaml', 0, rec]], ['RUN-20260701-001']
    )
    assert_empty errors
  end

  def test_approval_linked_run_broken_link_fails
    rec = { 'linked_run' => 'RUN-DOES-NOT-EXIST' }
    errors = check_approval_run_references(
      [['appr.yaml', 0, rec]], ['RUN-20260701-001']
    )
    assert_equal 1, errors.length
    assert_includes errors.first, 'RUN-DOES-NOT-EXIST'
  end

  def test_approval_without_linked_run_is_skipped
    rec = { 'linked_run' => '' }
    errors = check_approval_run_references([['appr.yaml', 0, rec]], [])
    assert_empty errors
  end
end
