#!/usr/bin/env python3
"""
Captures the 4 dedicated high-resolution Retina screenshots for LinkedIn:
1. Hero Section (Homepage)
2. Document Upload Section (Workspace)
3. Under The Hood / Architecture (How it Works 7-Stage Pipeline)
4. Test Results / Evaluation (The Exam 46-Question Benchmark Matrix)
"""

import asyncio
import base64
import json
import subprocess
import urllib.request
from pathlib import Path

import websockets
from PIL import Image

DOWNLOADS_DIR = Path("/Users/suvendu/Downloads")
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
    print("Launching Brave in headless mode (window: 1920x1080 @ 2x Retina)...")
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
    tmp_dir = Path("/tmp/allcited_shots")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    try:
        tabs_res = urllib.request.urlopen("http://localhost:9222/json").read()
        tabs = json.loads(tabs_res.decode())
        ws_url = tabs[0]["webSocketDebuggerUrl"]
        print(f"Connected to CDP: {ws_url}")

        async with websockets.connect(ws_url, max_size=50 * 1024 * 1024) as ws:
            await cdp_command(ws, "Page.enable", msg_id=1)
            await cdp_command(ws, "Runtime.enable", msg_id=2)
            await cdp_command(ws, "DOM.enable", msg_id=3)

            # -------------------------------------------------------------
            # 1. Hero Section
            # -------------------------------------------------------------
            print("\n[1/4] Capturing Hero Section...")
            await cdp_command(
                ws, "Page.navigate", {"url": "https://allcited.vercel.app"}, msg_id=10
            )
            await asyncio.sleep(3.5)
            # Clip top viewport to capture header + hero headline + action buttons + live demo preview
            hero_png = tmp_dir / "01_hero.png"
            await capture_screenshot(
                ws,
                hero_png,
                clip={"x": 0, "y": 0, "width": 1920, "height": 960, "scale": 1},
                msg_id=11,
            )
            convert_to_jpg(hero_png, DOWNLOADS_DIR / "01_allcited_hero_section.jpg")

            # -------------------------------------------------------------
            # 2. Document Upload Section (Workspace)
            # -------------------------------------------------------------
            print("\n[2/4] Capturing Document Upload Section...")
            await cdp_command(
                ws,
                "Page.navigate",
                {"url": "https://allcited.vercel.app/?workspace=true"},
                msg_id=20,
            )
            await asyncio.sleep(3.0)
            # Click continue as guest if on auth screen
            await evaluate_script(
                ws,
                """
                const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Continue as Guest') || b.textContent.includes('guest') || b.textContent.includes('Try'));
                if (btn) btn.click();
            """,
                msg_id=21,
            )
            await asyncio.sleep(2.0)
            upload_png = tmp_dir / "02_upload.png"
            await capture_screenshot(
                ws,
                upload_png,
                clip={"x": 0, "y": 0, "width": 1920, "height": 960, "scale": 1},
                msg_id=22,
            )
            convert_to_jpg(upload_png, DOWNLOADS_DIR / "02_allcited_document_upload.jpg")

            # -------------------------------------------------------------
            # 3. How It Works Under The Hood (7-Stage Pipeline)
            # -------------------------------------------------------------
            print("\n[3/4] Capturing How It Works (7-Stage Pipeline)...")
            await cdp_command(
                ws, "Page.navigate", {"url": "https://allcited.vercel.app/how-it-works"}, msg_id=30
            )
            await asyncio.sleep(3.5)
            # Scroll down to the stages architecture section
            await evaluate_script(
                ws,
                """
                const heading = Array.from(document.querySelectorAll('h2, h3')).find(h => h.textContent.includes('The 7 Stages') || h.textContent.includes('Pipeline') || h.textContent.includes('Stage'));
                if (heading) {
                    heading.scrollIntoView({ behavior: 'instant', block: 'start' });
                    window.scrollBy(0, -80);
                } else {
                    window.scrollBy(0, 520);
                }
            """,
                msg_id=31,
            )
            await asyncio.sleep(1.5)
            pipeline_png = tmp_dir / "03_pipeline.png"
            await capture_screenshot(
                ws,
                pipeline_png,
                clip={"x": 0, "y": 0, "width": 1920, "height": 1000, "scale": 1},
                msg_id=32,
            )
            convert_to_jpg(pipeline_png, DOWNLOADS_DIR / "03_allcited_under_the_hood_pipeline.jpg")

            # -------------------------------------------------------------
            # 4. Test Results / Evaluation (Exam Benchmark Matrix)
            # -------------------------------------------------------------
            print("\n[4/4] Capturing Test Results / Evaluation Scorecard...")
            await cdp_command(
                ws, "Page.navigate", {"url": "https://allcited.vercel.app/exam"}, msg_id=40
            )
            await asyncio.sleep(3.5)
            # Scroll down to the benchmark comparison matrix & scorecards
            await evaluate_script(
                ws,
                """
                const matrixHeader = Array.from(document.querySelectorAll('h2, h3, div')).find(el => el.textContent.includes('Benchmark') || el.textContent.includes('Ablation') || el.textContent.includes('Scorecard'));
                if (matrixHeader) {
                    matrixHeader.scrollIntoView({ behavior: 'instant', block: 'start' });
                    window.scrollBy(0, -60);
                } else {
                    window.scrollBy(0, 480);
                }
            """,
                msg_id=41,
            )
            await asyncio.sleep(1.5)
            exam_png = tmp_dir / "04_exam.png"
            await capture_screenshot(
                ws,
                exam_png,
                clip={"x": 0, "y": 0, "width": 1920, "height": 1000, "scale": 1},
                msg_id=42,
            )
            convert_to_jpg(exam_png, DOWNLOADS_DIR / "04_allcited_benchmark_test_results.jpg")

    finally:
        proc.terminate()
        print("\nAll 4 photos successfully captured and saved to ~/Downloads!")


if __name__ == "__main__":
    asyncio.run(main())
