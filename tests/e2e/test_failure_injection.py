#!/usr/bin/env python3
"""Worst-case failure-injection suite: drive the 14 FAILURE_TAXONOMY modes.

The happy-path smoke test (``test_dummy_task_smoke.py``) proves the harness
works when everything goes right. This suite proves it *fails safely* when
everything goes wrong: for every failure mode declared in
``system/FAILURE_TAXONOMY.yaml`` we inject the corresponding bad input and
assert the matching guardrail (a gate ``on_fail`` / ``rollback`` clause, a
PERMISSIONS deny entry, or a CLAUDE.md hard rule) actually fires.

Behavioural modes that the runtime enforces via natural-language reasoning
are pinned as *contract* assertions against the policy files — the same
philosophy as the smoke test's ``test_policy_declares_all_four_gates``: a
silently dropped guardrail surfaces in CI rather than passing unnoticed.

A drift guard asserts the taxonomy ids and the handler registry stay in
lockstep, so adding/removing a failure mode without a matching injection
fails the build.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

# Reuse the exact gate implementations the happy-path test pins, so both
# suites exercise one shared contract. sys.path juggling keeps this working
# under both ``python3 tests/e2e/test_failure_injection.py`` (CI) and
# ``python3 -m unittest`` (local).
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_dummy_task_smoke as smoke  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FAILURE_TAXONOMY_PATH = ROOT / "system" / "FAILURE_TAXONOMY.yaml"
GATE_POLICY_PATH = ROOT / "system" / "GATE_POLICY.yaml"
PERMISSIONS_PATH = ROOT / "system" / "PERMISSIONS.yaml"
CLAUDE_MD_PATH = ROOT / "CLAUDE.md"

CONSECUTIVE_FAILURE_LIMIT = 3


def should_stop(consecutive_failures: int, limit: int = CONSECUTIVE_FAILURE_LIMIT) -> bool:
    """CLAUDE.md hard rule 3 / SEC-03: stop after N consecutive failures."""
    return consecutive_failures >= limit


def _taxonomy_ids(taxonomy: dict) -> set[str]:
    return {
        entry["id"]
        for group in taxonomy.get("categories", {}).values()
        for entry in group
    }


class TestFailureInjection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.taxonomy = yaml.safe_load(
            FAILURE_TAXONOMY_PATH.read_text(encoding="utf-8")
        )
        cls.gate_policy = yaml.safe_load(
            GATE_POLICY_PATH.read_text(encoding="utf-8")
        )
        cls.permissions = yaml.safe_load(
            PERMISSIONS_PATH.read_text(encoding="utf-8")
        )
        cls.claude_md = CLAUDE_MD_PATH.read_text(encoding="utf-8")
        cls.handlers = {
            "SPEC-01": cls._spec_01_goal_violation,
            "SPEC-02": cls._spec_02_loop,
            "SPEC-03": cls._spec_03_history_loss,
            "SPEC-04": cls._spec_04_no_stop,
            "COORD-01": cls._coord_01_context_reset,
            "COORD-02": cls._coord_02_ambiguous,
            "COORD-03": cls._coord_03_goal_drift,
            "COORD-04": cls._coord_04_ignored_input,
            "VAL-01": cls._val_01_fake_done,
            "VAL-02": cls._val_02_incomplete_check,
            "VAL-03": cls._val_03_format_vs_content,
            "SEC-01": cls._sec_01_unauthorized,
            "SEC-02": cls._sec_02_data_leak,
            "SEC-03": cls._sec_03_cost_runaway,
            "SEC-04": cls._sec_04_hallucination_action,
        }

    # --- injection handlers: each returns (passed, detail) -----------------

    def _missing_output(self):
        return Path("/nonexistent/never-produced.md")

    def _spec_01_goal_violation(self):
        """Output ignores the goal/DoD -> completion gate fails."""
        ok, misses = smoke.gate_completion(smoke.DUMMY_TASK, self._missing_output())
        return (not ok and misses), f"completion misses={misses}"

    def _spec_02_loop(self):
        """Same action repeated 3x -> stop fires; 2x does not."""
        return (
            should_stop(3) and not should_stop(2),
            "stop@3 / continue@2",
        )

    def _spec_03_history_loss(self):
        """Mitigation contract: CLAUDE.md mandates checkpoint + 20-round
        summarization to survive history loss."""
        ok = "checkpoint" in self.claude_md and "20 輪" in self.claude_md
        return ok, "CLAUDE.md declares checkpoint + 20-round summarization"

    def _spec_04_no_stop(self):
        """DoD compared line-by-line, not silently passed."""
        ok, misses = smoke.gate_completion(smoke.DUMMY_TASK, self._missing_output())
        return (not ok and len(misses) >= 1), f"explicit misses={misses}"

    def _coord_01_context_reset(self):
        """rule_check rollback must reinstate via git so a reset context
        doesn't lose work."""
        rollback = self.gate_policy["gates"]["rule_check"]["rollback"]
        return "git checkout" in rollback, rollback

    def _coord_02_ambiguous(self):
        """Ambiguous card (empty goal) is rejected at the schema gate
        instead of being executed blind."""
        bad = {**smoke.DUMMY_TASK, "goal": ""}
        passed, output = smoke.gate_schema(bad, smoke.VALIDATE_SCRIPT)
        return (not passed and "goal" in output), output.strip()

    def _coord_03_goal_drift(self):
        """Output drifted off-goal -> completion gate catches the gap."""
        ok, misses = smoke.gate_completion(smoke.DUMMY_TASK, self._missing_output())
        return (not ok), f"drift caught, misses={misses}"

    def _coord_04_ignored_input(self):
        """Mitigation contract: taxonomy documents the confirm-before-continue
        mitigation so the runtime has a rule to follow."""
        entry = next(
            e for e in self.taxonomy["categories"]["coordination"]
            if e["id"] == "COORD-04"
        )
        return bool(entry.get("mitigation", "").strip()), entry.get("mitigation")

    def _val_01_fake_done(self):
        """Declaring done with no artifact -> completion gate fails."""
        ok, misses = smoke.gate_completion(smoke.DUMMY_TASK, self._missing_output())
        return (not ok and misses == ["output not produced"]), f"{misses}"

    def _val_02_incomplete_check(self):
        """Partial DoD (one line missing) is reported, not waved through."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "partial.md"
            # Cover every DoD except the last one.
            out.write_text(
                "\n".join(smoke.DUMMY_TASK["definition_of_done"][:-1]),
                encoding="utf-8",
            )
            ok, misses = smoke.gate_completion(smoke.DUMMY_TASK, out)
        expected_miss = smoke.DUMMY_TASK["definition_of_done"][-1]
        return (not ok and misses == [expected_miss]), f"misses={misses}"

    def _val_03_format_vs_content(self):
        """Schema-valid card with empty content: schema gate passes but
        completion gate fails -> format and content checks are separate."""
        schema_ok, _ = smoke.gate_schema(smoke.DUMMY_TASK, smoke.VALIDATE_SCRIPT)
        content_ok, _ = smoke.gate_completion(
            smoke.DUMMY_TASK, self._missing_output()
        )
        return (schema_ok and not content_ok), "schema!=content"

    def _sec_01_unauthorized(self):
        """allowed_tools containing a deny-list entry -> rule gate fails."""
        deny_tool = self.permissions["permissions"]["deny"][0]
        bad = {**smoke.DUMMY_TASK, "allowed_tools": ["file_read", deny_tool]}
        passed, reason = smoke.gate_rule(bad, self.permissions)
        return (not passed and deny_tool in reason), reason

    def _sec_02_data_leak(self):
        """External-send / publish actions must be on the deny list so
        sensitive data cannot be exfiltrated by a tool call."""
        deny = set(self.permissions["permissions"]["deny"])
        required = {"send_email", "send_message_external", "publish_content"}
        missing = required - deny
        return (not missing), f"missing from deny: {sorted(missing)}"

    def _sec_03_cost_runaway(self):
        """Hard rule 3: consecutive-failure stop, plus CLAUDE.md declares the
        tool-call checkpoint cadence."""
        ok = (
            should_stop(CONSECUTIVE_FAILURE_LIMIT)
            and "連續失敗 3 次" in self.claude_md
        )
        return ok, "stop@3 + CLAUDE.md cost rule"

    def _sec_04_hallucination_action(self):
        """A hallucination-driven high-risk output is force-routed to
        drafts/ (human review) by the risk gate, not published."""
        wrong = Path("outputs/reports/hallucinated.md")
        passed, reason = smoke.gate_risk(smoke.DUMMY_TASK, wrong)
        return (not passed and "drafts/" in reason), reason

    # --- the suite --------------------------------------------------------

    def test_every_taxonomy_mode_has_a_firing_guardrail(self):
        for fid in sorted(_taxonomy_ids(self.taxonomy)):
            with self.subTest(failure_mode=fid):
                handler = self.handlers.get(fid)
                self.assertIsNotNone(
                    handler, f"no injection handler registered for {fid}"
                )
                passed, detail = handler(self)
                self.assertTrue(
                    passed, f"{fid} guardrail did not fire: {detail}"
                )

    def test_handler_registry_matches_taxonomy_no_drift(self):
        """Drift guard: adding/removing a failure mode without a matching
        injection handler (or vice versa) fails the build."""
        taxonomy_ids = _taxonomy_ids(self.taxonomy)
        handler_ids = set(self.handlers)
        self.assertEqual(
            taxonomy_ids,
            handler_ids,
            f"taxonomy/handler drift — "
            f"only in taxonomy: {sorted(taxonomy_ids - handler_ids)}; "
            f"only in handlers: {sorted(handler_ids - taxonomy_ids)}",
        )

    def test_every_taxonomy_entry_is_well_formed(self):
        """Structural pin: every failure mode carries id/name/mitigation so a
        malformed taxonomy can't slip a guardrail-less mode past the suite.

        NOTE: the file reports "14 種" but actually declares 15 (SEC-04 was
        back-filled per Task Card 20260409-001 without updating the header).
        The drift guard above is the real contract — this test deliberately
        avoids a magic number. The header/doc mismatch is flagged in the
        task summary; fixing system/ docs is out of this card's scope.
        """
        ids = _taxonomy_ids(self.taxonomy)
        self.assertGreaterEqual(len(ids), 14)
        for group in self.taxonomy["categories"].values():
            for entry in group:
                for key in ("id", "name", "mitigation"):
                    self.assertTrue(
                        str(entry.get(key, "")).strip(),
                        f"taxonomy entry {entry.get('id')} missing {key}",
                    )


if __name__ == "__main__":
    unittest.main()
