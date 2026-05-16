#!/usr/bin/env python3
"""Unit tests for scripts/migrate_audit_log.py.

Covers the one-time AUDIT_LOG migration contract:
  (a) the task_id="" format-spec example is skipped
  (b) a single ```yaml block holding two entries (the R01+R02 case) is split
  (c) operator `notes` survive verbatim into the 人工備註 section
  (d) re-running on an already-migrated file is a strict no-op (idempotent)
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import migrate_audit_log as mig


SPEC_BLOCK = '''# Audit Log

## 紀錄格式

```yaml
- task_id: ""
  date: ""
  notes: ""
```

## 紀錄（依時間倒序）

```yaml
- task_id: "20260404-R02"
  date: "2026-04-04"
  skill_type: "review"
  notes: "有條件通過。發現 2 個必須修改。"
  approval_given: false

- task_id: "20260404-R01"
  date: "2026-04-04"
  skill_type: "research"
  notes: "6 大類別 20+ 工具。web search 3 輪全部用完。"
  estimated_tokens: "~18K"
```

---

```yaml
- task_id: "20260515-001"
  date: "2026-05-15"
  notes: "前端/後端皆順利運行。"
  model_used: "—"
```
'''


class MigrateAuditLogTests(unittest.TestCase):
    def test_skips_empty_task_id(self) -> None:
        entries = mig.extract_entries(SPEC_BLOCK)
        ids = {e["task_id"] for e in entries}
        self.assertNotIn("", ids)
        self.assertEqual(
            ids, {"20260404-R02", "20260404-R01", "20260515-001"}
        )

    def test_two_entries_in_one_block_split(self) -> None:
        entries = mig.extract_entries(SPEC_BLOCK)
        r_ids = [e["task_id"] for e in entries if e["task_id"].startswith("20260404")]
        self.assertEqual(sorted(r_ids), ["20260404-R01", "20260404-R02"])

    def test_notes_preserved_verbatim(self) -> None:
        entries = mig.extract_entries(SPEC_BLOCK)
        section = mig.render_manual_section(entries)
        self.assertIn("6 大類別 20+ 工具。web search 3 輪全部用完。", section)
        self.assertIn("有條件通過。發現 2 個必須修改。", section)
        self.assertIn("estimated_tokens: ~18K", section)
        # approval_given: False must be rendered (not dropped as falsy)
        self.assertIn("approval_given: false", section)
        # placeholder model_used "—" must be dropped
        self.assertNotIn("model_used: —", section)
        # descending task_id order
        self.assertLess(
            section.index("### 20260515-001"), section.index("### 20260404-R02")
        )

    def test_idempotent_noop_when_markers_present(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "logs" / "AUDIT_LOG.md"
            log.parent.mkdir(parents=True)

            # First migration on hand-written source.
            log.write_text(SPEC_BLOCK, encoding="utf-8")
            self.assertEqual(mig.migrate(log), 0)
            after_first = log.read_text(encoding="utf-8")
            self.assertIn(mig.AUTO_BEGIN, after_first)
            self.assertIn("6 大類別 20+ 工具", after_first)

            # Simulate generate_audit_log having filled the AUTO body (no notes).
            mutated = after_first.replace(
                f"{mig.AUTO_BEGIN}\n\n{mig.AUTO_END}",
                f"{mig.AUTO_BEGIN}\n```yaml\ntask_id: 20260404-R01\n```\n{mig.AUTO_END}",
            )
            log.write_text(mutated, encoding="utf-8")

            # Re-run must be a strict no-op: manual notes untouched.
            self.assertEqual(mig.migrate(log), 0)
            self.assertEqual(log.read_text(encoding="utf-8"), mutated)
            self.assertIn("6 大類別 20+ 工具", log.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
