#!/usr/bin/env python3
"""Unit tests for scripts/output_scan.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import output_scan as osn


class TestSecretDetection(unittest.TestCase):
    def test_flags_real_looking_secrets(self):
        for s, rule in [
            ("token: ghp_" + "a" * 36, "github_token"),
            ("key sk-ant-" + "b" * 24, "anthropic_key"),
            ("my id is A123456789 here", "tw_national_id"),
            ('api_key = "s3cr3tValue1234567890"', "generic_secret"),
            ("-----BEGIN RSA PRIVATE KEY-----", "private_key"),
        ]:
            rules = {f.rule_id for f in osn.scan_text(s)}
            self.assertIn(rule, rules, f"expected {rule} for {s!r}")

    def test_placeholder_is_ignored(self):
        self.assertEqual(osn.scan_text("aws_key = AKIAIOSFODNN7EXAMPLE"), [])
        self.assertEqual(osn.scan_text('api_key = "your_api_key_here_xxxx"'), [])

    def test_hyphenated_openai_project_key_is_flagged(self):
        # Codex review: current sk-proj-/sk-svcacct- keys contain hyphens and
        # were missed by the legacy sk-<alnum> rule.
        s = "OPENAI_API_KEY=sk-proj-" + "a" * 40
        rules = {f.rule_id for f in osn.scan_text(s)}
        self.assertIn("openai_key", rules)

    def test_word_on_line_does_not_suppress_real_secret(self):
        # Codex review: 'tested token: ghp_...' must NOT be suppressed just
        # because the line mentions "test" — only the matched value is checked.
        self.assertTrue(osn.scan_text("tested token: ghp_" + "a" * 36))

    def test_luhn_filters_invalid_cards(self):
        self.assertTrue(osn.scan_text("card 4111 1111 1111 1111"))   # valid Luhn
        self.assertEqual(osn.scan_text("card 4111 1111 1111 1112"), [])  # invalid Luhn

    def test_allowlist_marker_skips_line(self):
        line = "token: ghp_" + "a" * 36 + "  [scan-ignore]"
        self.assertEqual(osn.scan_text(line), [])

    def test_clean_prose_has_no_findings(self):
        self.assertEqual(osn.scan_text("這是一份普通的研究草稿，沒有任何機密。"), [])

    def test_preview_is_redacted(self):
        findings = osn.scan_text("token: ghp_" + "a" * 36)
        self.assertTrue(findings)
        self.assertNotIn("a" * 36, findings[0].preview)


class TestScanPaths(unittest.TestCase):
    def test_scan_dir_reports_file_and_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "outputs" / "drafts"
            d.mkdir(parents=True)
            (d / "leak.md").write_text("line one\napi_key = aZ09kqstuvLMNO7654321\n", encoding="utf-8")
            (d / "clean.md").write_text("nothing to see here\n", encoding="utf-8")
            report = osn.scan_paths(["outputs/drafts"], root=root)
            self.assertFalse(report.clean)
            self.assertEqual(report.findings[0].line, 2)
            self.assertTrue(report.findings[0].path.endswith("leak.md"))

    def test_clean_dir_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "outputs" / "drafts"
            d.mkdir(parents=True)
            (d / "ok.md").write_text("# report\n結論先行\n", encoding="utf-8")
            self.assertTrue(osn.scan_paths(["outputs/drafts"], root=root).clean)


if __name__ == "__main__":
    unittest.main()
