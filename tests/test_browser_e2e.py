from __future__ import annotations

import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8000")


@unittest.skipUnless(os.getenv("RUN_BROWSER_TESTS"), "Set RUN_BROWSER_TESTS=1 to run Playwright browser tests")
class BrowserE2ETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise unittest.SkipTest("Playwright is not installed")

        import urllib.request

        server_running = False
        try:
            with urllib.request.urlopen(f"{BASE_URL}/health", timeout=1) as resp:
                if resp.status == 200:
                    server_running = True
        except Exception:
            server_running = False

        cls._server_process = None
        if not server_running:
            repo_root = Path(__file__).resolve().parent.parent
            cls._server_process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "fkip.interfaces.api.main:app", "--host", "127.0.0.1", "--port", "8000"],
                cwd=str(repo_root),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Wait up to 12s for server
            start = time.time()
            started = False
            while time.time() - start < 12:
                try:
                    with urllib.request.urlopen(f"{BASE_URL}/health", timeout=1) as resp:
                        if resp.status == 200:
                            started = True
                            break
                except Exception:
                    time.sleep(0.5)
            if not started:
                if cls._server_process:
                    cls._server_process.terminate()
                raise unittest.SkipTest("Could not start local uvicorn server for browser test")

        cls._pw = sync_playwright().start()
        launch_args = {}
        if os.path.exists(CHROME_PATH):
            launch_args["executable_path"] = CHROME_PATH
        cls._browser = cls._pw.chromium.launch(headless=True, **launch_args)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "_browser"):
            cls._browser.close()
        if hasattr(cls, "_pw"):
            cls._pw.stop()
        if cls._server_process:
            cls._server_process.terminate()
            cls._server_process.wait()

    def setUp(self):
        self.context = self._browser.new_context(viewport={"width": 1280, "height": 800})
        self.page = self.context.new_page()

    def tearDown(self):
        self.context.close()

    def test_overview_navigation_and_metrics(self):
        self.page.goto(BASE_URL, wait_until="networkidle")
        self.page.wait_for_selector("text=INDEXED DOCUMENTS", timeout=10000)
        self.page.wait_for_selector("text=Source-Type Distribution", timeout=10000)

    def test_document_explorer_view(self):
        self.page.goto(BASE_URL, wait_until="networkidle")
        self.page.click("button.nav-tab-btn:has-text('Document Explorer')")
        self.page.wait_for_selector("text=Financial Document Explorer", timeout=10000)
        self.page.wait_for_selector("table", timeout=10000)

    def test_ai_research_view(self):
        self.page.goto(BASE_URL, wait_until="networkidle")
        self.page.click("button.nav-tab-btn:has-text('AI Research')")
        self.page.wait_for_selector("text=Evidence-Based Financial AI Research", timeout=10000)

    def test_company_comparison_view(self):
        self.page.goto(BASE_URL, wait_until="networkidle")
        self.page.click("button.nav-tab-btn:has-text('Company Comparison')")
        self.page.wait_for_selector("text=Side-by-Side Financial Disclosure Comparison", timeout=10000)

    def test_pipeline_operations_view(self):
        self.page.goto(BASE_URL, wait_until="networkidle")
        self.page.click("button.nav-tab-btn:has-text('Pipeline Ops')")
        self.page.wait_for_selector("text=Pipeline Operations & Ingestion Observability", timeout=10000)
        self.page.wait_for_selector("text=Historical Run Records", timeout=10000)
