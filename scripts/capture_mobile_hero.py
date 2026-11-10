#!/usr/bin/env python3
import asyncio
import base64
import json
import subprocess
import urllib.request
from pathlib import Path

import pytesseract
import websockets
from PIL import Image

DOWNLOADS_DIR = Path("/Users/suvendu/Downloads")
TMP_DIR = Path("/tmp/allcited_mobile")
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

async def main():
    print("Launching Brave in mobile emulation mode (390x844 @ 3x Retina)...")
    proc = subprocess.Popen([
        BRAVE_PATH,
        "--headless=new",
        "--remote-debugging-port=9222",
        "--window-size=390,844",
        "--force-device-scale-factor=3",
        "--disable-gpu",
        "--hide-scrollbars",
        "about:blank"
    ])

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
            await cdp_command(ws, "Emulation.setDeviceMetricsOverride", {
                "width": 390,
                "height": 844,
                "deviceScaleFactor": 3,
                "mobile": True,
                "screenOrientation": {"type": "portraitPrimary", "angle": 0}
            }, msg_id=2)
            await cdp_command(ws, "Network.setUserAgentOverride", {
                "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
            }, msg_id=3)

            print("Navigating to https://allcited.vercel.app ...")
            await cdp_command(ws, "Page.navigate", {"url": "https://allcited.vercel.app"}, msg_id=10)
            await asyncio.sleep(3.5)

            # Dismiss any popup or banner if present
            await cdp_command(ws, "Runtime.evaluate", {
                "expression": """
                const closeBtn = document.querySelector('button[aria-label="Close"]');
                if (closeBtn) closeBtn.click();
                """
            }, msg_id=11)
            await asyncio.sleep(0.5)

            # Capture viewport screenshot (mobile screen: 390x844 at 3x = 1170x2532, exact iPhone resolution)
            res = await cdp_command(ws, "Page.captureScreenshot", {
                "format": "png",
                "clip": {"x": 0, "y": 0, "width": 390, "height": 844, "scale": 1}
            }, msg_id=12)

            png_data = base64.b64decode(res["data"])
            tmp_png = TMP_DIR / "mobile_hero.png"
            with open(tmp_png, "wb") as f:
                f.write(png_data)

            jpg_path = DOWNLOADS_DIR / "allcited_hero_mobile_view.jpg"
            im = Image.open(tmp_png).convert("RGB")
            im.save(jpg_path, "JPEG", quality=95, optimize=True)
            print(f"Saved: {jpg_path} [{im.size[0]}x{im.size[1]}] ({jpg_path.stat().st_size / 1024:.1f} KB)")

            # OCR verify
            txt = pytesseract.image_to_string(im)
            lines = [line.strip() for line in txt.splitlines() if line.strip()]
            print("\n=== OCR Verification ===")
            for line in lines[:12]:
                print("  *", line)

    finally:
        proc.terminate()
        print("Finished.")

if __name__ == "__main__":
    asyncio.run(main())
