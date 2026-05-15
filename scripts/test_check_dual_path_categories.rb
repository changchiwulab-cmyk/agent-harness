#!/usr/bin/env ruby
# frozen_string_literal: true

require 'minitest/autorun'
require 'tmpdir'
require 'yaml'
require 'fileutils'

SCRIPT = File.expand_path('check_dual_path_categories.rb', __dir__)

class TestCheckDualPathCategories < Minitest::Test
  def run_checker(args, chdir: nil)
    cmd = ['ruby', SCRIPT, *args]
    if chdir
      Dir.chdir(chdir) { `#{cmd.join(' ')} 2>&1` }
    else
      `#{cmd.join(' ')} 2>&1`
    end
  end

  def dual_yaml(status: 'partial', cat: 'D', py: 'pending', fb: 'pending')
    {
      'execution_log' => {
        'status' => status,
        'comparison_results' => (1..10).map do |i|
          {
            'index' => i,
            'task_file' => "tasks/#{i}.yaml",
            'python_result' => py,
            'fallback_result' => fb,
            'diff_category' => cat,
            'note' => ''
          }
        end
      }
    }
  end

  def test_no_file_pattern_is_ok
    Dir.mktmpdir do |dir|
      FileUtils.mkdir_p(File.join(dir, 'logs', 'runs'))
      out = run_checker([], chdir: dir)
      assert_includes out, 'OK: no dual-path run files found'
    end
  end

  def test_completed_with_pending_fails
    Dir.mktmpdir do |dir|
      path = File.join(dir, 'dual.yaml')
      File.write(path, dual_yaml(status: 'completed', py: 'pending', fb: 'pass').to_yaml)
      out = run_checker([path])
      assert_includes out, 'FAILED: dual-path category checks found issues:'
      assert_includes out, 'completed status cannot contain pending'
    end
  end

  def test_invalid_category_fails
    Dir.mktmpdir do |dir|
      path = File.join(dir, 'dual.yaml')
      File.write(path, dual_yaml(cat: 'Z').to_yaml)
      out = run_checker([path])
      assert_includes out, 'FAILED: dual-path category checks found issues:'
      assert_includes out, 'diff_category must be one of A/B/C/D'
    end
  end

  def test_valid_file_passes
    Dir.mktmpdir do |dir|
      path = File.join(dir, 'dual.yaml')
      File.write(path, dual_yaml(status: 'completed', py: 'pass', fb: 'pass').to_yaml)
      out = run_checker([path])
      assert_includes out, 'OK: dual-path category checks passed (1 file(s))'
    end
  end
end
