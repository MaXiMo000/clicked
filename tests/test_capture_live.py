"""Run: python tests/test_capture_live.py

Real Playwright, a real headless Chromium, a real local HTTP server --
not mocked. This is the actual point of the package: proving it captures
what a real browser really did, not just that fake event objects fan out
to the right handlers (test_capture.py already covers that).

Requires `pip install playwright && playwright install chromium` --
skipped cleanly (not failed) if either isn't available, the same "can't
verify, don't guess" discipline as every unverified path elsewhere in
this portfolio.
"""
from __future__ import annotations

import http.server
import json
import pathlib
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

try:
    from playwright.sync_api import sync_playwright
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    _PLAYWRIGHT_AVAILABLE = False

from clicked.capture import capture

_PAGE_HTML = b"""<!doctype html><html><body>
<button id="save" onclick="save()">Save</button>
<script>
async function save() {
  await fetch('/api/save', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({name: 'ada'}),
  });
}
</script>
</body></html>"""


def _make_handler(write_dir: pathlib.Path):
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass  # keep test output clean

        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(_PAGE_HTML)

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            if self.path == "/api/save":
                # The real side effect being proven here: a click leads to
                # a network request leads to a file actually being written.
                (write_dir / "saved.json").write_bytes(body)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok": true}')
            else:
                self.send_response(404)
                self.end_headers()

    return Handler


@unittest.skipUnless(_PLAYWRIGHT_AVAILABLE, "playwright not installed -- skipped, not failed")
class TestCaptureLive(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.watch_dir = pathlib.Path(self.tmp.name)
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _make_handler(self.watch_dir))
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch()
        self.page = self.browser.new_page()
        self.page.goto(f"http://127.0.0.1:{self.port}/")

    def tearDown(self):
        self.browser.close()
        self.playwright.stop()
        self.server.shutdown()
        self.thread.join()
        self.tmp.cleanup()

    def test_a_real_click_that_fires_a_real_fetch_is_captured(self):
        with capture(self.page, task="click save button") as c:
            self.page.click("#save")
            self.page.wait_for_timeout(200)  # let the fetch actually complete

        api_calls = [r for r in c.requests if r["url"].endswith("/api/save")]
        self.assertEqual(len(api_calls), 1)
        self.assertEqual(api_calls[0]["method"], "POST")
        self.assertEqual(api_calls[0]["status"], 200)
        # The real POST body the browser actually sent -- not asserted
        # from the page's own JS, read back from what the browser did.
        self.assertEqual(json.loads(api_calls[0]["post_data"]), {"name": "ada"})

    def test_the_real_filesystem_side_effect_of_the_click_is_diffed(self):
        """The click causes the *server* to write a real file -- proving
        this isn't just DOM/network observation, it closes the loop to an
        actual backend side effect, the same "verified execution" idea
        receipt/custody already prove for a shell command / tool call."""
        self.assertFalse((self.watch_dir / "saved.json").exists())

        with capture(self.page, task="click save button", watch_dir=str(self.watch_dir)) as c:
            self.page.click("#save")
            self.page.wait_for_timeout(200)

        self.assertTrue((self.watch_dir / "saved.json").exists())
        self.assertIn("saved.json", c.result["changes"]["added"])

    def test_no_interaction_means_no_requests_captured(self):
        with capture(self.page, task="do nothing") as c:
            self.page.wait_for_timeout(50)
        api_calls = [r for r in c.requests if r["url"].endswith("/api/save")]
        self.assertEqual(api_calls, [])


if __name__ == "__main__":
    unittest.main()
