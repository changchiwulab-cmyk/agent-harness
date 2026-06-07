#!/usr/bin/env python3
"""Optional real-browser smoke test for frontend/workflow.html (Playwright).

NOT part of required CI — it needs a browser. Run locally with:

    pip install playwright
    playwright install chromium
    python3 tests/e2e/test_frontend_workflow_browser.py

It serves the repo over a local HTTP server (workflow.html uses
``<script type="module">``, which browsers refuse to load from ``file://``),
opens the page in headless Chromium, and asserts the renderer runs with **zero
console / JS errors** while every section is present in the live DOM — the one
thing the dependency-free contract test (``test_frontend_workflow_smoke.py``)
cannot check. The dashboard (index.html) is loaded too as a regression guard.

Set ``WORKFLOW_SHOT_DIR=<dir>`` to also write desktop + mobile screenshots
(used to refresh ``docs/screenshots/``).

When Playwright (or its browser) is not installed, the test SKIPS — it never
fails a run just because the optional dependency is absent.
"""

from __future__ import annotations

import contextlib
import functools
import http.server
import os
import socketserver
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

try:
    from playwright.sync_api import sync_playwright

    _HAS_PLAYWRIGHT = True
except Exception:  # pragma: no cover - optional dependency
    _HAS_PLAYWRIGHT = False


@contextlib.contextmanager
def serve(directory: Path):
    """Serve ``directory`` on an ephemeral localhost port for the block."""
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(directory)
    )
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    httpd.daemon_threads = True
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        httpd.shutdown()
        httpd.server_close()


@unittest.skipUnless(_HAS_PLAYWRIGHT, "playwright not installed (optional browser test)")
class TestWorkflowBrowser(unittest.TestCase):
    def _audit(self, page, url):
        errors = []
        page.on(
            "console",
            lambda m: errors.append(f"console.error: {m.text}")
            if m.type == "error"
            else None,
        )
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        page.goto(url, wait_until="networkidle")
        probe = page.evaluate(
            """() => ({
                sections: document.querySelectorAll('.wf-section').length,
                flowSteps: document.querySelectorAll('.flow-step').length,
                gates: document.querySelectorAll('.gate').length,
                permCols: document.querySelectorAll('.perm-col').length,
                riskRows: document.querySelectorAll('.risk-row').length,
                hardRules: document.querySelectorAll('.rule-banner').length,
            })"""
        )
        return errors, probe

    def test_workflow_renders_without_errors(self):
        shot_dir = os.environ.get("WORKFLOW_SHOT_DIR")
        if shot_dir:
            Path(shot_dir).mkdir(parents=True, exist_ok=True)
        with serve(ROOT) as base, sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                # Desktop
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                errors, probe = self._audit(page, f"{base}/frontend/workflow.html")
                self.assertEqual(errors, [], f"console/JS errors on workflow.html: {errors}")
                self.assertGreaterEqual(probe["sections"], 8)
                self.assertEqual(probe["flowSteps"], 9)
                self.assertEqual(probe["gates"], 4)
                self.assertEqual(probe["permCols"], 3)
                self.assertEqual(probe["riskRows"], 4)
                self.assertEqual(probe["hardRules"], 3)
                if shot_dir:
                    page.screenshot(
                        path=str(Path(shot_dir) / "workflow-desktop.png"), full_page=True
                    )
                page.close()

                # Mobile (responsive)
                page = browser.new_page(viewport={"width": 414, "height": 900})
                errors, probe = self._audit(page, f"{base}/frontend/workflow.html")
                self.assertEqual(errors, [], f"console/JS errors on mobile: {errors}")
                self.assertGreaterEqual(probe["sections"], 8)
                if shot_dir:
                    page.screenshot(
                        path=str(Path(shot_dir) / "workflow-mobile.png"), full_page=True
                    )
                page.close()

                # Dashboard regression guard
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                errors, _ = self._audit(page, f"{base}/frontend/index.html")
                self.assertEqual(errors, [], f"console/JS errors on index.html: {errors}")
                page.close()
            finally:
                browser.close()


if __name__ == "__main__":
    unittest.main()
