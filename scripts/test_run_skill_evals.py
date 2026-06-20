#!/usr/bin/env python3
"""Offline unit tests for scripts/run_skill_evals.py (no network, no API key)."""

from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_skill_evals as cse
import run_skill_evals as rse

SAMPLE = """# X Skill — 評測範例

## 好的輸出範例

> 題目：x

```markdown
GOOD OUTPUT BODY
```

**為什麼好**：...

---

## 壞的輸出範例

```markdown
BAD OUTPUT BODY
```

**哪裡錯**：...

---

## 判斷標準

| 項目 | 通過 | 不通過 |
|------|------|--------|
| 來源 | 有來源 | 模糊引用 |
| 分類 | 區塊分開 | 混在一起 |
"""


class TestParser(unittest.TestCase):
    def test_parse_sample(self):
        p = cse.parse_eval_examples(SAMPLE)
        self.assertEqual(p["good"], "GOOD OUTPUT BODY")
        self.assertEqual(p["bad"], "BAD OUTPUT BODY")
        self.assertEqual([c["item"] for c in p["criteria"]], ["來源", "分類"])
        self.assertEqual(p["criteria"][0]["pass"], "有來源")
        self.assertEqual(p["criteria"][0]["fail"], "模糊引用")

    def test_parse_real_research(self):
        text = (cse.SKILLS_DIR / "research" / "eval_examples.md").read_text(encoding="utf-8")
        p = cse.parse_eval_examples(text)
        self.assertTrue(p["good"] and p["bad"])
        items = [c["item"] for c in p["criteria"]]
        self.assertIn("來源", items)
        self.assertEqual(len(items), 4)  # 來源/分類/結論/誠實


class TestAggregateGolden(unittest.TestCase):
    def _crit(self, n):
        return [{"item": f"c{i}", "pass": "p", "fail": "f"} for i in range(n)]

    def test_aggregate_counts(self):
        crit = self._crit(3)
        verdicts = [
            {"item": "c0", "verdict": "pass", "reason": "r"},
            {"item": "c1", "verdict": "fail", "reason": "r"},
            # c2 omitted -> counts as fail
        ]
        agg = rse.aggregate(crit, verdicts)
        self.assertEqual(agg["total"], 3)
        self.assertEqual(agg["passed"], 1)
        self.assertEqual(agg["failed"], 2)

    def test_golden_ok(self):
        good = rse.aggregate(self._crit(4), [{"item": f"c{i}", "verdict": "pass", "reason": ""} for i in range(4)])
        bad = rse.aggregate(self._crit(4), [{"item": f"c{i}", "verdict": "fail", "reason": ""} for i in range(4)])
        ok, reasons = rse.golden_verdict(good, bad)
        self.assertTrue(ok, reasons)

    def test_golden_fails_when_good_rejected(self):
        good = rse.aggregate(self._crit(4), [{"item": f"c{i}", "verdict": "fail", "reason": ""} for i in range(4)])
        bad = rse.aggregate(self._crit(4), [{"item": f"c{i}", "verdict": "fail", "reason": ""} for i in range(4)])
        ok, reasons = rse.golden_verdict(good, bad)
        self.assertFalse(ok)
        self.assertTrue(any("good" in r for r in reasons))

    def test_golden_fails_when_bad_passes(self):
        good = rse.aggregate(self._crit(4), [{"item": f"c{i}", "verdict": "pass", "reason": ""} for i in range(4)])
        bad = rse.aggregate(self._crit(4), [{"item": f"c{i}", "verdict": "pass", "reason": ""} for i in range(4)])
        ok, reasons = rse.golden_verdict(good, bad)
        self.assertFalse(ok)
        self.assertTrue(any("bad" in r for r in reasons))


class TestCli(unittest.TestCase):
    def test_mock_runs_offline_exit_0(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = rse.main(["--mock", "--today", "2026-06-20", "--no-write"])
        self.assertEqual(code, 0)
        self.assertIn("Skill Evals", out.getvalue())

    def test_no_api_key_skips_exit_0(self):
        out = io.StringIO()
        with mock.patch.dict("os.environ", {}, clear=True):
            with redirect_stdout(out):
                code = rse.main(["--today", "2026-06-20", "--no-write"])
        self.assertEqual(code, 0)
        self.assertIn("skipped", out.getvalue())

    def test_real_skills_discovered(self):
        skills = rse.discover_skills()
        names = {s["name"] for s in skills}
        self.assertGreaterEqual(len(names), 5)
        for s in skills:
            self.assertTrue(s["good"] and s["bad"] and s["criteria"])


if __name__ == "__main__":
    unittest.main()
