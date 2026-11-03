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
TMP_DIR = Path("/tmp/allcited_5_distinct")
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
    print("Launching Brave in headless mode (1920x1080 @ 2x Retina)...")
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

    tabs_res = None
    for _ in range(25):
        try:
            tabs_res = urllib.request.urlopen("http://localhost:9222/json").read()
            break
        except Exception:
            await asyncio.sleep(0.4)

    if not tabs_res:
        proc.terminate()
        raise RuntimeError("Failed to connect to Brave CDP port 9222")

    tabs = json.loads(tabs_res.decode())
    ws_url = tabs[0]["webSocketDebuggerUrl"]
    print(f"Connected to CDP: {ws_url}")

    try:
        async with websockets.connect(ws_url, max_size=50 * 1024 * 1024) as ws:
            await cdp_command(ws, "Page.enable", msg_id=1)
            await cdp_command(ws, "Runtime.enable", msg_id=2)
            await cdp_command(ws, "DOM.enable", msg_id=3)

            # =================================================================
            # Section 1: Hero Landing & Value Proposition (/)
            # =================================================================
            print("\n[1/5] Capturing Section 1: Hero Landing...")
            await cdp_command(
                ws, "Page.navigate", {"url": "https://allcited.vercel.app"}, msg_id=10
            )
            await asyncio.sleep(3.5)
            # Dismiss any popup/cookie if present
            await evaluate_script(
                ws,
                """
                const closeBtn = document.querySelector('button[aria-label="Close"]');
                if (closeBtn) closeBtn.click();
            """,
                msg_id=11,
            )
            png1 = TMP_DIR / "01_hero_overview.png"
            await capture_screenshot(
                ws, png1, clip={"x": 0, "y": 0, "width": 1920, "height": 960, "scale": 1}, msg_id=12
            )
            convert_to_jpg(png1, DOWNLOADS_DIR / "01_hero_overview.jpg")

            # =================================================================
            # Section 2: Interactive Grounded Q&A & Citation Receipts Demo (/)
            # =================================================================
            print("\n[2/5] Capturing Section 2: Interactive Grounded Q&A & Receipts Demo...")
            # Scroll specifically to "Try it right here"
            await evaluate_script(
                ws,
                """
                const h2 = Array.from(document.querySelectorAll('h2')).find(el => el.textContent.includes('Try it right here'));
                if (h2) {
                    h2.scrollIntoView({ behavior: 'instant', block: 'start' });
                    window.scrollBy(0, -60);
                } else {
                    window.scrollBy(0, 580);
                }
            """,
                msg_id=20,
            )
            await asyncio.sleep(2.5)
            # Click [S1] chip so citation receipt callout is open
            await evaluate_script(
                ws,
                """
                const chip = document.querySelector('button[title*="Leave Policy"]') ||
                             Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('[S1]') || b.textContent.includes('S1'));
                if (chip) chip.click();
            """,
                msg_id=21,
            )
            await asyncio.sleep(2.0)
            png2 = TMP_DIR / "02_interactive_citations_demo.png"
            # Height 920 shows: TRY IT -> Heading -> Query -> Streamed Answer with [S1] -> Stamped receipt box -> sub-100ms badges
            await capture_screenshot(
                ws, png2, clip={"x": 0, "y": 0, "width": 1920, "height": 940, "scale": 1}, msg_id=22
            )
            convert_to_jpg(png2, DOWNLOADS_DIR / "02_interactive_citations_demo.jpg")

            # =================================================================
            # Section 3: Product Capabilities & Guarantees (/product)
            # =================================================================
            print("\n[3/5] Capturing Section 3: Product Capabilities (/product)...")
            await cdp_command(
                ws, "Page.navigate", {"url": "https://allcited.vercel.app/product"}, msg_id=30
            )
            await asyncio.sleep(3.5)
            png3 = TMP_DIR / "03_product_capabilities.png"
            await capture_screenshot(
                ws, png3, clip={"x": 0, "y": 0, "width": 1920, "height": 980, "scale": 1}, msg_id=31
            )
            convert_to_jpg(png3, DOWNLOADS_DIR / "03_product_capabilities.jpg")

            # =================================================================
            # Section 4: Under The Hood 7-Stage Pipeline (/how-it-works)
            # =================================================================
            print("\n[4/5] Capturing Section 4: Under The Hood Pipeline (/how-it-works)...")
            await cdp_command(
                ws, "Page.navigate", {"url": "https://allcited.vercel.app/how-it-works"}, msg_id=40
            )
            await asyncio.sleep(3.5)
            await evaluate_script(
                ws,
                """
                const header = Array.from(document.querySelectorAll('h1, h2, h3, div')).find(h =>
                    h.textContent.includes('THE PIPELINE') || h.textContent.includes('Stage 1')
                );
                if (header) {
                    header.scrollIntoView({ behavior: 'instant', block: 'start' });
                    window.scrollBy(0, -60);
                } else {
                    window.scrollBy(0, 480);
                }
            """,
                msg_id=41,
            )
            await asyncio.sleep(1.5)
            png4 = TMP_DIR / "04_under_the_hood_pipeline.png"
            await capture_screenshot(
                ws,
                png4,
                clip={"x": 0, "y": 0, "width": 1920, "height": 1020, "scale": 1},
                msg_id=42,
            )
            convert_to_jpg(png4, DOWNLOADS_DIR / "04_under_the_hood_pipeline.jpg")

            # =================================================================
            # Section 5: Empirical Benchmark & Adversarial Test Scores (/exam)
            # =================================================================
            print("\n[5/5] Capturing Section 5: Test Results Benchmark (/exam)...")
            await cdp_command(
                ws, "Page.navigate", {"url": "https://allcited.vercel.app/exam"}, msg_id=50
            )
            await asyncio.sleep(3.5)
            await evaluate_script(
                ws,
                """
                const examHeader = Array.from(document.querySelectorAll('h1, h2, h3, div')).find(el =>
                    el.textContent.includes('OUR TEST SCORES') || el.textContent.includes('What we test')
                );
                if (examHeader) {
                    examHeader.scrollIntoView({ behavior: 'instant', block: 'start' });
                    window.scrollBy(0, -60);
                } else {
                    window.scrollBy(0, 480);
                }
            """,
                msg_id=51,
            )
            await asyncio.sleep(1.5)
            png5 = TMP_DIR / "05_test_results_benchmark.png"
            await capture_screenshot(
                ws,
                png5,
                clip={"x": 0, "y": 0, "width": 1920, "height": 1020, "scale": 1},
                msg_id=52,
            )
            convert_to_jpg(png5, DOWNLOADS_DIR / "05_test_results_benchmark.jpg")

            # =================================================================
            # BONUS Section: Honest Transparent Pricing (/pricing)
            # =================================================================
            print("\n[BONUS] Capturing Transparent Pricing (/pricing)...")
            await cdp_command(
                ws, "Page.navigate", {"url": "https://allcited.vercel.app/pricing"}, msg_id=60
            )
            await asyncio.sleep(3.5)
            png6 = TMP_DIR / "06_pricing_plans.png"
            await capture_screenshot(
                ws, png6, clip={"x": 0, "y": 0, "width": 1920, "height": 980, "scale": 1}, msg_id=61
            )
            convert_to_jpg(png6, DOWNLOADS_DIR / "06_pricing_plans.jpg")

    finally:
        proc.terminate()
        print("\nAll 5 sections (+ bonus pricing) captured successfully!")


if __name__ == "__main__":
    asyncio.run(main())
