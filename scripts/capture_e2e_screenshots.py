#!/usr/bin/env python3
"""Run automated end-to-end browser tests and capture high-resolution screenshots."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent
CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BASE_URL = "http://127.0.0.1:8000"
IMAGES_DIR = REPO_ROOT / "docs" / "images"


def wait_for_server(url: str, timeout: int = 15) -> bool:
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(f"{url}/health", timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def main() -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    server_process = None
    if not wait_for_server(BASE_URL, timeout=1):
        print("Starting FastAPI server in background...")
        server_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "fkip.interfaces.api.main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=str(REPO_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if not wait_for_server(BASE_URL, timeout=15):
            if server_process:
                server_process.terminate()
            raise RuntimeError("FastAPI server failed to start on http://127.0.0.1:8000")
        print("FastAPI server started successfully.")
    else:
        print("FastAPI server already running on http://127.0.0.1:8000.")

    try:
        with sync_playwright() as p:
            launch_args = {}
            if os.path.exists(CHROME_PATH):
                launch_args["executable_path"] = CHROME_PATH

            browser = p.chromium.launch(headless=True, **launch_args)
            context = browser.new_context(
                viewport={"width": 1440, "height": 900},
                device_scale_factor=2,  # Retina crisp screenshots
            )
            page = context.new_page()

            # -------------------------------------------------------------
            # Screenshot 1: Research Overview
            # -------------------------------------------------------------
            print("1. Loading Research Overview...")
            page.goto(BASE_URL, wait_until="networkidle")
            page.wait_for_selector("text=INDEXED DOCUMENTS", timeout=10000)
            page.wait_for_selector("text=Source-Type Distribution", timeout=10000)
            page.wait_for_timeout(1000)
            overview_path = IMAGES_DIR / "screenshot_01_research_overview.png"
            page.screenshot(path=str(overview_path))
            print(f"   -> Saved: {overview_path}")

            # -------------------------------------------------------------
            # Screenshot 2: Document Explorer
            # -------------------------------------------------------------
            print("2. Navigating to Document Explorer...")
            page.click("button.nav-tab-btn:has-text('Document Explorer')")
            page.wait_for_selector("text=Financial Document Explorer", timeout=10000)
            page.wait_for_selector("table", timeout=10000)
            page.wait_for_timeout(800)

            # Click "Inspect" on first document to display detailed modal with chunks
            first_view_button = page.locator("button:has-text('Inspect')").first
            if first_view_button.count() > 0:
                first_view_button.click()
                page.wait_for_selector("text=Document Provenance & Extraction Detail", timeout=8000)
                page.wait_for_timeout(800)

            explorer_path = IMAGES_DIR / "screenshot_02_document_explorer.png"
            page.screenshot(path=str(explorer_path))
            print(f"   -> Saved: {explorer_path}")

            # Close modal by clicking close button in modal header
            close_btn = page.locator(".modal-header button").first
            if close_btn.count() > 0:
                close_btn.click()
                page.wait_for_selector(".modal-overlay", state="detached", timeout=5000)
                page.wait_for_timeout(400)

            # -------------------------------------------------------------
            # Screenshot 3: Evidence-Based AI Research with Expanded Citation
            # -------------------------------------------------------------
            print("3. Navigating to AI Research & analyzing query...")
            page.click("button.nav-tab-btn:has-text('AI Research')")
            page.wait_for_selector("text=Evidence-Based Financial AI Research", timeout=10000)

            # Fill in query and click "Run Analysis"
            query_input = page.locator("input[placeholder*='research question']")
            query_input.fill("What operational resilience, cybersecurity, and regulatory risks are disclosed by Apple and Microsoft?")
            page.click("button:has-text('Run Analysis')")

            # Wait for answer and citations to load
            page.wait_for_selector("text=Extractive Financial Synthesis", timeout=20000)
            page.wait_for_selector("text=Selected Passage Inspector", timeout=10000)
            page.wait_for_timeout(1000)

            research_path = IMAGES_DIR / "screenshot_03_ai_research_expanded_citation.png"
            page.screenshot(path=str(research_path))
            print(f"   -> Saved: {research_path}")

            # -------------------------------------------------------------
            # Screenshot 4: Company Comparison
            # -------------------------------------------------------------
            print("4. Navigating to Company Comparison...")
            page.click("button.nav-tab-btn:has-text('Company Comparison')")
            page.wait_for_selector("text=Side-by-Side Financial Disclosure Comparison", timeout=10000)

            # Click "Execute Comparison"
            page.click("button:has-text('Execute Comparison')")
            # Wait for comparison assessment banner to load
            page.wait_for_selector("text=Objective Comparison Assessment", timeout=20000)
            page.wait_for_timeout(1000)

            comparison_path = IMAGES_DIR / "screenshot_04_company_comparison.png"
            page.screenshot(path=str(comparison_path))
            print(f"   -> Saved: {comparison_path}")

            # -------------------------------------------------------------
            # Screenshot 5: Pipeline Operations Dashboard
            # -------------------------------------------------------------
            print("5. Navigating to Pipeline Operations...")
            page.click("button.nav-tab-btn:has-text('Pipeline Ops')")
            page.wait_for_selector("text=Pipeline Operations & Ingestion Observability", timeout=10000)
            page.wait_for_selector("text=Historical Run Records", timeout=10000)
            page.wait_for_timeout(1000)

            pipeline_path = IMAGES_DIR / "screenshot_05_pipeline_operations.png"
            page.screenshot(path=str(pipeline_path))
            print(f"   -> Saved: {pipeline_path}")

            browser.close()
            print("\n=======================================================")
            print("ALL 5 HIGH-RESOLUTION PORTFOLIO SCREENSHOTS CAPTURED SUCCESSFULLY!")
            print("=======================================================")
    finally:
        if server_process:
            print("Stopping background FastAPI server...")
            server_process.terminate()
            server_process.wait()


if __name__ == "__main__":
    main()
