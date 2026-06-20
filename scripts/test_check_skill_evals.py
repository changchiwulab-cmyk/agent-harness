#!/usr/bin/env python3
"""Unit tests for scripts/check_skill_evals.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_skill_evals as cse


class TestCheckSkill(unittest.TestCase):
    def _skill(self, tmp: Path, name: str, *, skill_md=True, evals_text=None) -> Path:
        d = tmp / name
        d.mkdir()
        if skill_md:
            (d / "SKILL.md").write_text("# x\n", encoding="utf-8")
        if evals_text is not None:
            (d / "eval_examples.md").write_text(evals_text, encoding="utf-8")
        return d

    def test_ok_when_good_and_bad_present(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            d = self._skill(
                tmp, "research",
                evals_text="## 好的輸出範例\n...\n## 壞的輸出範例\n...\n",
            )
            self.assertEqual(cse.check_skill(d), [])

    def test_flags_missing_bad_example(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            d = self._skill(tmp, "writing", evals_text="## 好的輸出範例\nonly good\n")
            problems = cse.check_skill(d)
            self.assertTrue(any("壞的輸出範例" in p for p in problems))

    def test_flags_missing_eval_file(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            d = self._skill(tmp, "ops", evals_text=None)
            problems = cse.check_skill(d)
            self.assertTrue(any("eval_examples.md" in p for p in problems))

    def test_flags_missing_skill_md(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            d = self._skill(
                tmp, "review", skill_md=False,
                evals_text="好的輸出範例 / 壞的輸出範例",
            )
            problems = cse.check_skill(d)
            self.assertTrue(any("SKILL.md" in p for p in problems))


class TestRealRepo(unittest.TestCase):
    def test_real_repo_passes(self):
        # The actual skills/ tree must satisfy the structural check.
        problems, checked = cse.collect_problems()
        self.assertEqual(problems, [])
        self.assertGreaterEqual(checked, 5)


if __name__ == "__main__":
    unittest.main()
