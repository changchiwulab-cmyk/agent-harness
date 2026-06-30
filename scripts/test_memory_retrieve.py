#!/usr/bin/env python3
"""Unit tests for scripts/memory_retrieve.py and scripts/build_memory_index.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_memory_index as idx
import memory_retrieve as mr


def write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


EPISODE = """\
episode_id: "20260101-E001"
date: "2026-01-01"
task_id: "20260101-001"
skill_type: "research"
goal: "investigate web search rate limit"
outcome: "partial"
tags: ["web-search", "rate-limit"]
lessons:
  - "keep one search round in reserve"
"""

PLAYBOOK = """\
# Research Playbook

<!-- ENTRY id=PB-research-001 skill=research tags=web-search,rate-limit -->
## keep one web search round in reserve
body text here.

<!-- ENTRY id=PB-research-002 skill=research tags=sources,quality -->
## bind every fact to a source
body text here.
"""


def make_repo(root: Path) -> None:
    write(root / "memory" / "episodes" / "20260101-E001_x.yaml", EPISODE)
    write(root / "memory" / "episodes" / "EPISODE_TEMPLATE.yaml", 'episode_id: ""\n')
    write(root / "memory" / "playbook" / "research.md", PLAYBOOK)
    write(root / "memory" / "playbook" / "PLAYBOOK_ENTRY_TEMPLATE.md", "# template\n")


class TestIndexBuilder(unittest.TestCase):
    def test_collect_skips_template_and_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root)
            eps = idx.collect_episodes(root)
            pb = idx.collect_playbook(root)
            self.assertEqual([e["id"] for e in eps], ["20260101-E001"])
            self.assertEqual([p["id"] for p in pb], ["PB-research-001", "PB-research-002"])

    def test_playbook_entry_parsing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root)
            pb = idx.collect_playbook(root)
            first = pb[0]
            self.assertEqual(first["skill_type"], "research")
            self.assertEqual(first["tags"], ["web-search", "rate-limit"])
            self.assertEqual(first["title"], "keep one web search round in reserve")

    def test_dump_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root)
            a = idx.dump_index("episodes", idx.collect_episodes(root))
            b = idx.dump_index("episodes", idx.collect_episodes(root))
            self.assertEqual(a, b)
            self.assertIn("20260101-E001", a)


class TestRetrieve(unittest.TestCase):
    def _root(self, tmp: str) -> Path:
        root = Path(tmp)
        make_repo(root)
        # build indexes the retriever reads
        write(root / "memory" / "episodes" / "INDEX.yaml",
              idx.dump_index("episodes", idx.collect_episodes(root)))
        write(root / "memory" / "playbook" / "INDEX.yaml",
              idx.dump_index("entries", idx.collect_playbook(root)))
        return root

    def test_keyword_ranks_relevant_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)
            res = mr.retrieve("research", ["web search,rate limit"], root=root)
            self.assertTrue(res["playbook"])
            self.assertEqual(res["playbook"][0]["id"], "PB-research-001")
            self.assertTrue(res["episodes"])
            self.assertEqual(res["episodes"][0]["id"], "20260101-E001")

    def test_skill_only_filter_returns_that_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)
            res = mr.retrieve("research", [""], root=root)
            ids = {p["id"] for p in res["playbook"]}
            self.assertEqual(ids, {"PB-research-001", "PB-research-002"})

    def test_tag_match_outscores_text_match(self):
        item_tag = {"skill_type": "research", "tags": ["rate-limit"], "title": "x"}
        item_text = {"skill_type": "research", "tags": [], "title": "rate limit note"}
        kws = mr._norm_keywords(["rate limit"])
        self.assertGreater(
            mr.score_item(item_tag, "research", kws),
            mr.score_item(item_text, "research", kws),
        )

    def test_no_match_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)
            res = mr.retrieve("ops", ["nonexistent-keyword-xyz"], root=root)
            self.assertEqual(res["playbook"], [])
            self.assertEqual(res["episodes"], [])


if __name__ == "__main__":
    unittest.main()
