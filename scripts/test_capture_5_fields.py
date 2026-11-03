#!/usr/bin/env python3
import asyncio
import base64
import json
import subprocess
import urllib.request
from pathlib import Path

import websockets
from PIL import Image

DOWNLOADS_DIR = Path("/Users/suvendu/Downloads")
TMP_DIR = Path("/tmp/allcited_5_fields")
TMP_DIR.mkdir(parents=True, exist_ok=True)
BRAVE_PATH = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"


async def cdp_command(ws, method, params=None, msg_id=1):
    payload = {"id": msg_id, "method": method, "params": params or {}}
    await ws.send(json.dumps(payload))
    while True:
        resp = await ws.recv()
        data = json.loads(resp)
        if data.get("id") == msg_id:
            return data.get("result", {})


async def capture_screenshot(ws, output_png: Path, clip=None, msg_id=100):
    params = {"format": "png", "captureBeyondViewport": True}
    if clip:
        params["clip"] = clip
    res = await cdp_command(ws, "Page.captureScreenshot", params, msg_id=msg_id)
    raw_data = base64.b64decode(res["data"])
    with open(output_png, "wb") as f:
        f.write(raw_data)
    print(f"Captured PNG: {output_png.name} ({len(raw_data) / 1024:.1f} KB)")


async def evaluate_script(ws, expression: str, msg_id=200):
    res = await cdp_command(
        ws,
        "Runtime.evaluate",
        {"expression": expression, "awaitPromise": True, "returnByValue": True},
        msg_id=msg_id,
    )
    return res.get("result", {}).get("value")


def convert_to_jpg(png_path: Path, jpg_path: Path, quality=95):
    im = Image.open(png_path).convert("RGB")
    im.save(jpg_path, "JPEG", quality=quality, optimize=True)
    size_mb = jpg_path.stat().st_size / (1024 * 1024)
    print(f"Saved JPG: {jpg_path.name} [{im.size[0]}x{im.size[1]}] ({size_mb:.2f} MB)")


