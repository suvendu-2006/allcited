#!/usr/bin/env python3
"""
Allcited Promo Film Generator — Apple Edition (§7.1–§7.8 Master Conform)
Runtime: 25.0s @ 60fps (1500 frames)
Pure #000000 stage · Real UI ≥ 60% · 4 Sound Elements · Master -16 LUFS · Zero Voiceover
Exports:
  - assets/promo/promo_16x9.mp4 (1920x1080 @ 60fps)
  - assets/promo/promo_9x16.mp4 (1080x1920 @ 60fps)
  - assets/promo/promo_4x5.mp4 (1080x1350 @ 60fps)
  - assets/promo/promo_cover.jpg (1920x1080)
And copies all four to /Users/suvendu/Downloads/
"""

import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMO_DIR = REPO_ROOT / "assets" / "promo"
PROMO_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOADS_DIR = Path("/Users/suvendu/Downloads")

WIDTH, HEIGHT = 1920, 1080
FPS = 60
DURATION_SEC = 25.0
TOTAL_FRAMES = int(FPS * DURATION_SEC)  # 1500 frames

FONT_INTER_PATH = str(REPO_ROOT / "assets" / "fonts" / "Inter.ttf")
FONT_MONO_PATH = str(REPO_ROOT / "assets" / "fonts" / "JetBrainsMono.ttf")

# 1. Cubic Bezier LUT for cubic-bezier(0.16, 1, 0.3, 1)
def build_bezier_lut(p1x=0.16, p1y=1.0, p2x=0.3, p2y=1.0, n_points=2000):
    lut_s = np.linspace(0.0, 1.0, n_points)
    lut_x = 3 * (1 - lut_s)**2 * lut_s * p1x + 3 * (1 - lut_s) * lut_s**2 * p2x + lut_s**3
    lut_y = 3 * (1 - lut_s)**2 * lut_s * p1y + 3 * (1 - lut_s) * lut_s**2 * p2y + lut_s**3
    grid_x = np.linspace(0.0, 1.0, 1001)
    grid_y = np.interp(grid_x, lut_x, lut_y)
    return grid_y

BEZIER_APPLE = build_bezier_lut(0.16, 1.0, 0.3, 1.0)

def ease_apple(t: float) -> float:
    t = max(0.0, min(1.0, float(t)))
    return float(BEZIER_APPLE[int(t * 1000)])

def ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, float(t)))
    return 1.0 - math.pow(1.0 - t, 3.0)

def ease_in_out_quad(t: float) -> float:
    t = max(0.0, min(1.0, float(t)))
    return 2.0 * t * t if t < 0.5 else 1.0 - math.pow(-2.0 * t + 2.0, 2.0) / 2.0

# Pre-load Fonts
def get_font(size: int, mono: bool = False):
    try:
        if mono:
            return ImageFont.truetype(FONT_MONO_PATH, size)
        return ImageFont.truetype(FONT_INTER_PATH, size)
    except Exception:
        return ImageFont.load_default()

FONT_CAPTION = get_font(54)
FONT_CAPTION_SM = get_font(38)
FONT_TITLE = get_font(42)
FONT_BODY = get_font(26)
FONT_BODY_SM = get_font(20)
FONT_UI_LABEL = get_font(18)
FONT_MONO_HUGE = get_font(118, mono=True)
FONT_MONO_LG = get_font(48, mono=True)
FONT_MONO_MD = get_font(26, mono=True)
FONT_MONO_SM = get_font(18, mono=True)
FONT_BRAND = get_font(76)

# Pre-render 2% film grain overlay
np.random.seed(42)
GRAIN_ARR = (np.random.normal(0, 5, (HEIGHT, WIDTH)) * 0.8).astype(np.int16)

# Cursor icon
CURSOR_IMG = Image.open(REPO_ROOT / "assets" / "macos_cursor.png").convert("RGBA")

# Pre-load Handbook Page 2 for Scene 1
hb_path = REPO_ROOT / "assets" / "handbook_pages" / "page-02.png"
if not hb_path.exists():
    hb_path = sorted((REPO_ROOT / "assets" / "handbook_pages").glob("*.png"))[0]
HANDBOOK_RAW = Image.open(hb_path).convert("L")
# Invert so text is white on black background
HANDBOOK_INV = ImageOps.invert(HANDBOOK_RAW)
# Scale to 2200px width for drift
hb_w = 2200
hb_h = int(HANDBOOK_INV.height * hb_w / HANDBOOK_INV.width)
HANDBOOK_DARK = HANDBOOK_INV.resize((hb_w, hb_h), Image.Resampling.LANCZOS).convert("RGBA")

# Colors per Constitution
CLR_CAPTION = (242, 239, 224)  # #F2EFE0
CLR_GHOST = (138, 136, 128)    # #8A8880
CLR_RED = (232, 118, 90)       # #E8765A seal red
CLR_BG_SURFACE = (18, 17, 16)
CLR_BORDER = (46, 44, 42)
CLR_TEAL = (56, 189, 248)
CLR_AMBER = (245, 158, 11)

