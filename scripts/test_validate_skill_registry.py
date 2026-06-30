#!/usr/bin/env python3
"""Unit tests for scripts/validate_skill_registry.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_skill_registry as vsr

ROOT = Path(__file__).resolve().parents[1]

REGISTRY_TMPL = """\
version: 1
skills:
{body}
"""

ENTRY = """\
  {name}:
    description: "d"
    path: "skills/{name}/"
    trigger_keywords: ["k"]
    token_budget: "10K"
    default_allowed_tools: ["file_read"]
"""


def make(root: Path, names: list[str], registered: list[str]) -> None:
    for n in names:
        (root / "skills" / n).mkdir(parents=True, exist_ok=True)
        (root / "skills" / n / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    body = "".join(ENTRY.format(name=n) for n in registered)
    (root / "skills" / "REGISTRY.yaml").write_text(REGISTRY_TMPL.format(body=body), encoding="utf-8")


class TestRealRegistry(unittest.TestCase):
    def test_repo_registry_is_consistent(self):
        self.assertEqual(vsr.validate(ROOT), [])


class TestSyntheticDrift(unittest.TestCase):
    def test_unregistered_dir_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make(root, ["research", "ops"], ["research"])  # ops on disk, not registered
            errs = vsr.validate(root)
            self.assertTrue(any("ops" in e and "not registered" in e for e in errs))

    def test_phantom_registration_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make(root, ["research"], ["research", "review"])  # review registered, no dir
            errs = vsr.validate(root)
            self.assertTrue(any("review" in e and "no skills" in e for e in errs))

    def test_missing_field_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "skills" / "research").mkdir(parents=True)
            (root / "skills" / "research" / "SKILL.md").write_text("# s\n", encoding="utf-8")
            (root / "skills" / "REGISTRY.yaml").write_text(
                'version: 1\nskills:\n  research:\n    description: "d"\n', encoding="utf-8")
            errs = vsr.validate(root)
            self.assertTrue(any("missing/empty field" in e for e in errs))

    def test_noncanonical_skill_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make(root, ["frobnicate"], ["frobnicate"])
            errs = vsr.validate(root)
            self.assertTrue(any("canonical" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