async def main():
    print("Launching Brave...")
    proc = subprocess.Popen(
        [
            BRAVE_PATH,
            "--headless=new",
            "--remote-debugging-port=9222",
            "--window-size=1920,1080",
            "--force-device-scale-factor=2",
            "--disable-gpu",
            "--hide-scrollbars",
            "about:blank",
        ]
    )
    await asyncio.sleep(2.5)

    try:
        tabs_res = urllib.request.urlopen("http://localhost:9222/json").read()
        tabs = json.loads(tabs_res.decode())
        ws_url = tabs[0]["webSocketDebuggerUrl"]
        print(f"CDP connected: {ws_url}")

        async with websockets.connect(ws_url, max_size=50 * 1024 * 1024) as ws:
            await cdp_command(ws, "Page.enable", msg_id=1)
            await cdp_command(ws, "Runtime.enable", msg_id=2)
            await cdp_command(ws, "DOM.enable", msg_id=3)

            # -----------------------------------------------------------------
            # 1. Hero Landing Section
            # -----------------------------------------------------------------
            print("\n[1/5] Capturing Hero Section...")
            await cdp_command(
                ws, "Page.navigate", {"url": "https://allcited.vercel.app"}, msg_id=10
            )
            await asyncio.sleep(3.5)
            png1 = TMP_DIR / "01_hero.png"
            await capture_screenshot(
                ws, png1, clip={"x": 0, "y": 0, "width": 1920, "height": 960, "scale": 1}, msg_id=11
            )
            convert_to_jpg(png1, DOWNLOADS_DIR / "01_hero_section.jpg")

            # -----------------------------------------------------------------
            # 2. Interactive Workspace: Document Upload & Workspace
            # (Ensure guest bypass so NO sign-in modal exists)
            # -----------------------------------------------------------------
            print("\n[2/5] Capturing Document Upload Section...")
            await cdp_command(
                ws,
                "Page.navigate",
                {"url": "https://allcited.vercel.app/?workspace=true"},
                msg_id=20,
            )
            await asyncio.sleep(3.0)
            # Auto-click "Continue as Guest" if shown
            await evaluate_script(
                ws,
                """
                const btn = Array.from(document.querySelectorAll('button')).find(b =>
                    b.textContent.includes('Continue as Guest') ||
                    b.textContent.includes('guest') ||
                    b.textContent.includes('Try as Guest')
                );
                if (btn) btn.click();
            """,
                msg_id=21,
            )
            await asyncio.sleep(2.0)
            # Check if any modal is still up, dismiss it
            await evaluate_script(
                ws,
                """
                const closeBtn = document.querySelector('button[aria-label="Close"]');
                if (closeBtn) closeBtn.click();
            """,
                msg_id=22,
            )
            await asyncio.sleep(1.0)
            png2 = TMP_DIR / "02_upload.png"
            await capture_screenshot(
                ws, png2, clip={"x": 0, "y": 0, "width": 1920, "height": 960, "scale": 1}, msg_id=23
            )
            convert_to_jpg(png2, DOWNLOADS_DIR / "02_document_upload.jpg")

            # -----------------------------------------------------------------
            # 3. Interactive Citations & Receipts Drawer (Live Demo)
            # -----------------------------------------------------------------
            print("\n[3/5] Capturing Interactive Citations & Receipts Drawer...")
            await cdp_command(
                ws, "Page.navigate", {"url": "https://allcited.vercel.app"}, msg_id=30
            )
            await asyncio.sleep(3.5)
            # Scroll down to the live demo interactive card
            await evaluate_script(
                ws,
                """
                const demoEl = document.querySelector('[data-testid="live-mini-demo"]') ||
                               Array.from(document.querySelectorAll('h2, h3, div')).find(el => el.textContent.includes('Interactive') || el.textContent.includes('See it in action') || el.textContent.includes('Carry forward'));
                if (demoEl) {
                    demoEl.scrollIntoView({ behavior: 'instant', block: 'center' });
                } else {
                    window.scrollBy(0, 480);
                }
            """,
                msg_id=31,
            )
            await asyncio.sleep(1.5)
            # Click [S1] chip to open drawer
            await evaluate_script(
                ws,
                """
                const chip = document.querySelector('button[title*="Leave Policy"]') ||
                             Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('[S1]') || b.textContent.includes('S1'));
                if (chip) chip.click();
            """,
                msg_id=32,
            )
            await asyncio.sleep(2.0)
            png3 = TMP_DIR / "03_citations_drawer.png"
            await capture_screenshot(
                ws,
                png3,
                clip={"x": 0, "y": 280, "width": 1920, "height": 980, "scale": 1},
                msg_id=33,
            )
            convert_to_jpg(png3, DOWNLOADS_DIR / "03_citations_drawer.jpg")

            # -----------------------------------------------------------------
            # 4. Under The Hood / Architecture (7-Stage Pipeline on /how-it-works)
            # -----------------------------------------------------------------
            print("\n[4/5] Capturing Under The Hood (7-Stage Pipeline)...")
            await cdp_command(
                ws, "Page.navigate", {"url": "https://allcited.vercel.app/how-it-works"}, msg_id=40
            )
            await asyncio.sleep(3.5)
            await evaluate_script(
                ws,
                """
                const pipelineHeader = Array.from(document.querySelectorAll('h2, h3')).find(h =>
                    h.textContent.includes('7 Stages') || h.textContent.includes('Pipeline') || h.textContent.includes('Under the hood')
                );
                if (pipelineHeader) {
                    pipelineHeader.scrollIntoView({ behavior: 'instant', block: 'start' });
                    window.scrollBy(0, -60);
                } else {
                    window.scrollBy(0, 520);
                }
            """,
                msg_id=41,
            )
            await asyncio.sleep(1.5)
            png4 = TMP_DIR / "04_pipeline.png"
            await capture_screenshot(
                ws,
                png4,
                clip={"x": 0, "y": 0, "width": 1920, "height": 1020, "scale": 1},
                msg_id=42,
            )
            convert_to_jpg(png4, DOWNLOADS_DIR / "04_under_the_hood_pipeline.jpg")

            # -----------------------------------------------------------------
            # 5. Test Results / Evaluation (46-Question Benchmark on /exam)
            # -----------------------------------------------------------------
            print("\n[5/5] Capturing Evaluation Benchmark Matrix (/exam)...")
            await cdp_command(
                ws, "Page.navigate", {"url": "https://allcited.vercel.app/exam"}, msg_id=50
            )
            await asyncio.sleep(3.5)
            await evaluate_script(
                ws,
                """
                const matrixHeader = Array.from(document.querySelectorAll('h2, h3, div')).find(el =>
                    el.textContent.includes('Benchmark') || el.textContent.includes('Ablation') || el.textContent.includes('Scorecard')
                );
                if (matrixHeader) {
                    matrixHeader.scrollIntoView({ behavior: 'instant', block: 'start' });
                    window.scrollBy(0, -60);
                } else {
                    window.scrollBy(0, 480);
                }
            """,
                msg_id=51,
            )
            await asyncio.sleep(1.5)
            png5 = TMP_DIR / "05_exam.png"
            await capture_screenshot(
                ws,
                png5,
                clip={"x": 0, "y": 0, "width": 1920, "height": 1020, "scale": 1},
                msg_id=52,
            )
            convert_to_jpg(png5, DOWNLOADS_DIR / "05_test_results_benchmark.jpg")

    finally:
        proc.terminate()
        print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
