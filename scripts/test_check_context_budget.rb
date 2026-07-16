#!/usr/bin/env ruby
# frozen_string_literal: true

# Unit tests for check_context_budget.rb

require 'minitest/autorun'
require 'tmpdir'

load File.join(__dir__, 'check_context_budget.rb')

class TestEstimateTokens < Minitest::Test
  def test_nil_for_missing_file
    assert_nil estimate_tokens('does/not/exist.md')
  end

  def test_empty_file_is_zero
    Dir.mktmpdir do |dir|
      path = File.join(dir, 'empty.md')
      File.write(path, '')
      assert_equal 0, estimate_tokens(path)
    end
  end

  def test_rough_ratio_four_ascii_chars_per_token
    Dir.mktmpdir do |dir|
      path = File.join(dir, 'sample.md')
      File.write(path, 'a' * 40)
      # 40 ASCII / 4 = 10 tokens
      assert_equal 10, estimate_tokens(path)
    end
  end

  def test_rounds_up_partial_tokens
    Dir.mktmpdir do |dir|
      path = File.join(dir, 'sample.md')
      File.write(path, 'a' * 5)
      # 5 / 4 = 1.25 → ceil → 2
      assert_equal 2, estimate_tokens(path)
    end
  end

  def test_cjk_chars_count_as_one_token_each
    Dir.mktmpdir do |dir|
      path = File.join(dir, 'cjk.md')
      File.write(path, '任務執行框架')
      # 6 CJK chars × 1 = 6 tokens (conservative upper bound)
      assert_equal 6, estimate_tokens(path)
    end
  end

  def test_mixed_ascii_and_cjk
    Dir.mktmpdir do |dir|
      path = File.join(dir, 'mixed.md')
      File.write(path, 'abcd任務')
      # 4 ASCII / 4 = 1, 2 CJK × 1 = 2, total ceil(3) = 3
      assert_equal 3, estimate_tokens(path)
    end
  end

  def test_emoji_counts_as_non_ascii
    Dir.mktmpdir do |dir|
      path = File.join(dir, 'emoji.md')
      File.write(path, '🚀🔥')
      # 2 non-ASCII chars × 1 = 2
      assert_equal 2, estimate_tokens(path)
    end
  end
end

class TestConstants < Minitest::Test
  def test_budget_matches_claude_md_rule
    assert_equal 3_000, TOKEN_BUDGET
  end

  def test_target_files_include_both_sources
    assert_includes TARGET_FILES, 'CLAUDE.md'
    assert_includes TARGET_FILES, 'system/GLOBAL_RULES.md'
  end

  def test_ascii_chars_per_token_is_rough_estimate
    assert_equal 4, ASCII_CHARS_PER_TOKEN
  end

  def test_skill_budget_matches_claude_md_rule
    # CLAUDE.md「單一 skill prompt ≤ 1,500 tokens」
    assert_equal 1_500, SKILL_TOKEN_BUDGET
  end

  def test_skill_glob_targets_skill_prompts
    assert_equal 'skills/*/SKILL.md', SKILL_GLOB
  end

  def test_eval_glob_targets_eval_examples
    # eval_examples.md 僅 advisory 顯示，不計入預算（20260711-A01）
    assert_equal 'skills/*/eval_examples.md', EVAL_GLOB
  end
end

class TestSkillBudgets < Minitest::Test
  def test_all_current_skill_prompts_within_budget
    Dir.chdir(File.join(__dir__, '..')) do
      files = Dir.glob(SKILL_GLOB)
      refute_empty files, 'skills/*/SKILL.md 不應為空'
      files.each do |path|
        est = estimate_tokens(path)
        assert est <= SKILL_TOKEN_BUDGET,
               "#{path} 超出 skill prompt 預算（~#{est} > #{SKILL_TOKEN_BUDGET}）"
      end
    end
  end
end
