#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E2E：信任邊界架構的結構不變式（v2.1）。

這不是 runtime 注入防禦測試（本框架的注入防禦是 prompt + 政策，無 runtime hook）；
它釘住的是「安全架構的構件存在且互相連動」：TRUST_BOUNDARY 三層 + core_rules、
FAILURE_TAXONOMY 的 SEC-05~07、SECURITY.md 非空模板、以及 lethal trifecta 的
exfiltration 腿確實被 PERMISSIONS deny 封堵。任何一處被改壞都會在 CI 浮現。

執行：python3 tests/e2e/test_trust_boundary.py
"""
import os
import unittest

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRUST = os.path.join(ROOT, "system", "TRUST_BOUNDARY.yaml")
TAXO = os.path.join(ROOT, "system", "FAILURE_TAXONOMY.yaml")
PERMS = os.path.join(ROOT, "system", "PERMISSIONS.yaml")
SECMD = os.path.join(ROOT, "SECURITY.md")
FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "untrusted_injection_sample.md")


def load(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestTrustBoundaryStructure(unittest.TestCase):
    def test_trust_boundary_tiers_and_rules(self):
        doc = load(TRUST)
        self.assertIn("principle", doc)
        tiers = doc.get("trust_tiers", {})
        for t in ("trusted", "semi_trusted", "untrusted"):
            self.assertIn(t, tiers, "缺少信任層級：%s" % t)
            self.assertTrue(tiers[t].get("sources"), "%s 須列出 sources" % t)
        rules = doc.get("core_rules", [])
        self.assertTrue(rules, "core_rules 不可為空")
        for r in rules:
            self.assertIn("id", r)
            self.assertIn("rule", r)

    def test_untrusted_includes_web_and_tools(self):
        doc = load(TRUST)
        joined = " ".join(doc["trust_tiers"]["untrusted"]["sources"])
        self.assertIn("web_search", joined)
        self.assertIn("MCP", joined)

    def test_lethal_trifecta_exfiltration_blocked(self):
        doc = load(TRUST)
        legs = doc["lethal_trifecta"]["legs"]
        self.assertEqual(legs["exfiltration_vector"]["status"], "blocked")

    def test_taxonomy_has_injection_modes(self):
        taxo = load(TAXO)
        sec_ids = {item["id"] for item in taxo["categories"]["security"]}
        for need in ("SEC-05", "SEC-06", "SEC-07"):
            self.assertIn(need, sec_ids, "FAILURE_TAXONOMY 缺少 %s" % need)

    def test_security_md_is_real_policy_not_template(self):
        with open(SECMD, encoding="utf-8") as f:
            body = f.read()
        self.assertNotIn("5.1.x", body, "SECURITY.md 仍是 GitHub 空白模板")
        self.assertIn("lethal trifecta", body)
        self.assertIn("TRUST_BOUNDARY", body)

    def test_exfiltration_leg_actually_denied(self):
        """fixture 的 payload 嘗試 send_email 外洩；該動作必須在 PERMISSIONS deny。"""
        perms = load(PERMS)["permissions"]
        self.assertIn("send_email", perms["deny"])
        with open(FIXTURE, encoding="utf-8") as f:
            payload = f.read()
        self.assertIn("忽略前述", payload)   # 注入觸發語
        self.assertIn("send_email", payload)  # 外洩管道嘗試


if __name__ == "__main__":
    unittest.main()
