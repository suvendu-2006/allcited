#!/usr/bin/env python3
"""
Captures pixel-perfect 4K Retina screenshots of the real Allcited web application
across various interactive states using Chrome DevTools Protocol (CDP).
"""

import asyncio
import base64
import json
import subprocess
import time
import urllib.request
from pathlib import Path
import websockets

REPO_ROOT = Path(__file__).resolve().parent.parent
CAPTURES_DIR = REPO_ROOT / "assets" / "real_site_photos"
CAPTURES_DIR.mkdir(parents=True, exist_ok=True)

BRAVE_PATH = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

async def cdp_command(ws, method, params=None, msg_id=1):
    payload = {"id": msg_id, "method": method, "params": params or {}}
    await ws.send(json.dumps(payload))
    while True:
        resp = await ws.recv()
        data = json.loads(resp)
        if data.get("id") == msg_id:
            return data.get("result", {})

async def capture_screenshot(ws, output_path: Path, clip=None, msg_id=100):
    params = {"format": "png", "captureBeyondViewport": True}
    if clip:
        params["clip"] = clip
    res = await cdp_command(ws, "Page.captureScreenshot", params, msg_id=msg_id)
    raw_data = base64.b64decode(res["data"])
    with open(output_path, "wb") as f:
        f.write(raw_data)
    print(f"Captured: {output_path} ({len(raw_data) / 1024:.1f} KB)")

async def evaluate_script(ws, expression: str, msg_id=200):
    res = await cdp_command(ws, "Runtime.evaluate", {
        "expression": expression,
        "awaitPromise": True,
        "returnByValue": True
    }, msg_id=msg_id)
    return res.get("result", {}).get("value")

async def run_capture_session():
    print("Launching browser in headless mode with 2x Retina scale...")
    proc = subprocess.Popen([
        BRAVE_PATH,
        "--headless=new",
        "--remote-debugging-port=9222",
        "--window-size=1920,1080",
        "--force-device-scale-factor=2",
        "--disable-gpu",
        "--hide-scrollbars",
        "about:blank"
    ])

    await asyncio.sleep(2.5)

    try:
        tabs_res = urllib.request.urlopen("http://localhost:9222/json").read()
        tabs = json.loads(tabs_res.decode())
        ws_url = tabs[0]["webSocketDebuggerUrl"]
        print(f"Connecting to CDP: {ws_url}")

        async with websockets.connect(ws_url, max_size=50 * 1024 * 1024) as ws:
            # Enable domains
            await cdp_command(ws, "Page.enable", msg_id=1)
            await cdp_command(ws, "Runtime.enable", msg_id=2)
            await cdp_command(ws, "DOM.enable", msg_id=3)

            # 1. Capture Homepage Hero
            print("Navigating to https://allcited.vercel.app ...")
            await cdp_command(ws, "Page.navigate", {"url": "https://allcited.vercel.app"}, msg_id=10)
            await asyncio.sleep(4.0)

            # Capture Hero Viewport
            await capture_screenshot(ws, CAPTURES_DIR / "01_hero_landing.png", msg_id=101)

            # 2. Scroll to and interact with LiveMiniDemo
            print("Interacting with LiveMiniDemo...")
            await evaluate_script(ws, """
                const replayBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Replay'));
                if (replayBtn) replayBtn.click();
            """, msg_id=20)
            await asyncio.sleep(1.0)
            await capture_screenshot(ws, CAPTURES_DIR / "02_live_demo_streaming.png", msg_id=102)

            # Wait for streaming to finish and citations to show
            await asyncio.sleep(2.5)
            await capture_screenshot(ws, CAPTURES_DIR / "03_live_demo_citations.png", msg_id=103)

            # Click Citation Chip [S1] or first chip to open receipts drawer
            print("Clicking citation chip to trigger receipts drawer...")
            await evaluate_script(ws, """
                const chip = document.querySelector('button[title*="Leave Policy"]') || document.querySelector('button[title*="S1"]');
                if (chip) {
                    chip.click();
                } else {
                    const anyChip = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('[S1]') || b.textContent.includes('S1'));
                    if (anyChip) anyChip.click();
                }
            """, msg_id=30)
            await asyncio.sleep(1.5)
            await capture_screenshot(ws, CAPTURES_DIR / "04_receipts_drawer_open.png", msg_id=104)

            # 3. Capture 7-Stage Pipeline on /how-it-works
            print("Navigating to https://allcited.vercel.app/how-it-works ...")
            await cdp_command(ws, "Page.navigate", {"url": "https://allcited.vercel.app/how-it-works"}, msg_id=40)
            await asyncio.sleep(3.5)
            await capture_screenshot(ws, CAPTURES_DIR / "05_pipeline_stages.png", msg_id=105)

            # Scroll down to stages grid
            await evaluate_script(ws, "window.scrollBy(0, 500);", msg_id=45)
            await asyncio.sleep(1.5)
            await capture_screenshot(ws, CAPTURES_DIR / "06_pipeline_grid.png", msg_id=106)

            # 4. Capture Empirical Test Scorecards on /exam
            print("Navigating to https://allcited.vercel.app/exam ...")
            await cdp_command(ws, "Page.navigate", {"url": "https://allcited.vercel.app/exam"}, msg_id=50)
            await asyncio.sleep(3.5)
            await capture_screenshot(ws, CAPTURES_DIR / "07_exam_scorecard.png", msg_id=107)

            # Scroll down to ablation matrix
            await evaluate_script(ws, "window.scrollBy(0, 600);", msg_id=55)
            await asyncio.sleep(1.5)
            await capture_screenshot(ws, CAPTURES_DIR / "08_exam_matrix.png", msg_id=108)

            # 5. Capture Workspace View
            print("Navigating to workspace mode...")
            await cdp_command(ws, "Page.navigate", {"url": "https://allcited.vercel.app/?workspace=true"}, msg_id=60)
            await asyncio.sleep(3.0)
            await capture_screenshot(ws, CAPTURES_DIR / "09_workspace_auth_guest.png", msg_id=109)

            # Continue as guest
            await evaluate_script(ws, """
                const guestBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Continue as Guest') || b.textContent.includes('guest') || b.textContent.includes('Try'));
                if (guestBtn) guestBtn.click();
            """, msg_id=65)
            await asyncio.sleep(2.0)
            await capture_screenshot(ws, CAPTURES_DIR / "10_workspace_chat.png", msg_id=110)

    finally:
        proc.terminate()
        print("Capture session complete!")

if __name__ == "__main__":
    asyncio.run(run_capture_session())
