#!/usr/bin/env python3
"""Validator tests — validate_task_card + check_audit_format."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validate_task_card as vtc
import check_audit_format as caf


VALID_CARD = {
    "task_id": "20260509-XTEST",
    "date": "2026-05-09",
    "status": "pending",
    "goal": "test",
    "definition_of_done": ["alpha"],
    "expected_output": {"format": "md", "location": "outputs/drafts/", "filename": "x.md"},
    "risk_level": "low",
    "approval_needed": False,
    "allowed_tools": ["file_read"],
    "max_tool_calls": 5,
    "skill_type": "ops",
}


class TestValidateTaskCard(unittest.TestCase):
    def _write(self, card: dict) -> Path:
        f = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8")
        yaml.safe_dump(card, f, allow_unicode=True, sort_keys=False)
        f.close()
        return Path(f.name)

    def test_pass(self):
        path = self._write(VALID_CARD)
        self.assertEqual(vtc.validate(path), [])

    def test_missing_required_field_fails(self):
        bad = {**VALID_CARD}
        del bad["goal"]
        path = self._write(bad)
        errors = vtc.validate(path)
        self.assertTrue(any("goal" in e for e in errors), errors)

    def test_empty_dod_fails(self):
        bad = {**VALID_CARD, "definition_of_done": []}
        path = self._write(bad)
        errors = vtc.validate(path)
        self.assertTrue(any("definition_of_done" in e for e in errors), errors)

    def test_non_string_dod_items_fail(self):
        bad = {**VALID_CARD, "definition_of_done": [123, ["nested"]]}
        path = self._write(bad)
        errors = vtc.validate(path)
        self.assertTrue(any("definition_of_done[0]" in e and "int" in e for e in errors), errors)
        self.assertTrue(any("definition_of_done[1]" in e and "list" in e for e in errors), errors)

    def test_invalid_skill_type_fails(self):
        bad = {**VALID_CARD, "skill_type": "marketing"}
        path = self._write(bad)
        errors = vtc.validate(path)
        self.assertTrue(any("skill_type" in e for e in errors), errors)

    def test_invalid_risk_level_fails(self):
        bad = {**VALID_CARD, "risk_level": "extreme"}
        path = self._write(bad)
        errors = vtc.validate(path)
        self.assertTrue(any("risk_level" in e for e in errors), errors)

    def test_main_returns_exit_2_on_fail(self):
        bad = {**VALID_CARD}
        del bad["goal"]
        path = self._write(bad)
        self.assertEqual(vtc.main([str(path)]), 2)

    def test_main_returns_exit_0_on_pass(self):
        path = self._write(VALID_CARD)
        self.assertEqual(vtc.main([str(path)]), 0)

    def test_main_returns_exit_1_on_no_args(self):
        self.assertEqual(vtc.main([]), 1)


class TestCheckAuditFormat(unittest.TestCase):
    def _write(self, content: str) -> Path:
        f = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        f.write(content)
        f.close()
        return Path(f.name)

    def test_valid_audit_passes(self):
        content = """# Audit Log

```yaml
- task_id: "20260509-X01"
  date: "2026-05-09"
  status: "done"
```
"""
        path = self._write(content)
        self.assertEqual(caf.validate(path), [])

    def test_missing_required_key_fails(self):
        content = """# Audit Log

```yaml
- task_id: "20260509-X01"
  status: "done"
```
"""
        path = self._write(content)
        errors = caf.validate(path)
        self.assertTrue(any("date" in e for e in errors), errors)

    def test_invalid_task_id_fails(self):
        content = """# Audit Log

```yaml
- task_id: "bad-id"
  date: "2026-05-09"
  status: "done"
```
"""
        path = self._write(content)
        errors = caf.validate(path)
        self.assertTrue(any("task_id" in e for e in errors), errors)

    def test_invalid_status_fails(self):
        content = """# Audit Log

```yaml
- task_id: "20260509-X01"
  date: "2026-05-09"
  status: "shipped"
```
"""
        path = self._write(content)
        errors = caf.validate(path)
        self.assertTrue(any("status" in e for e in errors), errors)

    def test_unbalanced_auto_markers_fail(self):
        content = """# Audit Log

<!-- AUTO_AUDIT_BEGIN -->
<!-- AUTO_AUDIT_BEGIN -->
<!-- AUTO_AUDIT_END -->

```yaml
- task_id: "20260509-X01"
  date: "2026-05-09"
  status: "done"
```
"""
        path = self._write(content)
        errors = caf.validate(path)
        self.assertTrue(any("AUTO_AUDIT" in e for e in errors), errors)

    def test_main_exit_codes(self):
        good_path = self._write("""# Audit Log

```yaml
- task_id: "20260509-X01"
  date: "2026-05-09"
  status: "done"
```
""")
        self.assertEqual(caf.main([str(good_path)]), 0)
        self.assertEqual(caf.main([]), 1)


if __name__ == "__main__":
    unittest.main()
