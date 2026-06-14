#!/usr/bin/env python3
"""Unit tests for scripts/run_evals.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_evals

SAMPLE = """# Skill — 評測範例

## 好的輸出範例

```markdown
# Title

## 結論
ok

## 來源
- a
```

**為什麼好**：...

## 壞的輸出範例

```markdown
# Title

just prose with no sections
```

## 判斷標準
table
"""


class TestParsing(unittest.TestCase):
    def test_extract_good_and_bad_blocks(self):
        good = run_evals._extract_block_after(SAMPLE, run_evals.GOOD_HEADER)
        bad = run_evals._extract_block_after(SAMPLE, run_evals.BAD_HEADER)
        self.assertIn("## 結論", good)
        self.assertIn("## 來源", good)
        self.assertNotIn("結論", bad)

    def test_section_titles_skips_top_level(self):
        titles = run_evals.section_titles("# Title\n## 結論\n### 細項\n")
        self.assertEqual(titles, ["結論", "細項"])

    def test_conformance(self):
        rubric = ["結論", "來源"]
        self.assertEqual(run_evals.conformance("## 結論\n## 來源\n", rubric), 1.0)
        self.assertEqual(run_evals.conformance("## 結論\n", rubric), 0.5)
        self.assertEqual(run_evals.conformance("no headers", rubric), 0.0)


class TestEvalSkill(unittest.TestCase):
    def _write(self, body: str) -> Path:
        d = Path(tempfile.mkdtemp()) / "demo"
        d.mkdir()
        p = d / "eval_examples.md"
        p.write_text(body, encoding="utf-8")
        return p

    def test_discriminating_skill_passes(self):
        r = run_evals.eval_skill(self._write(SAMPLE))
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["good_score"], 1.0)
        self.assertEqual(r["bad_score"], 0.0)

    def test_missing_bad_block_fails(self):
        body = SAMPLE.split("## 壞的輸出範例")[0]
        r = run_evals.eval_skill(self._write(body))
        self.assertFalse(r["ok"])


class TestRealRepo(unittest.TestCase):
    def test_all_skills_pass_structural_eval(self):
        results = run_evals.run_all()
        self.assertGreaterEqual(len(results), 5)
        failing = [r["skill"] for r in results if not r["ok"]]
        self.assertEqual(failing, [], f"skills failing structural eval: {failing}")


if __name__ == "__main__":
    unittest.main()
