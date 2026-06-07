#!/usr/bin/env python3
"""Contract smoke test for the workflow visualization page (frontend/workflow.html).

frontend/workflow.html embeds a ``#workflow-spec`` JSON block that the page
advertises as the single source of truth — humans read the rendered diagram,
agents read the JSON. This test pins that contract so regressions surface in CI
*without* needing a browser:

  * the embedded JSON parses and has the expected shape/counts;
  * its permissions / risk levels / gate names stay in sync with the real
    ``system/`` policy files (drift-guard, mirroring the manifest drift check);
  * every ``system/...`` path the JSON tells an agent to load actually exists on
    disk (this is the exact regression the Codex P2 review caught — a dropped
    ``system/`` prefix);
  * the page is wired up (links styles.css + workflow.js, nav <-> index.html).

A real-browser render check (console errors, visual screenshots) lives in the
optional ``test_frontend_workflow_browser.py`` and is intentionally NOT part of
required CI.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_HTML = ROOT / "frontend" / "workflow.html"
WORKFLOW_JS = ROOT / "frontend" / "workflow.js"
INDEX_HTML = ROOT / "frontend" / "index.html"
STYLES_CSS = ROOT / "frontend" / "styles.css"
PERMISSIONS_PATH = ROOT / "system" / "PERMISSIONS.yaml"
GATE_POLICY_PATH = ROOT / "system" / "GATE_POLICY.yaml"

SPEC_RE = re.compile(
    r'<script type="application/json" id="workflow-spec">(.*?)</script>',
    re.S,
)

# Policy files referenced *with extension* in the spec must always carry a
# ``system/`` prefix. Bare prose names without extension (e.g. the gate
# description "違反 GLOBAL_RULES 或 PERMISSIONS") are matched verbatim from the
# source policy and intentionally excluded by requiring the extension here.
SYSTEM_FILE_NAMES = (
    "GLOBAL_RULES.md",
    "AGENT_CONTEXT.yaml",
    "APPROVAL_POLICY.yaml",
    "GATE_POLICY.yaml",
    "ROUTING_RULES.md",
    "EXECUTION_LOG_SCHEMA.yaml",
    "PERMISSIONS.yaml",
)

EXPECTED_GATES = frozenset({"schema_check", "rule_check", "completion_check", "risk_check"})


def load_spec() -> dict:
    html = WORKFLOW_HTML.read_text(encoding="utf-8")
    m = SPEC_RE.search(html)
    if not m:
        raise AssertionError("#workflow-spec block not found in frontend/workflow.html")
    return json.loads(m.group(1))


class TestWorkflowSpec(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = WORKFLOW_HTML.read_text(encoding="utf-8")
        cls.spec = load_spec()
        cls.spec_text = SPEC_RE.search(cls.html).group(1)
        cls.permissions = yaml.safe_load(PERMISSIONS_PATH.read_text(encoding="utf-8"))
        cls.gate_policy = yaml.safe_load(GATE_POLICY_PATH.read_text(encoding="utf-8"))

    def test_files_exist(self):
        for p in (WORKFLOW_HTML, WORKFLOW_JS, INDEX_HTML, STYLES_CSS):
            self.assertTrue(p.exists(), f"missing frontend file: {p}")

    def test_spec_parses_and_has_sections(self):
        for key in (
            "hard_rules", "intake", "execution_flow",
            "gates", "permissions", "risk_levels",
            "approval", "validation_failure_handling",
        ):
            self.assertIn(key, self.spec, f"#workflow-spec missing key: {key}")

    def test_section_counts(self):
        self.assertEqual(len(self.spec["hard_rules"]), 3)
        self.assertEqual(len(self.spec["execution_flow"]), 9)
        self.assertEqual(len(self.spec["gates"]), 4)
        # intake has both the fast path and the fallback
        self.assertIn("fast_path", self.spec["intake"])
        self.assertIn("intake_mode", self.spec["intake"])

    def test_execution_flow_is_sequential_and_references_gates(self):
        steps = [s["step"] for s in self.spec["execution_flow"]]
        self.assertEqual(steps, list(range(1, 10)), "steps must be numbered 1..9 in order")
        gate_refs = [s for s in self.spec["execution_flow"] if s.get("ref") == "gates"]
        self.assertTrue(gate_refs, "one execution_flow step must ref the gates section")

    def test_gates_match_gate_policy(self):
        spec_gate_names = {g["name"] for g in self.spec["gates"]}
        self.assertEqual(spec_gate_names, EXPECTED_GATES)
        policy_gate_names = set(self.gate_policy.get("gates", {}).keys())
        self.assertEqual(
            spec_gate_names, policy_gate_names,
            "spec gates must stay in sync with system/GATE_POLICY.yaml",
        )
        for g in self.spec["gates"]:
            self.assertTrue(g.get("on_fail"), f"gate {g['name']} missing on_fail")
            self.assertTrue(g.get("rollback"), f"gate {g['name']} missing rollback")

    def test_permissions_match_policy(self):
        """Drift-guard: the three permission tiers in the spec must equal the
        real PERMISSIONS.yaml, so a policy change forces a spec update."""
        policy = self.permissions["permissions"]
        for tier in ("allow", "ask", "deny"):
            self.assertEqual(
                set(self.spec["permissions"][tier]), set(policy[tier]),
                f"permissions.{tier} drifted from system/PERMISSIONS.yaml",
            )

    def test_risk_levels_match_policy(self):
        spec_levels = {r["level"] for r in self.spec["risk_levels"]}
        policy_levels = set(self.permissions["risk_levels"].keys())
        self.assertEqual(spec_levels, policy_levels)

    def test_system_paths_exist(self):
        """Every system/<file> path the spec tells an agent to load must exist.
        Directly pins the Codex P2 regression (a dropped ``system/`` prefix)."""
        paths = set(re.findall(r"system/[A-Za-z0-9_./-]+", self.spec_text))
        self.assertTrue(paths, "expected at least one system/ path in the spec")
        for rel in sorted(paths):
            self.assertTrue((ROOT / rel).exists(), f"spec references missing path: {rel}")

    def test_policy_file_refs_keep_system_prefix(self):
        """Any policy file named *with extension* must be prefixed with
        ``system/`` everywhere it appears in the spec."""
        for name in SYSTEM_FILE_NAMES:
            for m in re.finditer(re.escape(name), self.spec_text):
                start = m.start()
                self.assertEqual(
                    self.spec_text[max(0, start - 7):start], "system/",
                    f"'{name}' must be referenced as 'system/{name}' in #workflow-spec",
                )

    def test_page_is_wired(self):
        self.assertIn('href="./styles.css"', self.html)
        self.assertIn('src="./workflow.js"', self.html)
        self.assertIn('href="./workflow.html"', self.html)  # self nav
        index_html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn('href="./workflow.html"', index_html, "index.html nav must link workflow.html")

    def test_renderer_covers_every_section(self):
        js = WORKFLOW_JS.read_text(encoding="utf-8")
        for fn in (
            "renderHardRules", "renderIntake", "renderFlow", "renderGates",
            "renderPermissions", "renderRiskLevels", "renderApproval", "renderFailure",
        ):
            self.assertIn(f"{fn}(spec)", js, f"workflow.js init must call {fn}(spec)")


if __name__ == "__main__":
    unittest.main()