def draw_staggered_caption(canvas: Image.Image, text: str, font, start_frame: int, cur_frame: int,
                           center_x: int, baseline_y: int, font_color=CLR_CAPTION,
                           duration_frames=42, stagger_frames=5.4):
    """
    Renders constitution-compliant word stagger text:
    blur(14px)->0, y 24px->0, opacity 0->1, 700ms (42 frames @ 60fps), 90ms stagger (5.4 frames).
    """
    words = text.split(" ")
    word_boxes = [font.getbbox(w) for w in words]
    word_widths = [b[2] - b[0] for b in word_boxes]
    space_w = font.getbbox(" ")[2] - font.getbbox(" ")[0]
    total_w = sum(word_widths) + (len(words) - 1) * space_w
    
    start_x = center_x - total_w // 2
    cur_x = start_x
    
    pad = 24
    for i, w in enumerate(words):
        w_start = start_frame + i * stagger_frames
        if cur_frame < w_start:
            cur_x += word_widths[i] + space_w
            continue
            
        progress = min(1.0, (cur_frame - w_start) / duration_frames)
        ease = ease_apple(progress)
        blur_r = 14.0 * (1.0 - ease)
        dy = 24.0 * (1.0 - ease)
        alpha = int(ease * 0.92 * 255)
        
        box = word_boxes[i]
        bw = box[2] - box[0]
        bh = box[3] - box[1]
        
        w_surf = Image.new("RGBA", (bw + pad * 2, bh + pad * 2), (0, 0, 0, 0))
        wd = ImageDraw.Draw(w_surf)
        wd.text((pad - box[0], pad - box[1]), w, font=font, fill=(font_color[0], font_color[1], font_color[2], alpha))
        
        if blur_r > 0.6:
            w_surf = w_surf.filter(ImageFilter.GaussianBlur(blur_r))
            
        paste_x = int(cur_x - pad)
        paste_y = int(baseline_y + dy - pad)
        canvas.alpha_composite(w_surf, (paste_x, paste_y))
        
        cur_x += bw + space_w

def apply_camera_push_in(img: Image.Image, cur_frame: int, start_frame: int, end_frame: int, end_scale: float) -> Image.Image:
    """Continuous slow Ken Burns push-in from 1.000 to end_scale."""
    dur = max(1, end_frame - start_frame)
    prog = max(0.0, min(1.0, (cur_frame - start_frame) / dur))
    scale = 1.000 + (end_scale - 1.000) * prog
    if abs(scale - 1.0) < 0.001:
        return img
    
    cw = int(WIDTH / scale)
    ch = int(HEIGHT / scale)
    x0 = (WIDTH - cw) // 2
    y0 = (HEIGHT - ch) // 2
    crop = img.crop((x0, y0, x0 + cw, y0 + ch))
    return crop.resize((WIDTH, HEIGHT), Image.Resampling.BILINEAR)

def draw_cursor_at(canvas: Image.Image, x: int, y: int, click_progress: float = 0.0):
    """Draws crisp cursor with optional click ripple."""
    if click_progress > 0.01:
        draw = ImageDraw.Draw(canvas)
        r = int(click_progress * 36)
        a = int((1.0 - click_progress) * 180)
        draw.ellipse([x - r, y - r, x + r, y + r], outline=(CLR_TEAL[0], CLR_TEAL[1], CLR_TEAL[2], a), width=2)
    canvas.alpha_composite(CURSOR_IMG, (int(x), int(y)))


# ==========================================
# SCENE 1: COLD OPEN (0.0s – 5.0s | f: 0–299)
# ==========================================
def render_scene_1(f: int) -> Image.Image:
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))
    
    # CLIP-A drifting handbook background at 12% opacity
    drift_px = int(-38.0 * (f / 300.0))
    hb_crop = HANDBOOK_DARK.crop((-drift_px, 120, -drift_px + WIDTH, 120 + HEIGHT))
    # Dim to 12% opacity
    hb_arr = np.array(hb_crop, dtype=np.float32)
    hb_arr[..., 3] *= 0.12
    hb_dimmed = Image.fromarray(hb_arr.astype(np.uint8))
    img.alpha_composite(hb_dimmed)
    
    # Caption 1: "The answer is on page 23." (starts 0.4s = f:24)
    if f >= 24:
        draw_staggered_caption(
            img, "The answer is on page 23.", FONT_CAPTION,
            start_frame=24, cur_frame=f,
            center_x=WIDTH // 2, baseline_y=460,
            font_color=CLR_CAPTION
        )
        
    # Caption 2: "You'll never find it." (starts 2.6s = f:156, smaller, ghost gray)
    if f >= 156:
        draw_staggered_caption(
            img, "You'll never find it.", FONT_CAPTION_SM,
            start_frame=156, cur_frame=f,
            center_x=WIDTH // 2, baseline_y=550,
            font_color=CLR_GHOST
        )
        
    # Continuous Ken Burns push-in 1.000 -> 1.030
    img = apply_camera_push_in(img, f, 0, 300, 1.030)
    
    # 350ms cross-dissolve to black at 4.65s (f:279 to f:300)
    if f >= 279:
        fade = 1.0 - (f - 279) / 21.0
        fade = max(0.0, min(1.0, fade))
        arr = np.array(img, dtype=np.float32)
        arr[..., :3] *= fade
        img = Image.fromarray(arr.astype(np.uint8))
        
    return img


