#!/usr/bin/env python3
"""Unit tests for system/validate_task_card.py"""

import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "system"))
from validate_task_card import validate


class TestValidateTaskCardStructure(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def _write(self, name: str, content: str) -> Path:
        path = self.tmp / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_root_must_be_mapping(self):
        path = self._write("root_list.yaml", "- item\n")
        errors = validate(str(path))
        self.assertEqual(errors, ["YAML 根節點必須是 mapping/object"])

    def test_expected_output_must_be_mapping(self):
        path = self._write(
            "bad_output.yaml",
            "\n".join(
                [
                    "task_id: 20260422-001",
                    "date: 2026-04-22",
                    "goal: test",
                    "definition_of_done:",
                    "  - done",
                    "skill_type: review",
                    "risk_level: low",
                    'expected_output: "not-a-map"',
                    "",
                ]
            ),
        )
        errors = validate(str(path))
        self.assertEqual(errors, ["expected_output 必須是 mapping/object"])

    def test_expected_output_none_is_rejected(self):
        path = self._write(
            "none_output.yaml",
            "\n".join(
                [
                    "task_id: 20260422-002",
                    "date: 2026-04-22",
                    "goal: test",
                    "definition_of_done:",
                    "  - done",
                    "skill_type: review",
                    "risk_level: low",
                    "expected_output: null",
                    "",
                ]
            ),
        )
        errors = validate(str(path))
        self.assertEqual(errors, ["expected_output 必須是 mapping/object"])


if __name__ == "__main__":
    unittest.main()
