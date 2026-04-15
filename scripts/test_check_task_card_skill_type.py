#!/usr/bin/env python3
"""Unit tests for check_task_card_skill_type.py"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check_task_card_skill_type import (
    ALLOWED_SKILL_TYPES,
    EXCLUDE_NAMES,
    collect_task_cards,
    extract_skill_type,
)


class TestExtractSkillType(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def _write(self, name: str, content: str) -> Path:
        p = self.tmp / name
        p.write_text(content, encoding="utf-8")
        return p

    def test_all_valid_skill_types_recognised(self):
        for skill in ALLOWED_SKILL_TYPES:
            path = self._write(f"{skill}.yaml", f"skill_type: {skill}\n")
            self.assertEqual(extract_skill_type(path), skill)

    def test_missing_field_returns_none(self):
        path = self._write("no_skill.yaml", "goal: test\n")
        self.assertIsNone(extract_skill_type(path))

    def test_empty_value_returns_none(self):
        path = self._write("empty.yaml", 'skill_type: ""\n')
        self.assertIsNone(extract_skill_type(path))

    def test_inline_comment_stripped(self):
        path = self._write("comment.yaml", "skill_type: research  # 研究任務\n")
        self.assertEqual(extract_skill_type(path), "research")

    def test_double_quoted_value(self):
        path = self._write("quoted.yaml", 'skill_type: "writing"\n')
        self.assertEqual(extract_skill_type(path), "writing")

    def test_single_quoted_value(self):
        path = self._write("squoted.yaml", "skill_type: 'ops'\n")
        self.assertEqual(extract_skill_type(path), "ops")

    def test_indented_field_not_matched(self):
        # skill_type 必須在行首（MULTILINE ^），縮排版不應被誤判
        path = self._write("indented.yaml", "nested:\n  skill_type: review\n")
        self.assertIsNone(extract_skill_type(path))


class TestAllowedSkillTypes(unittest.TestCase):
    def test_five_skills_defined(self):
        self.assertEqual(
            ALLOWED_SKILL_TYPES,
            {"research", "analysis", "writing", "ops", "review"},
        )


class TestExcludeNames(unittest.TestCase):
    def test_template_excluded(self):
        self.assertIn("TASK_CARD_TEMPLATE", EXCLUDE_NAMES)

    def test_decision_log_excluded(self):
        self.assertIn("DECISION_LOG_TEMPLATE", EXCLUDE_NAMES)

    def test_weekly_review_excluded(self):
        self.assertIn("WEEKLY_REVIEW_TEMPLATE", EXCLUDE_NAMES)


class TestCollectTaskCards(unittest.TestCase):
    def test_returns_list(self):
        cards = collect_task_cards()
        self.assertIsInstance(cards, list)

    def test_no_templates_in_result(self):
        cards = collect_task_cards()
        for card in cards:
            stem_upper = card.stem.upper().replace("-", "_").replace(" ", "_")
            for excl in EXCLUDE_NAMES:
                self.assertNotIn(excl, stem_upper, f"{card} should be excluded")


if __name__ == "__main__":
    unittest.main()
