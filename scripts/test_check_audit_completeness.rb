#!/usr/bin/env ruby
# frozen_string_literal: true

# Unit tests for check_audit_completeness.rb

require 'minitest/autorun'
require 'tmpdir'
require 'fileutils'
require 'yaml'

load File.join(__dir__, 'check_audit_completeness.rb')

# ── 測試 collect_completed_task_ids ──────────────────────────────────────────
class TestCollectCompletedTaskIds < Minitest::Test
  def setup
    @tmpdir = Dir.mktmpdir
    @tasks_dir = File.join(@tmpdir, 'tasks')
    FileUtils.mkdir_p(@tasks_dir)
    FileUtils.mkdir_p(File.join(@tasks_dir, 'examples'))
  end

  def teardown
    FileUtils.remove_entry(@tmpdir)
  end

  def write_task(filename, hash)
    File.write(File.join(@tasks_dir, filename), hash.to_yaml)
  end

  def glob
    File.join(@tasks_dir, '**/*.yaml')
  end

  def test_picks_up_done_task
    write_task('a.yaml', { 'task_id' => '20260427-A01', 'status' => 'done' })
    result = collect_completed_task_ids(glob)
    assert_equal ['20260427-A01'], result.map { |t| t[:task_id] }
  end

  def test_picks_up_failed_task
    write_task('f.yaml', { 'task_id' => '20260427-F01', 'status' => 'failed' })
    ids = collect_completed_task_ids(glob).map { |t| t[:task_id] }
    assert_includes ids, '20260427-F01'
  end

  def test_picks_up_partial_task
    write_task('p.yaml', { 'task_id' => '20260427-P01', 'status' => 'partial' })
    ids = collect_completed_task_ids(glob).map { |t| t[:task_id] }
    assert_includes ids, '20260427-P01'
  end

  def test_skips_pending_task
    write_task('p.yaml', { 'task_id' => '20260427-X01', 'status' => 'pending' })
    ids = collect_completed_task_ids(glob).map { |t| t[:task_id] }
    refute_includes ids, '20260427-X01'
  end

  def test_skips_review_task
    write_task('r.yaml', { 'task_id' => '20260427-R01', 'status' => 'review' })
    ids = collect_completed_task_ids(glob).map { |t| t[:task_id] }
    refute_includes ids, '20260427-R01'
  end

  def test_skips_template_files
    write_task('TASK_CARD_TEMPLATE.yaml', { 'task_id' => '20260427-T01', 'status' => 'done' })
    ids = collect_completed_task_ids(glob).map { |t| t[:task_id] }
    refute_includes ids, '20260427-T01'
  end

  def test_skips_examples_dir
    File.write(File.join(@tasks_dir, 'examples', 'sample.yaml'),
               { 'task_id' => '20260427-EX1', 'status' => 'done' }.to_yaml)
    ids = collect_completed_task_ids(glob).map { |t| t[:task_id] }
    refute_includes ids, '20260427-EX1'
  end

  def test_rejects_invalid_task_id_format
    write_task('bad.yaml', { 'task_id' => 'INVALID', 'status' => 'done' })
    ids = collect_completed_task_ids(glob).map { |t| t[:task_id] }
    refute_includes ids, 'INVALID'
  end

  def test_returns_status_in_result
    write_task('a.yaml', { 'task_id' => '20260427-A01', 'status' => 'failed' })
    result = collect_completed_task_ids(glob)
    assert_equal 'failed', result.first[:status]
  end
end

# ── 測試 collect_audit_log_task_ids ──────────────────────────────────────────
class TestCollectAuditLogTaskIds < Minitest::Test
  def setup
    @tmpdir = Dir.mktmpdir
    @audit_path = File.join(@tmpdir, 'AUDIT_LOG.md')
  end

  def teardown
    FileUtils.remove_entry(@tmpdir)
  end

  def test_extracts_double_quoted_task_ids
    File.write(@audit_path, <<~MD)
      ```yaml
      - task_id: "20260427-A01"
        date: "2026-04-27"
      ```
    MD
    assert_includes collect_audit_log_task_ids(@audit_path), '20260427-A01'
  end

  def test_skips_empty_task_id
    File.write(@audit_path, <<~MD)
      ```yaml
      - task_id: ""
        date: ""
      ```
    MD
    assert_empty collect_audit_log_task_ids(@audit_path)
  end

  def test_deduplicates
    File.write(@audit_path, <<~MD)
      task_id: "20260427-A01"
      task_id: "20260427-A01"
      task_id: "20260427-B01"
    MD
    result = collect_audit_log_task_ids(@audit_path)
    assert_equal 2, result.length
  end

  def test_returns_empty_when_file_absent
    assert_equal [], collect_audit_log_task_ids(File.join(@tmpdir, 'nonexistent.md'))
  end
end

# ── 整合情境（DoD 三情境）─────────────────────────────────────────────────────
class TestIntegrationScenarios < Minitest::Test
  def setup
    @tmpdir = Dir.mktmpdir
    @tasks_dir = File.join(@tmpdir, 'tasks')
    @audit_path = File.join(@tmpdir, 'AUDIT_LOG.md')
    FileUtils.mkdir_p(@tasks_dir)
  end

  def teardown
    FileUtils.remove_entry(@tmpdir)
  end

  def test_scenario_齊全_no_missing
    File.write(File.join(@tasks_dir, 'a.yaml'),
               { 'task_id' => '20260427-A01', 'status' => 'done' }.to_yaml)
    File.write(@audit_path, "```yaml\n- task_id: \"20260427-A01\"\n```\n")

    completed = collect_completed_task_ids(File.join(@tasks_dir, '**/*.yaml'))
    audit_ids = collect_audit_log_task_ids(@audit_path)
    missing = completed.reject { |t| audit_ids.include?(t[:task_id]) }

    assert_empty missing
  end

  def test_scenario_漏記_one_missing
    File.write(File.join(@tasks_dir, 'a.yaml'),
               { 'task_id' => '20260427-A01', 'status' => 'done' }.to_yaml)
    File.write(File.join(@tasks_dir, 'b.yaml'),
               { 'task_id' => '20260427-B01', 'status' => 'done' }.to_yaml)
    File.write(@audit_path, "```yaml\n- task_id: \"20260427-A01\"\n```\n")

    completed = collect_completed_task_ids(File.join(@tasks_dir, '**/*.yaml'))
    audit_ids = collect_audit_log_task_ids(@audit_path)
    missing = completed.reject { |t| audit_ids.include?(t[:task_id]) }

    assert_equal 1, missing.length
    assert_equal '20260427-B01', missing.first[:task_id]
  end

  def test_scenario_task_id_format_invalid_skipped
    File.write(File.join(@tasks_dir, 'bad.yaml'),
               { 'task_id' => 'NOT-A-VALID-ID', 'status' => 'done' }.to_yaml)
    File.write(@audit_path, '')

    completed = collect_completed_task_ids(File.join(@tasks_dir, '**/*.yaml'))
    assert_empty completed
  end
end
