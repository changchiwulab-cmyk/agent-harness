#!/usr/bin/env ruby
# frozen_string_literal: true

require 'minitest/autorun'
require 'tmpdir'
require 'set'

load File.join(__dir__, 'check_docs_parity.rb')

class TestExtractValidatorSkills < Minitest::Test
  def with_tmp_file(content)
    Dir.mktmpdir do |dir|
      path = File.join(dir, 'check.rb')
      File.write(path, content)
      yield path
    end
  end

  def test_extracts_allowed_skill_array
    with_tmp_file(<<~RUBY) do |path|
      ALLOWED_SKILL = %w[research writing ops review analysis].freeze
    RUBY
      assert_equal %w[research writing ops review analysis], extract_validator_skills(path)
    end
  end

  def test_returns_nil_when_constant_missing
    with_tmp_file('# no constant here') do |path|
      assert_nil extract_validator_skills(path)
    end
  end
end

class TestExtractReadmeSkills < Minitest::Test
  def with_tmp_file(content)
    Dir.mktmpdir do |dir|
      path = File.join(dir, 'README.md')
      File.write(path, content)
      yield path
    end
  end

  def test_extracts_inline_backtick_list
    with_tmp_file(<<~MD) do |path|
      填入 skill_type。`skill_type` 請使用：`research` / `analysis` / `writing` / `ops` / `review`。參考範例。
    MD
      assert_equal %w[research analysis writing ops review], extract_readme_skills(path)
    end
  end
end

class TestExtractTemplateSkills < Minitest::Test
  def with_tmp_file(content)
    Dir.mktmpdir do |dir|
      path = File.join(dir, 'TASK_CARD_TEMPLATE.yaml')
      File.write(path, content)
      yield path
    end
  end

  def test_extracts_skill_type_comment
    with_tmp_file(<<~YAML) do |path|
      skill_type: ""                 # research / analysis / writing / ops / review
    YAML
      assert_equal %w[research analysis writing ops review], extract_template_skills(path)
    end
  end

  def test_captures_unexpected_skill_so_drift_can_be_detected
    # Per Codex P2 review on PR #53: hard-coding the canonical tokens in the
    # parser would make the parity check blind to additions like "design",
    # because the extracted set would still equal canonical and the gate
    # would falsely report success. The parser must surface every token in
    # the comment so the parity comparison can fail on unexpected values.
    with_tmp_file(<<~YAML) do |path|
      skill_type: ""                 # research / analysis / writing / ops / review / design
    YAML
      assert_equal %w[research analysis writing ops review design], extract_template_skills(path)
    end
  end

  def test_returns_empty_when_comment_missing
    with_tmp_file(<<~YAML) do |path|
      skill_type: ""
    YAML
      assert_equal [], extract_template_skills(path)
    end
  end
end

class TestExtractRoutingSkills < Minitest::Test
  def with_tmp_file(content)
    Dir.mktmpdir do |dir|
      path = File.join(dir, 'ROUTING_RULES.md')
      File.write(path, content)
      yield path
    end
  end

  def test_extracts_table_skill_column
    with_tmp_file(<<~MD) do |path|
      | 任務關鍵字 | Skill | 說明 |
      |-----------|-------|------|
      | 調查、研究 | research | 資料蒐集 |
      | 決策、評估 | analysis | 決策支援 |
      | 撰寫、草稿 | writing | 內容產出 |
      | 整理、清洗 | ops | 營運操作 |
      | 審查、校對 | review | 品質審查 |
    MD
      assert_equal %w[research analysis writing ops review], extract_routing_skills(path)
    end
  end
end

class TestRepoLevelParity < Minitest::Test
  def test_main_branch_has_consistent_skill_set
    repo_root = File.expand_path('..', __dir__)
    Dir.chdir(repo_root) do
      validator = extract_validator_skills('scripts/check_spec_consistency.rb')
      readme = extract_readme_skills('README.md')
      template = extract_template_skills('tasks/TASK_CARD_TEMPLATE.yaml')
      routing = extract_routing_skills('system/ROUTING_RULES.md')

      canonical = CANONICAL_SKILLS.to_set
      [
        ['validator', validator],
        ['readme', readme],
        ['template', template],
        ['routing', routing]
      ].each do |label, skills|
        refute_nil skills, "#{label} extraction returned nil"
        assert_equal canonical, skills.to_set,
                     "#{label} skill set drifts from canonical: got #{skills.inspect}"
      end
    end
  end
end
