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

# ── 測試 PERMISSIONS 登錄器載入（D007）────────────────────────────────────────
class TestLoadPermissionsRegistry < Minitest::Test
  def setup
    @tmp = Dir.mktmpdir
  end

  def teardown
    FileUtils.remove_entry(@tmp) if @tmp && Dir.exist?(@tmp)
  end

  def write_perms(content)
    path = File.join(@tmp, 'perms.yaml')
    File.write(path, content)
    path
  end

  def test_returns_allow_and_ask_as_registered
    path = write_perms(<<~YAML)
      permissions:
        allow:
          - file_read
          - web_search
        ask:
          - modify_skills
        deny:
          - shell_delete
    YAML
    registered, denied, err = load_permissions_registry(path)
    assert_nil err
    assert_includes registered, 'file_read'
    assert_includes registered, 'web_search'
    assert_includes registered, 'modify_skills'
    refute_includes registered, 'shell_delete'
    assert_includes denied, 'shell_delete'
  end

  def test_missing_file_returns_error
    _registered, _denied, err = load_permissions_registry(File.join(@tmp, 'nope.yaml'))
    refute_nil err
    assert_match(/missing/, err)
  end

  def test_malformed_file_returns_error
    path = write_perms("not_a_permissions_doc: true\n")
    _registered, _denied, err = load_permissions_registry(path)
    refute_nil err
    assert_match(/permissions/, err)
  end

  def test_yaml_syntax_error_returns_error
    path = write_perms("permissions:\n  allow:\n    - foo\n  ask: [unterminated\n")
    _registered, _denied, err = load_permissions_registry(path)
    refute_nil err
    assert_match(/malformed YAML/, err)
  end
end

# ── 整合測試：Task Card 違反新規則時 validator 報錯 ───────────────────────────
# 以子程序方式跑 scripts/check_spec_consistency.rb，在 tmp 目錄下組裝假專案
require 'fileutils'
require 'open3'

class TestValidatorIntegration < Minitest::Test
  SCRIPT = File.expand_path('check_spec_consistency.rb', __dir__)

  def setup
    @tmp = Dir.mktmpdir
    # 模擬專案必要目錄
    %w[logs/runs logs/approvals logs/errors outputs/drafts outputs/reports
       memory/active_projects tasks system scripts].each do |d|
      FileUtils.mkdir_p(File.join(@tmp, d))
    end
    FileUtils.cp(SCRIPT, File.join(@tmp, 'scripts', 'check_spec_consistency.rb'))
    File.write(File.join(@tmp, 'system/PERMISSIONS.yaml'), <<~YAML)
      permissions:
        allow:
          - file_read
          - write_drafts
        ask:
          - modify_skills
        deny:
          - shell_delete
          - sub_agent_with_write_access
    YAML
  end

  def teardown
    FileUtils.remove_entry(@tmp) if @tmp && Dir.exist?(@tmp)
  end

  def base_task(overrides = {})
    {
      'task_id' => '20260420-T01',
      'date' => '2026-04-20',
      'status' => 'pending',
      'goal' => 'test',
      'definition_of_done' => ['x'],
      'expected_output' => { 'format' => 'md', 'location' => 'outputs/drafts/', 'filename' => 'x.md' },
      'risk_level' => 'low',
      'approval_needed' => false,
      'skill_type' => 'ops',
      'allowed_tools' => ['file_read']
    }.merge(overrides)
  end

  def run_validator
    Open3.capture3('ruby', 'scripts/check_spec_consistency.rb', chdir: @tmp)
  end

  def write_task(name, task)
    File.write(File.join(@tmp, 'tasks', name), YAML.dump(task))
  end

  def test_unregistered_tool_fails
    write_task('t1.yaml', base_task('allowed_tools' => ['file_read', 'nonexistent_tool']))
    stdout, _stderr, status = run_validator
    refute status.success?, "expected validator to fail, got:\n#{stdout}"
    assert_match(/unregistered tool 'nonexistent_tool'/, stdout)
  end

  def test_denied_tool_fails
    write_task('t1.yaml', base_task('allowed_tools' => ['file_read', 'sub_agent_with_write_access']))
    stdout, _stderr, status = run_validator
    refute status.success?, "expected validator to fail, got:\n#{stdout}"
    assert_match(/denied tool 'sub_agent_with_write_access'/, stdout)
  end

  def test_high_risk_without_approval_fails
    write_task('t1.yaml', base_task('risk_level' => 'high', 'approval_needed' => false))
    stdout, _stderr, status = run_validator
    refute status.success?, "expected validator to fail, got:\n#{stdout}"
    assert_match(/risk_level=high requires approval_needed: true/, stdout)
  end

  def test_critical_risk_without_approval_fails
    write_task('t1.yaml', base_task('risk_level' => 'critical', 'approval_needed' => false))
    stdout, _stderr, status = run_validator
    refute status.success?, "expected validator to fail, got:\n#{stdout}"
    assert_match(/risk_level=critical/, stdout)
  end

  def test_duplicate_task_id_fails
    write_task('t1.yaml', base_task('task_id' => '20260420-D01'))
    write_task('t2.yaml', base_task('task_id' => '20260420-D01'))
    stdout, _stderr, status = run_validator
    refute status.success?, "expected validator to fail, got:\n#{stdout}"
    assert_match(/duplicate task_id 20260420-D01/, stdout)
  end

  def test_valid_task_passes
    write_task('t1.yaml', base_task)
    stdout, _stderr, status = run_validator
    assert status.success?, "expected validator to pass, got:\n#{stdout}"
  end
end
