#!/usr/bin/env python3
"""Unit tests for system/validate_task_card.py."""

import tempfile
import unittest
from unittest import mock
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "system" / "validate_task_card.py"
spec = importlib.util.spec_from_file_location("validate_task_card", VALIDATOR_PATH)
module = importlib.util.module_from_spec(spec)
if spec is None or spec.loader is None:
    raise RuntimeError("unable to load system/validate_task_card.py for tests")
spec.loader.exec_module(module)
validate = module.validate


class TestValidateTaskCardRootType(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def _write_yaml_text(self, name: str, text: str) -> Path:
        p = self.tmpdir / name
        p.write_text(text, encoding="utf-8")
        return p

    def test_root_none_returns_human_readable_error(self):
        path = self._write_yaml_text("none.yaml", "null\n")
        fake_yaml = mock.Mock()
        fake_yaml.safe_load.return_value = None
        with mock.patch.object(module, "_load_yaml_module", return_value=fake_yaml):
            self.assertEqual(validate(str(path)), ["YAML root 必須是 mapping/object"])

    def test_root_list_returns_human_readable_error(self):
        path = self._write_yaml_text("list.yaml", "- a\n- b\n")
        fake_yaml = mock.Mock()
        fake_yaml.safe_load.return_value = ["a", "b"]
        with mock.patch.object(module, "_load_yaml_module", return_value=fake_yaml):
            self.assertEqual(validate(str(path)), ["YAML root 必須是 mapping/object"])

    def test_root_string_returns_human_readable_error(self):
        path = self._write_yaml_text("str.yaml", "hello\n")
        fake_yaml = mock.Mock()
        fake_yaml.safe_load.return_value = "hello"
        with mock.patch.object(module, "_load_yaml_module", return_value=fake_yaml):
            self.assertEqual(validate(str(path)), ["YAML root 必須是 mapping/object"])


class TestExpectedOutputLocation(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def _write_yaml_text(self, name: str, text: str) -> Path:
        p = self.tmpdir / name
        p.write_text(text, encoding="utf-8")
        return p

    def test_missing_location_is_reported(self):
        path = self._write_yaml_text("missing_location.yaml", "dummy: true\n")
        fake_yaml = mock.Mock()
        fake_yaml.safe_load.return_value = {
            "task_id": "20260421-001",
            "date": "2026-04-21",
            "goal": "test",
            "definition_of_done": ["done"],
            "skill_type": "analysis",
            "risk_level": "low",
            "status": "pending",
            "expected_output": {"format": "md", "filename": "out.md"},
        }
        with mock.patch.object(module, "_load_yaml_module", return_value=fake_yaml):
            errors = validate(str(path))
        self.assertIn("expected_output.location 不能為空", errors)

    def test_with_location_passes_location_check(self):
        path = self._write_yaml_text("with_location.yaml", "dummy: true\n")
        fake_yaml = mock.Mock()
        fake_yaml.safe_load.return_value = {
            "task_id": "20260421-001",
            "date": "2026-04-21",
            "goal": "test",
            "definition_of_done": ["done"],
            "skill_type": "analysis",
            "risk_level": "low",
            "status": "pending",
            "expected_output": {
                "format": "md",
                "location": "outputs/drafts/",
                "filename": "out.md",
            },
        }
        with mock.patch.object(module, "_load_yaml_module", return_value=fake_yaml):
            errors = validate(str(path))
        self.assertNotIn("expected_output.location 不能為空", errors)


class TestYamlDependencyGuard(unittest.TestCase):
    def test_missing_pyyaml_returns_readable_error(self):
        with mock.patch.object(module, "_load_yaml_module", return_value=None):
            errors = validate("tasks/TASK_CARD_TEMPLATE.yaml")
        self.assertEqual(errors, ["缺少相依套件：PyYAML（請先執行：pip install pyyaml）"])


if __name__ == "__main__":
    unittest.main()