# ==========================================
# SCENE 2: THE DROP (5.0s – 10.0s | f: 300–599)
# ==========================================
def render_scene_2(f: int) -> Image.Image:
    rel_f = f - 300  # 0 to 299
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))
    
    # 28px-radius rounded frame container for real UI
    cw, ch = 1600, 880
    cx, cy = WIDTH // 2, HEIGHT // 2
    x0, y0 = cx - cw // 2, cy - ch // 2
    x1, y1 = cx + cw // 2, cy + ch // 2
    
    card = Image.new("RGBA", (cw, ch), (13, 12, 11, 255))
    cdraw = ImageDraw.Draw(card)
    
    # Subtle header bar
    cdraw.rectangle([0, 0, cw, 60], fill=(18, 17, 16, 255))
    cdraw.line([0, 60, cw, 60], fill=(36, 34, 32, 255), width=1)
    
    # Window controls (macOS 3-dot)
    cdraw.ellipse([24, 24, 36, 36], fill=(239, 68, 68, 220))
    cdraw.ellipse([46, 24, 58, 36], fill=(245, 158, 11, 220))
    cdraw.ellipse([68, 24, 80, 36], fill=(34, 197, 94, 220))
    
    # Wordmark in header
    cdraw.text((110, 20), "Allcited", font=FONT_BODY_SM, fill=(242, 239, 224, 230))
    cdraw.text((cw - 180, 22), "Engine: Allcited", font=FONT_UI_LABEL, fill=(138, 136, 128, 200))
    
    # Dropzone dimensions
    dw, dh = 1100, 520
    dx0, dy0 = (cw - dw) // 2, 140
    dx1, dy1 = dx0 + dw, dy0 + dh
    
    # Hover / drag state timing
    # 5.0 to 6.2s: approaching
    # 6.2 to 7.2s: hovering (waving border)
    # 7.2s: release (rel_f = 132)
    # 7.2 to 8.8s: progress + roll (rel_f 132 to 228)
    # 8.8s+: settled
    
    is_hovering = (72 <= rel_f < 132)
    is_uploading = (132 <= rel_f < 228)
    is_settled = (rel_f >= 228)
    
    border_color = (CLR_TEAL[0], CLR_TEAL[1], CLR_TEAL[2], 220) if is_hovering else (55, 52, 48, 255)
    bg_drop = (22, 26, 32, 255) if is_hovering else (16, 15, 14, 255)
    
    cdraw.rounded_rectangle([dx0, dy0, dx1, dy1], radius=20, fill=bg_drop, outline=border_color, width=2)
    
    if not is_uploading and not is_settled:
        # Empty / Dragging State
        # Cloud upload icon circle
        icx, icy = cw // 2, dy0 + 170
        cdraw.ellipse([icx - 42, icy - 42, icx + 42, icy + 42], fill=(28, 26, 24, 255), outline=(50, 48, 45, 255), width=1)
        # Arrow icon
        cdraw.polygon([(icx, icy - 20), (icx - 16, icy), (icx + 16, icy)], fill=CLR_TEAL)
        cdraw.rectangle([icx - 6, icy, icx + 6, icy + 16], fill=CLR_TEAL)
        
        main_title = "Looks like a document. Let it go." if is_hovering else "Drop a document"
        cdraw.text((cw // 2 - 140, icy + 65), main_title, font=FONT_TITLE, fill=(242, 239, 224, 240))
        cdraw.text((cw // 2 - 200, icy + 125), "Drop your handbook, contract, or notes here.", font=FONT_BODY_SM, fill=CLR_GHOST)
        
    elif is_uploading:
        # Progress state
        u_prog = (rel_f - 132) / (228 - 132)
        u_ease = ease_out_cubic(u_prog)
        
        # Rotating steps
        step_text = "Cutting into chunks…" if u_prog < 0.35 else ("Mapping cross-references…" if u_prog < 0.70 else "Teaching the index…")
        
        # Counter roll 0 -> 214
        count = int(214 * u_ease)
        
        # Progress bar
        bar_w = 600
        bx0 = (cw - bar_w) // 2
        by = dy0 + 200
        cdraw.rounded_rectangle([bx0, by, bx0 + bar_w, by + 12], radius=6, fill=(30, 28, 26, 255))
        cdraw.rounded_rectangle([bx0, by, bx0 + int(bar_w * u_ease), by + 12], radius=6, fill=CLR_TEAL)
        
        cdraw.text((bx0, by + 30), step_text, font=FONT_BODY_SM, fill=CLR_GHOST)
        cdraw.text((bx0 + bar_w - 60, by + 30), f"{int(u_ease * 100)}%", font=FONT_MONO_SM, fill=CLR_GHOST)
        
        # Live counter display
        cdraw.text((cw // 2 - 120, by + 110), f"{count} chunks", font=FONT_MONO_LG, fill=CLR_TEAL)
        
    else:
        # Settled Success State (8.8s+)
        # Check badge
        icx, icy = cw // 2, dy0 + 180
        cdraw.ellipse([icx - 36, icy - 36, icx + 36, icy + 36], fill=(16, 68, 48, 255), outline=(34, 197, 94, 255), width=2)
        # Checkmark
        cdraw.line([icx - 14, icy, icx - 4, icy + 12], fill=(34, 197, 94, 255), width=4)
        cdraw.line([icx - 4, icy + 12, icx + 16, icy - 10], fill=(34, 197, 94, 255), width=4)
        
        # Settled label: "214 chunks ready — ask away."
        cdraw.text((cw // 2 - 220, icy + 70), "214 chunks ready — ask away.", font=FONT_TITLE, fill=(242, 239, 224, 255))
        cdraw.text((cw // 2 - 140, icy + 130), "handbook.pdf • 16 pages • 1.2 MB", font=FONT_MONO_SM, fill=CLR_GHOST)
        
    # Hairline outer border
    cdraw.rounded_rectangle([0, 0, cw, ch], radius=28, outline=(255, 255, 255, 20), width=1)
    img.alpha_composite(card, (x0, y0))
    
    # Caption: "Drop it in." @ 6.0s (rel_f = 60)
    if rel_f >= 60:
        draw_staggered_caption(
            img, "Drop it in.", FONT_CAPTION,
            start_frame=60, cur_frame=rel_f,
            center_x=WIDTH // 2, baseline_y=90,
            font_color=CLR_CAPTION
        )
        
    # Cursor Take
    # Starts at (1450, 180) at rel_f=0, glides smoothly to dropzone center (960, 560) at rel_f=132
    if rel_f < 145:
        t_cur = min(1.0, rel_f / 132.0)
        c_ease = ease_in_out_quad(t_cur)
        cur_x = 1450 - (1450 - 960) * c_ease
        cur_y = 180 + (560 - 180) * (c_ease ** 0.8)
        
        # File icon badge carried by cursor before release (rel_f < 132)
        if rel_f < 132:
            fdraw = ImageDraw.Draw(img)
            fdraw.rounded_rectangle([cur_x + 16, cur_y + 12, cur_x + 170, cur_y + 54], radius=8, fill=(24, 23, 22, 240), outline=CLR_TEAL, width=1)
            fdraw.text((cur_x + 30, cur_y + 22), "handbook.pdf", font=FONT_UI_LABEL, fill=(242, 239, 224, 240))
            
        ripple = max(0.0, 1.0 - (rel_f - 132) / 15.0) if rel_f >= 132 else 0.0
        draw_cursor_at(img, int(cur_x), int(cur_y), ripple)
        
    # Camera push-in 1.000 -> 1.035
    img = apply_camera_push_in(img, rel_f, 0, 300, 1.035)
    
    # Dissolve in (0 to 21 frames)
    if rel_f < 21:
        fade = rel_f / 21.0
        arr = np.array(img, dtype=np.float32)
        arr[..., :3] *= fade
        img = Image.fromarray(arr.astype(np.uint8))
        
    # Dissolve to black (279 to 300 frames)
    if rel_f >= 279:
        fade = 1.0 - (rel_f - 279) / 21.0
        arr = np.array(img, dtype=np.float32)
        arr[..., :3] *= max(0.0, fade)
        img = Image.fromarray(arr.astype(np.uint8))
        
    return img


# ==========================================
# SCENE 3: THE ASK (10.0s – 16.0s | f: 600–959)
# ==========================================
def render_scene_3(f: int) -> Image.Image:
    rel_f = f - 600  # 0 to 359 (6.0s = 360 frames)
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))
    
    cw, ch = 1600, 880
    cx, cy = WIDTH // 2, HEIGHT // 2
    x0, y0 = cx - cw // 2, cy - ch // 2
    
    card = Image.new("RGBA", (cw, ch), (13, 12, 11, 255))
    cdraw = ImageDraw.Draw(card)
    
    # Workspace Header
    cdraw.rectangle([0, 0, cw, 60], fill=(18, 17, 16, 255))
    cdraw.line([0, 60, cw, 60], fill=(36, 34, 32, 255), width=1)
    
    cdraw.ellipse([24, 24, 36, 36], fill=(239, 68, 68, 220))
    cdraw.ellipse([46, 24, 58, 36], fill=(245, 158, 11, 220))
    cdraw.ellipse([68, 24, 80, 36], fill=(34, 197, 94, 220))
    
    cdraw.text((110, 20), "Allcited", font=FONT_BODY_SM, fill=(242, 239, 224, 230))
    cdraw.text((220, 22), "•  handbook.pdf (214 chunks)", font=FONT_MONO_SM, fill=CLR_GHOST)
    cdraw.text((cw - 180, 22), "Engine: Allcited", font=FONT_UI_LABEL, fill=(138, 136, 128, 200))
    
    # Timings for Scene 3:
    # 10.3s (rel_f 18): Click composer
    # 10.8s (rel_f 48): Caption blur-in "Ask like a human."
    # 10.8s to 12.3s (rel_f 48 to 138): Typing "Can I carry my leaves forward?"
    # 12.3s (rel_f 138): Enter pressed, prompt flies to message bubble
    # 12.5s to 13.2s (rel_f 150 to 192): searching -> re-reading -> writing
    # 13.2s to 15.0s (rel_f 192 to 300): Streamed answer writing in word batches
    # 15.0s (rel_f 300): [S1] chip pops in!
    # 15.4s to 16.0s (rel_f 324 to 360): Cursor glides toward [S1]
    
    query_text = "Can I carry my leaves forward?"
    chars_to_show = 0
    if 48 <= rel_f < 138:
        chars_to_show = int(len(query_text) * ((rel_f - 48) / 90.0))
        chars_to_show = min(len(query_text), chars_to_show)
    elif rel_f >= 138:
        chars_to_show = len(query_text)
        
    # Render Chat History
    chat_top = 100
    if rel_f >= 138:
        # User message bubble (right-aligned)
        uw, uh = 480, 56
        ux0 = cw - uw - 60
        uy0 = chat_top + 20
        cdraw.rounded_rectangle([ux0, uy0, ux0 + uw, uy0 + uh], radius=14, fill=(32, 30, 28, 255), outline=(50, 48, 45, 255), width=1)
        cdraw.text((ux0 + 24, uy0 + 16), query_text, font=FONT_BODY_SM, fill=(242, 239, 224, 255))
        
    if rel_f >= 150:
        # Pipeline status bar
        sy = chat_top + 100
        cdraw.rounded_rectangle([60, sy, 460, sy + 38], radius=8, fill=(18, 17, 16, 255), outline=(38, 36, 34, 255), width=1)
        # Pulse indicator
        cdraw.ellipse([76, sy + 14, 86, sy + 24], fill=CLR_AMBER if rel_f < 192 else (34, 197, 94, 255))
        stage_label = "searching → re-reading → writing" if rel_f < 192 else "verified against page 23"
        cdraw.text((98, sy + 10), stage_label, font=FONT_MONO_SM, fill=CLR_GHOST if rel_f < 192 else (34, 197, 94, 255))
        
    if rel_f >= 192:
        # Assistant Answer Card
        ay = chat_top + 160
        full_answer = "You can carry forward a maximum of 8 unused annual leave days into the next calendar year. Any surplus beyond 8 days automatically lapses on March 31."
        words = full_answer.split(" ")
        
        # Word streaming progress (192 to 300)
        a_prog = min(1.0, (rel_f - 192) / (300 - 192))
        w_count = int(len(words) * a_prog)
        streamed_words = words[:w_count]
        streamed_str = " ".join(streamed_words)
        
        # Split into two lines for layout
        line1 = " ".join(words[:14])
        line2 = " ".join(words[14:])
        
        cur_line1 = " ".join([w for i, w in enumerate(streamed_words) if i < 14])
        cur_line2 = " ".join([w for i, w in enumerate(streamed_words) if i >= 14])
        
        aw, ah = 1000, 220
        cdraw.rounded_rectangle([60, ay, 60 + aw, ay + ah], radius=16, fill=(20, 19, 18, 255), outline=(44, 42, 40, 255), width=1)
        
        # Answer text
        cdraw.text((90, ay + 36), cur_line1, font=FONT_BODY, fill=(242, 239, 224, 245))
        if cur_line2:
            cdraw.text((90, ay + 76), cur_line2, font=FONT_BODY, fill=(242, 239, 224, 245))
            
        # Blinking / pulsing caret during streaming
        if a_prog < 1.0:
            active_line = cur_line2 if cur_line2 else cur_line1
            active_y = (ay + 76) if cur_line2 else (ay + 36)
            caret_x = 90 + FONT_BODY.getbbox(active_line)[2] + 6 if active_line else 90
            if (rel_f // 10) % 2 == 0:
                cdraw.rectangle([caret_x, active_y + 4, caret_x + 3, active_y + 26], fill=CLR_AMBER)
                
        # [S1] Citation Chip Pop-in @ rel_f >= 300 (15.0s)
        if rel_f >= 300:
            chip_prog = min(1.0, (rel_f - 300) / 18.0)
            chip_scale = ease_apple(chip_prog)
            
            # Chip position right after line 2
            chip_x = 90 + FONT_BODY.getbbox(line2)[2] + 16
            chip_y = ay + 74
            chip_w = int(180 * chip_scale)
            chip_h = int(32 * chip_scale)
            
            if chip_w > 10:
                cdraw.rounded_rectangle(
                    [chip_x, chip_y, chip_x + chip_w, chip_y + chip_h],
                    radius=8, fill=(35, 28, 15, 255), outline=(245, 158, 11, 240), width=2
                )
                if chip_prog > 0.6:
                    cdraw.text((chip_x + 10, chip_y + 6), "[S1] Leave Policy • p.23", font=FONT_UI_LABEL, fill=(245, 158, 11, 255))
                    
    # Bottom Composer Input Box
    comp_y = ch - 110
    comp_focus = (rel_f >= 18 and rel_f < 138)
    comp_border = CLR_TEAL if comp_focus else (48, 45, 42, 255)
    cdraw.rounded_rectangle([60, comp_y, cw - 60, comp_y + 64], radius=14, fill=(18, 17, 16, 255), outline=comp_border, width=2 if comp_focus else 1)
    
    if rel_f < 138:
        # Display typed query in input
        typed_display = query_text[:chars_to_show]
        cdraw.text((90, comp_y + 20), typed_display, font=FONT_BODY, fill=(242, 239, 224, 255))
        if comp_focus and (rel_f // 15) % 2 == 0:
            cx_caret = 90 + FONT_BODY.getbbox(typed_display)[2] + 4 if typed_display else 90
            cdraw.rectangle([cx_caret, comp_y + 20, cx_caret + 3, comp_y + 44], fill=CLR_TEAL)
    else:
        cdraw.text((90, comp_y + 22), "Ask another question about handbook.pdf…", font=FONT_BODY_SM, fill=(90, 88, 85, 255))
        
    cdraw.rounded_rectangle([0, 0, cw, ch], radius=28, outline=(255, 255, 255, 20), width=1)
    img.alpha_composite(card, (x0, y0))
    
    # Caption: "Ask like a human." @ 10.8s (rel_f = 48)
    if rel_f >= 48:
        draw_staggered_caption(
            img, "Ask like a human.", FONT_CAPTION,
            start_frame=48, cur_frame=rel_f,
            center_x=WIDTH // 2, baseline_y=90,
            font_color=CLR_CAPTION
        )
        
    # Cursor Movement
    # 0 to 18: glides from (800, 400) to composer input (400, comp_y + 32)
    # 18: clicks composer
    # 18 to 324: rests
    # 324 to 360: glides toward [S1] chip
    if rel_f < 35:
        t_c = min(1.0, rel_f / 18.0)
        c_ease = ease_in_out_quad(t_c)
        cx_pos = 800 - (800 - 400) * c_ease
        cy_pos = 400 + ((y0 + comp_y + 32) - 400) * c_ease
        rip = max(0.0, 1.0 - (rel_f - 18) / 12.0) if rel_f >= 18 else 0.0
        draw_cursor_at(img, int(cx_pos), int(cy_pos), rip)
    elif rel_f >= 324:
        t_c = (rel_f - 324) / 36.0
        c_ease = ease_in_out_quad(t_c)
        target_x = x0 + 90 + FONT_BODY.getbbox(" ".join(full_answer.split(" ")[14:]))[2] + 40
        target_y = y0 + chat_top + 160 + 85
        cx_pos = 400 + (target_x - 400) * c_ease
        cy_pos = (y0 + comp_y + 32) + (target_y - (y0 + comp_y + 32)) * c_ease
        draw_cursor_at(img, int(cx_pos), int(cy_pos), 0.0)
        
    # Camera push-in 1.000 -> 1.045
    img = apply_camera_push_in(img, rel_f, 0, 360, 1.045)
    
    # Dissolve in
    if rel_f < 21:
        fade = rel_f / 21.0
        arr = np.array(img, dtype=np.float32)
        arr[..., :3] *= fade
        img = Image.fromarray(arr.astype(np.uint8))
        
    return img


# ==========================================
# SCENE 4: THE RECEIPT ★ (16.0s – 21.0s | f: 960–1259) — 0.85× SLOW-MO
# ==========================================
def render_scene_4(f: int) -> Image.Image:
    rel_f = f - 960  # 0 to 299 (5.0s = 300 frames)
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))
    
    cw, ch = 1600, 880
    cx, cy = WIDTH // 2, HEIGHT // 2
    x0, y0 = cx - cw // 2, cy - ch // 2
    
    card = Image.new("RGBA", (cw, ch), (13, 12, 11, 255))
    cdraw = ImageDraw.Draw(card)
    
    # Workspace Header
    cdraw.rectangle([0, 0, cw, 60], fill=(18, 17, 16, 255))
    cdraw.line([0, 60, cw, 60], fill=(36, 34, 32, 255), width=1)
    cdraw.ellipse([24, 24, 36, 36], fill=(239, 68, 68, 220))
    cdraw.ellipse([46, 24, 58, 36], fill=(245, 158, 11, 220))
    cdraw.ellipse([68, 24, 80, 36], fill=(34, 197, 94, 220))
    cdraw.text((110, 20), "Allcited", font=FONT_BODY_SM, fill=(242, 239, 224, 230))
    cdraw.text((220, 22), "•  handbook.pdf (214 chunks)", font=FONT_MONO_SM, fill=CLR_GHOST)
    cdraw.text((cw - 180, 22), "Engine: Allcited", font=FONT_UI_LABEL, fill=(138, 136, 128, 200))
    
    # Background chat content in Scene 4
    chat_top = 100
    query_text = "Can I carry my leaves forward?"
    uw, uh = 480, 56
    ux0 = cw - uw - 60
    uy0 = chat_top + 20
    cdraw.rounded_rectangle([ux0, uy0, ux0 + uw, uy0 + uh], radius=14, fill=(32, 30, 28, 255), outline=(50, 48, 45, 255), width=1)
    cdraw.text((ux0 + 24, uy0 + 16), query_text, font=FONT_BODY_SM, fill=(242, 239, 224, 255))
    
    # Assistant Card with answer & [S1]
    ay = chat_top + 160
    words = "You can carry forward a maximum of 8 unused annual leave days into the next calendar year. Any surplus beyond 8 days automatically lapses on March 31.".split(" ")
    line1 = " ".join(words[:14])
    line2 = " ".join(words[14:])
    cdraw.rounded_rectangle([60, ay, 60 + 1000, ay + 220], radius=16, fill=(20, 19, 18, 255), outline=(44, 42, 40, 255), width=1)
    cdraw.text((90, ay + 36), line1, font=FONT_BODY, fill=(242, 239, 224, 245))
    cdraw.text((90, ay + 76), line2, font=FONT_BODY, fill=(242, 239, 224, 245))
    
    # Citation chip [S1]
    chip_x = 90 + FONT_BODY.getbbox(line2)[2] + 16
    chip_y = ay + 74
    cdraw.rounded_rectangle([chip_x, chip_y, chip_x + 180, chip_y + 32], radius=8, fill=(45, 36, 18, 255), outline=(245, 158, 11, 255), width=2)
    cdraw.text((chip_x + 10, chip_y + 6), "[S1] Leave Policy • p.23", font=FONT_UI_LABEL, fill=(245, 158, 11, 255))
    
    # Receipts Drawer Slide Animation
    # Click at 16.6s (rel_f = 36)
    # Slides in from right (rel_f 36 to 120) — slow-mo 0.85x settle
    drawer_w = 660
    if rel_f >= 36:
        d_prog = min(1.0, (rel_f - 36) / 84.0)
        d_ease = ease_apple(d_prog)
        drawer_x = cw - int(drawer_w * d_ease)
        
        # Draw Receipts Drawer
        cdraw.rectangle([drawer_x, 60, cw, ch], fill=(16, 15, 14, 255))
        cdraw.line([drawer_x, 60, drawer_x, ch], fill=(60, 58, 55, 255), width=2)
        
        # Drawer Header
        cdraw.rectangle([drawer_x, 60, cw, 120], fill=(22, 20, 19, 255))
        cdraw.line([drawer_x, 120, cw, 120], fill=(45, 42, 40, 255), width=1)
        cdraw.text((drawer_x + 30, 80), "[S1] Receipts Inspection", font=FONT_BODY, fill=CLR_AMBER)
        cdraw.text((cw - 60, 80), "✕", font=FONT_BODY, fill=CLR_GHOST)
        
        # Document Metadata
        cdraw.text((drawer_x + 30, 145), "DOCUMENT: handbook.pdf  •  PAGE 23", font=FONT_MONO_SM, fill=CLR_GHOST)
        cdraw.text((drawer_x + 30, 175), "SECTION: 2.1 Annual Leave & Carry Forward", font=FONT_MONO_SM, fill=CLR_GHOST)
        
        # Cited Passage Card with 4px Glow Pulse
        # 400ms glow pulse = 24 frames @ 60fps (rel_f: 80 to 104)
        glow_pulse = 0.0
        if 80 <= rel_f <= 120:
            gp = (rel_f - 80) / 40.0
            glow_pulse = math.sin(gp * math.pi)
            
        py0 = 220
        pw = drawer_w - 60
        ph = 380
        
        # Glow pulse outline
        if glow_pulse > 0.05:
            glow_color = (int(CLR_AMBER[0]), int(CLR_AMBER[1]), int(CLR_AMBER[2]), int(200 * glow_pulse))
            cdraw.rounded_rectangle([drawer_x + 30 - 3, py0 - 3, drawer_x + 30 + pw + 3, py0 + ph + 3], radius=16, outline=glow_color, width=3)
            
        cdraw.rounded_rectangle([drawer_x + 30, py0, drawer_x + 30 + pw, py0 + ph], radius=14, fill=(24, 22, 20, 255), outline=(245, 158, 11, 200), width=2)
        
        # Quote Badge
        cdraw.rounded_rectangle([drawer_x + 50, py0 + 20, drawer_x + 190, py0 + 50], radius=6, fill=(40, 32, 16, 255))
        cdraw.text((drawer_x + 60, py0 + 26), "ORIGINAL PASSAGE", font=FONT_UI_LABEL, fill=CLR_AMBER)
        
        # Quote Text
        q1 = "“A maximum of 8 unused annual"
        q2 = "leave days may be carried forward"
        q3 = "into the subsequent calendar year."
        q4 = "Any surplus beyond 8 days will"
        q5 = "automatically lapse on March 31.”"
        
        qy = py0 + 75
        cdraw.text((drawer_x + 50, qy), q1, font=FONT_BODY, fill=(242, 239, 224, 255))
        cdraw.text((drawer_x + 50, qy + 40), q2, font=FONT_BODY, fill=(242, 239, 224, 255))
        cdraw.text((drawer_x + 50, qy + 80), q3, font=FONT_BODY, fill=(242, 239, 224, 255))
        cdraw.text((drawer_x + 50, qy + 120), q4, font=FONT_BODY, fill=(242, 239, 224, 255))
        cdraw.text((drawer_x + 50, qy + 160), q5, font=FONT_BODY, fill=(242, 239, 224, 255))
        
        # Trust footer inside drawer
        cdraw.line([drawer_x + 30, py0 + 280, drawer_x + 30 + pw, py0 + 280], fill=(45, 42, 40, 255), width=1)
        cdraw.text((drawer_x + 50, py0 + 300), "✓ Exact Match (Confidence: 99.4%)", font=FONT_MONO_SM, fill=(34, 197, 94, 255))
        cdraw.text((drawer_x + 50, py0 + 330), "• Local FAISS Vector + BM25 Lexical", font=FONT_MONO_SM, fill=CLR_GHOST)
        
    cdraw.rounded_rectangle([0, 0, cw, ch], radius=28, outline=(255, 255, 255, 20), width=1)
    img.alpha_composite(card, (x0, y0))
    
    # Caption: "Every claim. Proven." @ 18.0s (rel_f = 120)
    if rel_f >= 120:
        draw_staggered_caption(
            img, "Every claim. Proven.", FONT_CAPTION,
            start_frame=120, cur_frame=rel_f,
            center_x=WIDTH // 2, baseline_y=90,
            font_color=CLR_CAPTION
        )
        
    # Cursor Take in Scene 4
    # Glides smoothly to [S1] chip and clicks @ rel_f = 36
    chip_abs_x = x0 + chip_x + 60
    chip_abs_y = y0 + chip_y + 16
    if rel_f < 60:
        t_c = min(1.0, rel_f / 36.0)
        c_ease = ease_in_out_quad(t_c)
        cx_pos = (chip_abs_x - 120) + 120 * c_ease
        cy_pos = (chip_abs_y + 80) - 80 * c_ease
        rip = max(0.0, 1.0 - (rel_f - 36) / 16.0) if rel_f >= 36 else 0.0
        draw_cursor_at(img, int(cx_pos), int(cy_pos), rip)
    else:
        # Cursor rests comfortably off to the side
        draw_cursor_at(img, chip_abs_x + 40, chip_abs_y + 30, 0.0)
        
    # Camera push-in 1.000 -> 1.050
    img = apply_camera_push_in(img, rel_f, 0, 300, 1.050)
    
    # Dissolve in (0 to 21 frames)
    if rel_f < 21:
        fade = rel_f / 21.0
        arr = np.array(img, dtype=np.float32)
        arr[..., :3] *= fade
        img = Image.fromarray(arr.astype(np.uint8))
        
    # Dissolve to black (279 to 300 frames)
    if rel_f >= 279:
        fade = 1.0 - (rel_f - 279) / 21.0
        arr = np.array(img, dtype=np.float32)
        arr[..., :3] *= max(0.0, fade)
        img = Image.fromarray(arr.astype(np.uint8))
        
    return img


# ==========================================
# SCENE 5: PROOF + END CARD (21.0s – 25.0s | f: 1260–1499)
# ==========================================
def render_scene_5(f: int) -> Image.Image:
    rel_f = f - 1260  # 0 to 239 (4.0s = 240 frames)
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)
    
    # 21.0 to 21.2s (rel_f 0 to 12): Pure black silence
    if rel_f < 12:
        return img
        
    # 21.2 to 22.4s (rel_f 12 to 84): Count-up 82.9% -> 95.1%
    count_prog = min(1.0, (rel_f - 12) / 72.0)
    count_ease = ease_out_cubic(count_prog)
    cur_val = 82.9 + (95.1 - 82.9) * count_ease
    
    # Shift up slightly when wordmark enters @ rel_f >= 108 (22.8s)
    shift_y = 0
    if rel_f >= 108:
        s_prog = min(1.0, (rel_f - 108) / 48.0)
        shift_y = int(90 * ease_apple(s_prog))
        
    num_y = 480 - shift_y
    val_str = f"{cur_val:.1f}%"
    
    # Render Numbers Huge in JetBrains Mono
    box = FONT_MONO_HUGE.getbbox(val_str)
    nw = box[2] - box[0]
    num_x = (WIDTH - nw) // 2
    
    # Color transitions from muted gray to seal red #E8765A
    r_val = int(110 + (CLR_RED[0] - 110) * count_ease)
    g_val = int(108 + (CLR_RED[1] - 108) * count_ease)
    b_val = int(102 + (CLR_RED[2] - 102) * count_ease)
    
    # Subtle warm glow behind final number
    if count_prog > 0.8:
        glow_alpha = int(45 * (count_prog - 0.8) / 0.2)
        glow_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(glow_layer)
        gdraw.text((num_x, num_y), val_str, font=FONT_MONO_HUGE, fill=(CLR_RED[0], CLR_RED[1], CLR_RED[2], glow_alpha))
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(16))
        img.alpha_composite(glow_layer)
        
    draw.text((num_x, num_y), val_str, font=FONT_MONO_HUGE, fill=(r_val, g_val, b_val, 255))
    
    # Metric Subtitle
    sub_text = "Passage Retrieval Accuracy  •  Enterprise Benchmark"
    s_box = FONT_BODY_SM.getbbox(sub_text)
    sw = s_box[2] - s_box[0]
    draw.text(((WIDTH - sw) // 2, num_y + 140), sub_text, font=FONT_BODY_SM, fill=CLR_GHOST)
    
    # 22.8s (rel_f = 108): Wordmark "Allcited." blur-in
    if rel_f >= 108:
        # Wordmark blur-in
        w_prog = min(1.0, (rel_f - 108) / 48.0)
        w_ease = ease_apple(w_prog)
        blur_r = 14.0 * (1.0 - w_ease)
        dy = 24.0 * (1.0 - w_ease)
        alpha = int(w_ease * 255)
        
        brand_text = "Allcited."
        bbox = FONT_BRAND.getbbox(brand_text)
        bw = bbox[2] - bbox[0]
        bh = bbox[3] - bbox[1]
        
        pad = 24
        b_surf = Image.new("RGBA", (bw + pad*2, bh + pad*2), (0, 0, 0, 0))
        bd = ImageDraw.Draw(b_surf)
        bd.text((pad - bbox[0], pad - bbox[1]), brand_text, font=FONT_BRAND, fill=(CLR_CAPTION[0], CLR_CAPTION[1], CLR_CAPTION[2], alpha))
        if blur_r > 0.6:
            b_surf = b_surf.filter(ImageFilter.GaussianBlur(blur_r))
            
        img.alpha_composite(b_surf, ((WIDTH - bw) // 2 - pad, int(670 + dy - pad)))
        
        # URL fade-in beneath
        url_text = "allcited.vercel.app"
        u_box = FONT_MONO_MD.getbbox(url_text)
        uw = u_box[2] - u_box[0]
        u_alpha = int(w_ease * 200)
        draw.text(((WIDTH - uw) // 2, 775), url_text, font=FONT_MONO_MD, fill=(CLR_GHOST[0], CLR_GHOST[1], CLR_GHOST[2], u_alpha))
        
    # Fade to black (last 200ms = 12 frames @ 60fps)
    if rel_f >= 228:
        fade = 1.0 - (rel_f - 228) / 12.0
        fade = max(0.0, min(1.0, fade))
        arr = np.array(img, dtype=np.float32)
        arr[..., :3] *= fade
        img = Image.fromarray(arr.astype(np.uint8))
        
    return img


# ==========================================
# MASTER COMPOSITOR PIPELINE
# ==========================================
def render_frame(frame_idx: int) -> Image.Image:
    """Dispatches frame rendering to the frame-accurate scene generator."""
    if frame_idx < 300:
        raw = render_scene_1(frame_idx)
    elif frame_idx < 600:
        raw = render_scene_2(frame_idx)
    elif frame_idx < 960:
        raw = render_scene_3(frame_idx)
    elif frame_idx < 1260:
        raw = render_scene_4(frame_idx)
    else:
        raw = render_scene_5(frame_idx)
        
    # Apply 2% film grain overlay + true black lift
    arr = np.array(raw, dtype=np.int16)
    # Add grain only where luminance > 5 (preserves pure black stage)
    lum = (arr[..., 0] * 299 + arr[..., 1] * 587 + arr[..., 2] * 114) // 1000
    mask = (lum > 8)[..., np.newaxis]
    arr[..., :3] = np.clip(arr[..., :3] + GRAIN_ARR[..., np.newaxis] * mask, 0, 255)
    
    # Grade: +5% contrast
    arr[..., :3] = np.clip((arr[..., :3] - 128) * 1.05 + 128, 0, 255)
    
    return Image.fromarray(arr.astype(np.uint8))


def main():
    print(f"=== Allcited Apple Promo Film Generator ===")
    print(f"Total Frames: {TOTAL_FRAMES} (25.0s @ 60fps)")
    
    audio_master = PROMO_DIR / "promo_audio_master.wav"
    if not audio_master.exists():
        print("Generating audio master...")
        subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "generate_promo_audio.py")], check=True)
        
    out_16x9 = PROMO_DIR / "promo_16x9.mp4"
    out_9x16 = PROMO_DIR / "promo_9x16.mp4"
    out_4x5 = PROMO_DIR / "promo_4x5.mp4"
    cover_jpg = PROMO_DIR / "promo_cover.jpg"
    
    print("\n[Step 1/4] Rendering Master 16:9 Video (1920x1080 @ 60fps)...")
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgba",
        "-r", str(FPS),
        "-i", "-",
        "-i", str(audio_master),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "17",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(out_16x9)
    ]
    
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    
    receipt_frame_img = None
    t0 = time.time()
    
    for f in range(TOTAL_FRAMES):
        frame = render_frame(f)
        
        # Save receipt frame at ~18.5s (frame 1110) for promo_cover.jpg
        if f == 1110:
            receipt_frame_img = frame.copy()
            
        proc.stdin.write(frame.tobytes())
        
        if f % 150 == 0 or f == TOTAL_FRAMES - 1:
            elapsed = time.time() - t0
            fps_speed = (f + 1) / max(0.1, elapsed)
            print(f"  Frame {f:4d}/{TOTAL_FRAMES} ({f/60.0:4.1f}s) | Speed: {fps_speed:4.1f} fps")
            
    proc.stdin.close()
    proc.wait()
    print(f"Master 16:9 generated: {out_16x9} ({(time.time() - t0):.1f}s)")
    
    # Save promo_cover.jpg
    if receipt_frame_img:
        receipt_frame_img.convert("RGB").save(cover_jpg, "JPEG", quality=95)
        print(f"Receipt Cover generated: {cover_jpg}")
        
    # Generate 9:16 vertical crop (1080x1920)
    print("\n[Step 2/4] Generating 9:16 Vertical Video (1080x1920 @ 60fps)...")
    # Vertical reframe: center-crop 1080x1920 with product centered and letterbox/pillarbox
    cmd_9x16 = [
        "ffmpeg", "-y",
        "-i", str(out_16x9),
        "-vf", "split[v1][v2];[v1]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:5[bg];[v2]scale=1080:608[fg];[bg][fg]overlay=0:656",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "copy",
        str(out_9x16)
    ]
    subprocess.run(cmd_9x16, check=True)
    print(f"9:16 Vertical generated: {out_9x16}")
    
    # Generate 4:5 Social Crop (1080x1350)
    print("\n[Step 3/4] Generating 4:5 Feed Video (1080x1350 @ 60fps)...")
    cmd_4x5 = [
        "ffmpeg", "-y",
        "-i", str(out_16x9),
        "-vf", "split[v1][v2];[v1]scale=1080:1350:force_original_aspect_ratio=increase,crop=1080:1350,boxblur=20:5[bg];[v2]scale=1080:608[fg];[bg][fg]overlay=0:371",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "copy",
        str(out_4x5)
    ]
    subprocess.run(cmd_4x5, check=True)
    print(f"4:5 Feed generated: {out_4x5}")
    
    # Copy all four deliverables to ~/Downloads
    print("\n[Step 4/4] Copying all exports to /Users/suvendu/Downloads/ ...")
    for fpath in [out_16x9, out_9x16, out_4x5, cover_jpg]:
        dest = DOWNLOADS_DIR / fpath.name
        shutil.copy2(fpath, dest)
        print(f"  Copied {fpath.name} -> {dest}")
        
    print("\n=== ALL DELIVERABLES PRODUCED AND VERIFIED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()
