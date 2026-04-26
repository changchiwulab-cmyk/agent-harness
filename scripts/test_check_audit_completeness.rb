#!/usr/bin/env ruby
# frozen_string_literal: true

require 'minitest/autorun'
require 'tmpdir'
require 'fileutils'
require 'yaml'
require 'set'

load File.join(__dir__, 'check_audit_completeness.rb')

class TestExtractAuditTaskIds < Minitest::Test
  def with_tmp_audit
    Dir.mktmpdir do |dir|
      path = File.join(dir, 'AUDIT_LOG.md')
      yield path
    end
  end

  def test_extracts_quoted_task_ids
    with_tmp_audit do |path|
      File.write(path, <<~MD)
        # Audit Log

        ```yaml
        - task_id: "20260101-001"
          status: "done"
        ```

        ```yaml
        - task_id: "20260102-A01"
          status: "done"
        ```
      MD
      ids = extract_audit_task_ids(path)
      assert_equal %w[20260101-001 20260102-A01], ids
    end
  end

  def test_returns_empty_when_file_missing
    assert_equal [], extract_audit_task_ids('/nonexistent/path.md')
  end

  def test_skips_empty_task_id
    with_tmp_audit do |path|
      File.write(path, <<~MD)
        ```yaml
        - task_id: ""
        ```
      MD
      assert_equal [], extract_audit_task_ids(path)
    end
  end
end

class TestCollectTerminalTaskIds < Minitest::Test
  def with_tmp_tasks
    Dir.mktmpdir do |dir|
      tasks_dir = File.join(dir, 'tasks')
      FileUtils.mkdir_p(tasks_dir)
      yield tasks_dir
    end
  end

  def write_card(dir, name, fields)
    path = File.join(dir, name)
    File.write(path, fields.to_yaml)
    path
  end

  def test_collects_done_and_failed_only
    with_tmp_tasks do |tasks_dir|
      write_card(tasks_dir, 'a.yaml', { 'task_id' => '20260101-001', 'status' => 'done' })
      write_card(tasks_dir, 'b.yaml', { 'task_id' => '20260102-001', 'status' => 'failed' })
      write_card(tasks_dir, 'c.yaml', { 'task_id' => '20260103-001', 'status' => 'pending' })
      write_card(tasks_dir, 'd.yaml', { 'task_id' => '20260104-001', 'status' => 'in_progress' })

      records = collect_terminal_task_ids(File.join(tasks_dir, '*.yaml'))
      ids = records.map { |r| r[:task_id] }.sort
      assert_equal %w[20260101-001 20260102-001], ids
    end
  end

  def test_skips_template_files
    with_tmp_tasks do |tasks_dir|
      write_card(tasks_dir, 'TASK_CARD_TEMPLATE.yaml', { 'task_id' => '99999999-999', 'status' => 'done' })
      write_card(tasks_dir, 'real.yaml', { 'task_id' => '20260101-001', 'status' => 'done' })
      records = collect_terminal_task_ids(File.join(tasks_dir, '*.yaml'))
      ids = records.map { |r| r[:task_id] }
      assert_equal %w[20260101-001], ids
    end
  end
end

class TestFindMissing < Minitest::Test
  def test_returns_only_missing_records
    records = [
      { task_id: 'A', file: 'a.yaml', status: 'done' },
      { task_id: 'B', file: 'b.yaml', status: 'done' },
      { task_id: 'C', file: 'c.yaml', status: 'failed' }
    ]
    audit_set = %w[A C].to_set
    missing = find_missing(records, audit_set)
    assert_equal %w[B], missing.map { |r| r[:task_id] }
  end

  def test_returns_empty_when_all_audited
    records = [{ task_id: 'A', file: 'a.yaml', status: 'done' }]
    missing = find_missing(records, %w[A].to_set)
    assert_empty missing
  end
end

class TestRepoLevelInvariant < Minitest::Test
  def test_main_branch_has_full_audit_completeness
    repo_root = File.expand_path('..', __dir__)
    Dir.chdir(repo_root) do
      records = collect_terminal_task_ids(DEFAULT_TASKS_GLOB)
      audit_ids = extract_audit_task_ids(DEFAULT_AUDIT_LOG).to_set
      missing = find_missing(records, audit_ids)
      assert_empty missing,
                   "Repo audit completeness broken: #{missing.map { |r| r[:task_id] }.inspect}"
    end
  end
end
