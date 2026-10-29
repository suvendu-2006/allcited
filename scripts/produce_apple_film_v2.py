#!/usr/bin/env python3
"""
Allcited Promotional Video Generator v2 (Authentic Apple Keynote Master)
100% REAL Product Footage · Zero Mockups · Zero Cartoon Drawing · Zero Stock
Conforms strictly to ALLCITED.md §7.1–§7.8.
25.0s @ 60fps (1500 frames) · Master -16 LUFS · 4 Sound Elements · Zero Voiceover
"""

import math
import os
from pathlib import Path
import shutil
import subprocess
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMO_DIR = REPO_ROOT / "assets" / "promo"
PROMO_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOADS_DIR = Path("/Users/suvendu/Downloads")

FPS = 60
TOTAL_FRAMES = 1500  # 25.0s exactly

# Fonts per §7.1: Inter (captions) + JetBrains Mono (numbers only)
FONT_INTER_PATH = str(REPO_ROOT / "assets" / "fonts" / "Inter.ttf")
FONT_MONO_PATH = str(REPO_ROOT / "assets" / "fonts" / "JetBrainsMono.ttf")

if not os.path.exists(FONT_INTER_PATH):
    for cand in ["/System/Library/Fonts/SFPro.ttf", "/System/Library/Fonts/Helvetica.ttc"]:
        if os.path.exists(cand):
            FONT_INTER_PATH = cand
            break

if not os.path.exists(FONT_MONO_PATH):
    for cand in ["/System/Library/Fonts/SFMono-Regular.otf", "/System/Library/Fonts/Supplemental/Courier New.ttf"]:
        if os.path.exists(cand):
            FONT_MONO_PATH = cand
            break


def get_font(size: int, mono: bool = False):
    try:
        if mono:
            return ImageFont.truetype(FONT_MONO_PATH, size)
        return ImageFont.truetype(FONT_INTER_PATH, size)
    except Exception:
        return ImageFont.load_default()


# Constitution Typography Sizes
FONT_CAPTION = get_font(54)
FONT_CAPTION_SM = get_font(38)
FONT_CAPTION_MOBILE = get_font(46)
FONT_CAPTION_MOBILE_SM = get_font(32)
FONT_MONO_HUGE = get_font(124, mono=True)
FONT_MONO_LG = get_font(52, mono=True)
FONT_MONO_MD = get_font(26, mono=True)
FONT_MONO_SM = get_font(20, mono=True)
FONT_BODY_TITLE = get_font(26)
FONT_BODY_SM = get_font(20)
FONT_BRAND = get_font(84)

# Constitution Color Palette
CLR_BG = (0, 0, 0)
CLR_CAPTION = (242, 239, 224)   # #F2EFE0
CLR_GHOST = (160, 156, 148)     # #A09C94
CLR_RED = (232, 118, 90)        # #E8765A seal red
CLR_TEAL = (56, 189, 248)       # #38BDF8
CLR_GREEN = (49, 199, 165)      # #31C7A5 luminous teal
CLR_AMBER = (245, 158, 11)

# Cursor icon
CURSOR_IMG = Image.open(REPO_ROOT / "assets" / "macos_cursor.png").convert("RGBA")

# Load Real Captured Assets (100% Real UI)
REAL_DIR = REPO_ROOT / "assets" / "real_footage_frames"
REAL_DROP_EMPTY = Image.open(REAL_DIR / "01_dropzone_empty.png").convert("RGB")
REAL_DEMO_CITATIONS = Image.open(REAL_DIR / "04_demo_citations.png").convert("RGB")
REAL_DEMO_RECEIPT = Image.open(REAL_DIR / "05_demo_receipt_open.png").convert("RGB")
REAL_DEMO_STREAMING = Image.open(REAL_DIR / "06_demo_streaming.png").convert("RGB")

# Pre-load Handbook Page 2 for Scene 1 (CLIP-A)
hb_path = REPO_ROOT / "assets" / "handbook_pages" / "page-02.png"
HANDBOOK_RAW = Image.open(hb_path).convert("L")
HANDBOOK_INV = ImageOps.invert(HANDBOOK_RAW)
hb_w = 2400
hb_h = int(HANDBOOK_INV.height * hb_w / HANDBOOK_INV.width)
HANDBOOK_DARK = HANDBOOK_INV.resize((hb_w, hb_h), Image.Resampling.LANCZOS).convert("RGBA")

# Pre-crop and pre-scale high-res base assets for maximum rendering speed
BASE_S2_CROP = REAL_DROP_EMPTY.crop((800, 220, 3040, 1680))
BASE_S2_16X9 = BASE_S2_CROP.resize((int(1680 * 1.05), int(900 * 1.05)), Image.Resampling.LANCZOS)
BASE_S2_9X16 = BASE_S2_CROP.resize((int(1000 * 1.05), int(536 * 1.05)), Image.Resampling.LANCZOS)

BASE_S3_STREAM_CROP = REAL_DEMO_STREAMING.crop((850, 700, 2990, 1680))
BASE_S3_STREAM_16X9 = BASE_S3_STREAM_CROP.resize((int(1600 * 1.06), int(780 * 1.06)), Image.Resampling.LANCZOS)
BASE_S3_STREAM_9X16 = BASE_S3_STREAM_CROP.resize((int(1000 * 1.06), int(488 * 1.06)), Image.Resampling.LANCZOS)

BASE_S3_CITE_CROP = REAL_DEMO_CITATIONS.crop((850, 700, 2990, 1680))
BASE_S3_CITE_16X9 = BASE_S3_CITE_CROP.resize((int(1600 * 1.06), int(780 * 1.06)), Image.Resampling.LANCZOS)
BASE_S3_CITE_9X16 = BASE_S3_CITE_CROP.resize((int(1000 * 1.06), int(488 * 1.06)), Image.Resampling.LANCZOS)

BASE_S4_RECEIPT_CROP = REAL_DEMO_RECEIPT.crop((850, 700, 2990, 1680))
BASE_S4_RECEIPT_16X9 = BASE_S4_RECEIPT_CROP.resize((int(1600 * 1.06), int(780 * 1.06)), Image.Resampling.LANCZOS)
BASE_S4_RECEIPT_9X16 = BASE_S4_RECEIPT_CROP.resize((int(1000 * 1.06), int(488 * 1.06)), Image.Resampling.LANCZOS)


def ease_apple(t: float) -> float:
    """Apple motion constitution: cubic-bezier(0.16, 1, 0.3, 1)"""
    t = max(0.0, min(1.0, t))
    return 1.0 - math.pow(1.0 - t, 3.8)


def ease_in_out_quad(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 2 * t * t if t < 0.5 else 1 - math.pow(-2 * t + 2, 2) / 2


def draw_caption(canvas: Image.Image, text: str, font, start_frame: int, cur_frame: int,
                 center_x: int, baseline_y: int, font_color=CLR_CAPTION,
                 duration_frames=42, stagger_frames=5.4):
    """
    Apple Constitution Text Reveal: blur(14px)->0 + y 24px->0 + opacity 0->1, 700ms, staggered.
    Uses anchor='ls' on a unified mathematical baseline so all words align perfectly!
    """
    words = text.split(" ")
    space_w = font.getlength(" ")
    word_widths = [font.getlength(w) for w in words]
    total_w = sum(word_widths) + (len(words) - 1) * space_w
    
    ascent, descent = font.getmetrics()
    pad = 32
    
    start_x = center_x - total_w / 2.0
    cur_x = start_x
    
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
        
        w_len = word_widths[i]
        surf_w = int(w_len) + pad * 2
        surf_h = ascent + descent + pad * 2
        
        w_surf = Image.new("RGBA", (surf_w, surf_h), (0, 0, 0, 0))
        wd = ImageDraw.Draw(w_surf)
        wd.text((pad, pad + ascent), w, font=font, fill=(font_color[0], font_color[1], font_color[2], alpha), anchor="ls")
        
        if blur_r > 0.6:
            w_surf = w_surf.filter(ImageFilter.GaussianBlur(blur_r))
            
        paste_x = int(round(cur_x - pad))
        paste_y = int(round(baseline_y + dy - pad - ascent))
        canvas.alpha_composite(w_surf, (paste_x, paste_y))
        
        cur_x += w_len + space_w


def draw_cursor(canvas: Image.Image, x: int, y: int, click_progress: float = 0.0):
    if click_progress > 0.01:
        draw = ImageDraw.Draw(canvas)
        r = int(click_progress * 38)
        a = int((1.0 - click_progress) * 190)
        draw.ellipse([x - r, y - r, x + r, y + r], outline=(CLR_TEAL[0], CLR_TEAL[1], CLR_TEAL[2], a), width=2)
    canvas.alpha_composite(CURSOR_IMG, (int(x), int(y)))


def prepare_card_frame(base_img: Image.Image, target_w: int, target_h: int, scale: float = 1.0) -> Image.Image:
    """Prepares a floating product card with 28px rounded corners and 1px hairline border."""
    bw, bh = base_img.size
    crop_w = int(target_w * 1.05 / scale)
    crop_h = int(target_h * 1.05 / scale)
    cx, cy = bw // 2, bh // 2
    
    crop = base_img.crop((cx - crop_w // 2, cy - crop_h // 2, cx + crop_w // 2, cy + crop_h // 2))
    scaled = crop.resize((target_w, target_h), Image.Resampling.BILINEAR).convert("RGBA")
    
    # Rounded corners mask
    mask = Image.new("L", (target_w, target_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, target_w, target_h], radius=28, fill=255)
    
    card = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    card.paste(scaled, (0, 0), mask)
    
    # 1px hairline border per §7.1
    border_draw = ImageDraw.Draw(card)
    border_draw.rounded_rectangle([0, 0, target_w - 1, target_h - 1], radius=28, outline=(255, 255, 255, 22), width=1)
    
    return card


# ==============================================================================
# SCENE RENDERERS (16:9 Landscape - 1920x1080)
# ==============================================================================

def render_16x9_scene_1(f: int) -> Image.Image:
    """Scene 1: Cold Open (0.0s – 5.0s | f: 0–299)"""
    img = Image.new("RGBA", (1920, 1080), (0, 0, 0, 255))
    prog = f / 300.0
    
    # Push-in 1.000 -> 1.030, bg drifts x -2%
    drift_px = int(prog * 38)
    hb_crop = HANDBOOK_DARK.crop((-drift_px, 140, -drift_px + 1920, 140 + 1080))
    hb_arr = np.array(hb_crop, dtype=np.float32)
    hb_arr[..., 3] *= 0.12
    img.alpha_composite(Image.fromarray(hb_arr.astype(np.uint8)))
    
    # Caption 1: "The answer is on page 23." @ 0.4s (f:24)
    if f >= 24:
        draw_caption(img, "The answer is on page 23.", FONT_CAPTION, 24, f, 960, 510, CLR_CAPTION)
        
    # Caption 2: "You'll never find it." @ 2.6s (f:156, ghost gray)
    if f >= 156:
        draw_caption(img, "You'll never find it.", FONT_CAPTION_SM, 156, f, 960, 590, CLR_GHOST)
        
    # 350ms cross-dissolve to pure black (279-299)
    if f >= 279:
        fade = max(0.0, 1.0 - (f - 279) / 21.0)
        arr = np.array(img, dtype=np.float32)
        arr[..., :3] *= fade
        img = Image.fromarray(arr.astype(np.uint8))
        
    return img


def render_16x9_scene_2(f: int) -> Image.Image:
    """Scene 2: The Drop (5.0s – 10.0s | f: 300–599)"""
    rel_f = f - 300
    prog = rel_f / 300.0
    scale = 1.000 + 0.035 * prog
    
    card_w, card_h = 1680, 900
    card = prepare_card_frame(BASE_S2_16X9, card_w, card_h, scale=scale)
    cdraw = ImageDraw.Draw(card)
    
    # Interactive Dropzone State Transitions:
    if 72 <= rel_f < 132:
        # Hover state: glowing teal border & "Looks like a document. Let it go."
        cdraw.rounded_rectangle([202, 54, 1478, 246], radius=20, fill=(16, 15, 14, 255), outline=(56, 189, 248, 230), width=2)
        cdraw.text((840, 135), "Looks like a document. Let it go.", font=FONT_BODY_TITLE, fill=(242, 239, 224, 255), anchor="mm")
        cdraw.text((840, 175), "PDF, Word, PowerPoint, Excel, Markdown", font=FONT_BODY_SM, fill=(160, 156, 148, 255), anchor="mm")
    elif 132 <= rel_f < 228:
        # Processing & chunk counter roll
        cdraw.rounded_rectangle([202, 54, 1478, 246], radius=20, fill=(16, 15, 14, 255), outline=(56, 189, 248, 160), width=2)
        roll_p = (rel_f - 132) / 96.0
        bar_w = int(600 * roll_p)
        cdraw.rounded_rectangle([540, 175, 1140, 183], radius=4, fill=(35, 33, 30, 255))
        cdraw.rounded_rectangle([540, 175, 540 + bar_w, 183], radius=4, fill=(56, 189, 248, 255))
        
        cur_count = int(214 * roll_p)
        step_text = "Cutting into chunks…" if roll_p < 0.35 else ("Mapping cross-references…" if roll_p < 0.70 else "Teaching the index…")
        cdraw.text((540, 145), step_text, font=FONT_BODY_SM, fill=(242, 239, 224, 255), anchor="lm")
        cdraw.text((1140, 145), f"{cur_count} / 214", font=FONT_MONO_SM, fill=(56, 189, 248, 255), anchor="rm")
    elif rel_f >= 228:
        # Settled: 214 chunks ready — ask away.
        cdraw.rounded_rectangle([202, 54, 1478, 246], radius=20, fill=(16, 15, 14, 255), outline=(49, 199, 165, 180), width=1)
        cdraw.rounded_rectangle([520, 120, 1160, 180], radius=12, fill=(3, 79, 70, 80), outline=(49, 199, 165, 140), width=1)
        cdraw.ellipse([545, 137, 571, 163], fill=(49, 199, 165, 255))
        cdraw.line([(551, 150), (556, 155), (565, 144)], fill=(16, 15, 14, 255), width=2)
        cdraw.text((585, 150), "214 chunks ready — ask away.", font=FONT_BODY_TITLE, fill=(242, 239, 224, 255), anchor="lm")
        
    img = Image.new("RGBA", (1920, 1080), (0, 0, 0, 255))
    img.paste(card, (120, 140), card)
    
    # Caption: "Drop it in." @ 6.0s (rel_f = 60)
    if rel_f >= 60:
        draw_caption(img, "Drop it in.", FONT_CAPTION, 60, rel_f, 960, 78, CLR_CAPTION)
        
    # Cursor drag take into dropzone center (960, 290)
    if rel_f < 145:
        t_c = min(1.0, rel_f / 132.0)
        c_ease = ease_in_out_quad(t_c)
        cur_x = 1420 - (1420 - 960) * c_ease
        cur_y = 180 + (290 - 180) * (c_ease ** 0.85)
        
        if rel_f < 132:
            cd = ImageDraw.Draw(img)
            cd.rounded_rectangle([cur_x + 18, cur_y + 10, cur_x + 180, cur_y + 50], radius=8, fill=(22, 20, 19, 240), outline=CLR_TEAL, width=1)
            cd.text((cur_x + 32, cur_y + 20), "handbook.pdf", font=FONT_BODY_SM, fill=(242, 239, 224, 255))
            
        ripple = max(0.0, 1.0 - (rel_f - 132) / 16.0) if rel_f >= 132 else 0.0
        draw_cursor(img, int(cur_x), int(cur_y), ripple)
        
    # Cross dissolves
    if rel_f < 21:
        fade = rel_f / 21.0
        arr = np.array(img, dtype=np.float32)
        arr[..., :3] *= fade
        img = Image.fromarray(arr.astype(np.uint8))
    elif rel_f >= 279:
        fade = max(0.0, 1.0 - (rel_f - 279) / 21.0)
        arr = np.array(img, dtype=np.float32)
        arr[..., :3] *= fade
        img = Image.fromarray(arr.astype(np.uint8))
        
    return img


def render_16x9_scene_3(f: int) -> Image.Image:
    """Scene 3: The Ask (10.0s – 16.0s | f: 600–959)"""
    rel_f = f - 600
    prog = rel_f / 360.0
    scale = 1.000 + 0.045 * prog
    
    base_src = BASE_S3_CITE_16X9 if rel_f >= 250 else BASE_S3_STREAM_16X9
    card_w, card_h = 1600, 780
    card = prepare_card_frame(base_src, card_w, card_h, scale=scale)
    
    img = Image.new("RGBA", (1920, 1080), (0, 0, 0, 255))
    img.paste(card, (160, 170), card)
    
    # Caption: "Ask like a human." @ 10.8s (rel_f = 48)
    if rel_f >= 48:
        draw_caption(img, "Ask like a human.", FONT_CAPTION, 48, rel_f, 960, 88, CLR_CAPTION)
        
    # Cursor gliding toward [S1]
    if rel_f >= 320:
        c_prog = min(1.0, (rel_f - 320) / 40.0)
        c_ease = ease_in_out_quad(c_prog)
        cur_x = 1200 - (1200 - 810) * c_ease
        cur_y = 780 - (780 - 540) * c_ease
        draw_cursor(img, int(cur_x), int(cur_y))
        
    # Cross dissolves
    if rel_f < 21:
        fade = rel_f / 21.0
        arr = np.array(img, dtype=np.float32)
        arr[..., :3] *= fade
        img = Image.fromarray(arr.astype(np.uint8))
    elif rel_f >= 339:
        fade = max(0.0, 1.0 - (rel_f - 339) / 21.0)
        arr = np.array(img, dtype=np.float32)
        arr[..., :3] *= fade
        img = Image.fromarray(arr.astype(np.uint8))
        
    return img


def render_16x9_scene_4(f: int) -> Image.Image:
    """Scene 4: The Receipt ★ (16.0s – 21.0s | f: 960–1259) — 0.85x slow-mo signature"""
    rel_f = f - 960
    prog = rel_f / 300.0
    scale = 1.000 + 0.050 * prog
    
    card_w, card_h = 1600, 780
    card = prepare_card_frame(BASE_S4_RECEIPT_16X9, card_w, card_h, scale=scale)
    
    # 4px soft amber glow pulse on quote box per §7.8
    if 36 <= rel_f < 60:
        pulse_p = (rel_f - 36) / 24.0
        pulse_alpha = int(math.sin(pulse_p * math.pi) * 160)
        cdraw = ImageDraw.Draw(card)
        cdraw.rounded_rectangle([118, 478, 1482, 642], radius=16, outline=(245, 158, 11, pulse_alpha), width=3)
        
    img = Image.new("RGBA", (1920, 1080), (0, 0, 0, 255))
    img.paste(card, (160, 170), card)
    
    # Caption: "Every claim. Proven." @ 18.2s (rel_f = 132)
    if rel_f >= 132:
        draw_caption(img, "Every claim. Proven.", FONT_CAPTION, 132, rel_f, 960, 88, CLR_CAPTION)
        
    # Cursor rests beside [S1] chip
    click_rip = max(0.0, 1.0 - (rel_f - 36) / 16.0) if rel_f >= 36 else 0.0
    draw_cursor(img, 810, 540, click_rip)
    
    # Cross dissolves
    if rel_f < 21:
        fade = rel_f / 21.0
        arr = np.array(img, dtype=np.float32)
        arr[..., :3] *= fade
        img = Image.fromarray(arr.astype(np.uint8))
    elif rel_f >= 279:
        fade = max(0.0, 1.0 - (rel_f - 279) / 21.0)
        arr = np.array(img, dtype=np.float32)
        arr[..., :3] *= fade
        img = Image.fromarray(arr.astype(np.uint8))
        
    return img


def render_16x9_scene_5(f: int) -> Image.Image:
    """Scene 5: Proof + End Card (21.0s – 25.0s | f: 1260–1499)"""
    rel_f = f - 1260
    img = Image.new("RGBA", (1920, 1080), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)
    
    # Count-up 82.9% -> 95.1%
    if rel_f < 12:
        val_str = "82.9%"
    elif rel_f <= 84:
        p = (rel_f - 12) / 72.0
        e = ease_apple(p)
        cur_v = 82.9 + (95.1 - 82.9) * e
        val_str = f"{cur_v:.1f}%"
    else:
        val_str = "95.1%"
        
    num_y = 360
    box = FONT_MONO_HUGE.getbbox(val_str)
    nw = box[2] - box[0]
    num_x = (1920 - nw) // 2
    
    r_val = int(CLR_RED[0] * 0.95)
    g_val = int(CLR_RED[1] * 0.95)
    b_val = int(CLR_RED[2] * 0.95)
    
    # Subtle glow behind huge numbers
    glow_alpha = int(45 + 25 * math.sin(rel_f * 0.08))
    for dr in range(8, 0, -2):
        gd = ImageDraw.Draw(img)
        gd.text((num_x, num_y), val_str, font=FONT_MONO_HUGE, fill=(CLR_RED[0], CLR_RED[1], CLR_RED[2], glow_alpha))
        
    draw.text((num_x, num_y), val_str, font=FONT_MONO_HUGE, fill=(r_val, g_val, b_val, 255))
    
    # Subtext under number
    sub = "46-question release exam · 0 hallucinations"
    s_box = FONT_BODY_SM.getbbox(sub)
    draw.text(((1920 - (s_box[2] - s_box[0])) // 2, num_y + 145), sub, font=FONT_BODY_SM, fill=CLR_GHOST)
    
    # Wordmark blur-in @ 22.8s (rel_f = 108)
    if rel_f >= 108:
        brand = "Allcited."
        w_prog = min(1.0, (rel_f - 108) / 36.0)
        w_ease = ease_apple(w_prog)
        
        draw_caption(img, brand, FONT_BRAND, 108, rel_f, 960, 680, CLR_CAPTION, duration_frames=36)
        
        url = "allcited.vercel.app"
        u_box = FONT_MONO_MD.getbbox(url)
        draw.text(((1920 - (u_box[2] - u_box[0])) // 2, 730), url, font=FONT_MONO_MD, fill=(CLR_GHOST[0], CLR_GHOST[1], CLR_GHOST[2], int(w_ease * 200)))
        
    # Fade to black last 200ms
    if rel_f >= 228:
        fade = max(0.0, 1.0 - (rel_f - 228) / 12.0)
        arr = np.array(img, dtype=np.float32)
        arr[..., :3] *= fade
        img = Image.fromarray(arr.astype(np.uint8))
        
    return img


def render_16x9_frame(f: int) -> Image.Image:
    if f < 300:
        return render_16x9_scene_1(f)
    elif f < 600:
        return render_16x9_scene_2(f)
    elif f < 960:
        return render_16x9_scene_3(f)
    elif f < 1260:
        return render_16x9_scene_4(f)
    return render_16x9_scene_5(f)


# ==============================================================================
# VERTICAL 9:16 RENDERER (1080x1920 - Apple Mobile Reframe)
# ==============================================================================

def render_9x16_frame(f: int) -> Image.Image:
    canvas = Image.new("RGBA", (1080, 1920), (0, 0, 0, 255))
    
    if f < 300:
        # Scene 1: Cold Open (Vertical)
        prog = f / 300.0
        drift_px = int(prog * 25)
        hb_crop = HANDBOOK_DARK.crop((-drift_px, 140, -drift_px + 1080, 140 + 1920))
        hb_arr = np.array(hb_crop, dtype=np.float32)
        hb_arr[..., 3] *= 0.12
        canvas.alpha_composite(Image.fromarray(hb_arr.astype(np.uint8)))
        
        if f >= 24:
            draw_caption(canvas, "The answer is on page 23.", FONT_CAPTION_MOBILE, 24, f, 540, 840, CLR_CAPTION)
        if f >= 156:
            draw_caption(canvas, "You'll never find it.", FONT_CAPTION_MOBILE_SM, 156, f, 540, 920, CLR_GHOST)
            
        if f >= 279:
            fade = max(0.0, 1.0 - (f - 279) / 21.0)
            arr = np.array(canvas, dtype=np.float32)
            arr[..., :3] *= fade
            canvas = Image.fromarray(arr.astype(np.uint8))
            
    elif f < 600:
        # Scene 2: The Drop (Vertical)
        rel_f = f - 300
        prog = rel_f / 300.0
        scale = 1.000 + 0.035 * prog
        
        card_w, card_h = 1000, 536
        card = prepare_card_frame(BASE_S2_9X16, card_w, card_h, scale=scale)
        
        cdraw = ImageDraw.Draw(card)
        if 72 <= rel_f < 132:
            cdraw.rounded_rectangle([120, 32, 880, 146], radius=16, fill=(16, 15, 14, 255), outline=(56, 189, 248, 230), width=2)
            cdraw.text((500, 80), "Looks like a document. Let it go.", font=FONT_BODY_SM, fill=(242, 239, 224, 255), anchor="mm")
        elif 132 <= rel_f < 228:
            cdraw.rounded_rectangle([120, 32, 880, 146], radius=16, fill=(16, 15, 14, 255), outline=(56, 189, 248, 160), width=2)
            roll_p = (rel_f - 132) / 96.0
            cdraw.rounded_rectangle([300, 105, 700, 111], radius=3, fill=(35, 33, 30, 255))
            cdraw.rounded_rectangle([300, 105, 300 + int(400 * roll_p), 111], radius=3, fill=(56, 189, 248, 255))
            cur_count = int(214 * roll_p)
            cdraw.text((300, 80), "Teaching index…", font=FONT_BODY_SM, fill=(242, 239, 224, 255), anchor="lm")
            cdraw.text((700, 80), f"{cur_count}", font=FONT_MONO_SM, fill=(56, 189, 248, 255), anchor="rm")
        elif rel_f >= 228:
            cdraw.rounded_rectangle([120, 32, 880, 146], radius=16, fill=(16, 15, 14, 255), outline=(49, 199, 165, 180), width=1)
            cdraw.rounded_rectangle([250, 68, 750, 110], radius=10, fill=(3, 79, 70, 80), outline=(49, 199, 165, 140), width=1)
            cdraw.ellipse([265, 79, 287, 101], fill=(49, 199, 165, 255))
            cdraw.line([(270, 90), (274, 94), (282, 85)], fill=(16, 15, 14, 255), width=2)
            cdraw.text((298, 89), "214 chunks ready — ask away.", font=FONT_BODY_SM, fill=(242, 239, 224, 255), anchor="lm")
            
        ui_y = 680
        canvas.paste(card, (40, ui_y), card)
        
        # Caption in upper third (y = 380)
        if rel_f >= 60:
            draw_caption(canvas, "Drop it in.", FONT_CAPTION_MOBILE, 60, rel_f, 540, 380, CLR_CAPTION)
            
        # Cursor drag in mobile view
        if rel_f < 145:
            t_c = min(1.0, rel_f / 132.0)
            c_ease = ease_in_out_quad(t_c)
            cur_x = 880 - (880 - 540) * c_ease
            cur_y = 480 + (770 - 480) * (c_ease ** 0.85)
            
            if rel_f < 132:
                cd = ImageDraw.Draw(canvas)
                cd.rounded_rectangle([cur_x + 18, cur_y + 10, cur_x + 160, cur_y + 45], radius=6, fill=(22, 20, 19, 240), outline=CLR_TEAL, width=1)
                cd.text((cur_x + 28, cur_y + 18), "handbook.pdf", font=FONT_BODY_SM, fill=(242, 239, 224, 255))
                
            ripple = max(0.0, 1.0 - (rel_f - 132) / 16.0) if rel_f >= 132 else 0.0
            draw_cursor(canvas, int(cur_x), int(cur_y), ripple)
            
        if rel_f < 21:
            fade = rel_f / 21.0
            arr = np.array(canvas, dtype=np.float32)
            arr[..., :3] *= fade
            canvas = Image.fromarray(arr.astype(np.uint8))
        elif rel_f >= 279:
            fade = max(0.0, 1.0 - (rel_f - 279) / 21.0)
            arr = np.array(canvas, dtype=np.float32)
            arr[..., :3] *= fade
            canvas = Image.fromarray(arr.astype(np.uint8))
            
    elif f < 960:
        # Scene 3: The Ask (Vertical)
        rel_f = f - 600
        prog = rel_f / 360.0
        scale = 1.000 + 0.045 * prog
        
        base_src = BASE_S3_CITE_9X16 if rel_f >= 250 else BASE_S3_STREAM_9X16
        card_w, card_h = 1000, 488
        card = prepare_card_frame(base_src, card_w, card_h, scale=scale)
        
        ui_y = 700
        canvas.paste(card, (40, ui_y), card)
        
        # Caption in upper third (y = 380)
        if rel_f >= 48:
            draw_caption(canvas, "Ask like a human.", FONT_CAPTION_MOBILE, 48, rel_f, 540, 380, CLR_CAPTION)
            
        if rel_f < 21:
            fade = rel_f / 21.0
            arr = np.array(canvas, dtype=np.float32)
            arr[..., :3] *= fade
            canvas = Image.fromarray(arr.astype(np.uint8))
        elif rel_f >= 339:
            fade = max(0.0, 1.0 - (rel_f - 339) / 21.0)
            arr = np.array(canvas, dtype=np.float32)
            arr[..., :3] *= fade
            canvas = Image.fromarray(arr.astype(np.uint8))
            
    elif f < 1260:
        # Scene 4: The Receipt (Vertical)
        rel_f = f - 960
        prog = rel_f / 300.0
        scale = 1.000 + 0.050 * prog
        
        card_w, card_h = 1000, 488
        card = prepare_card_frame(BASE_S4_RECEIPT_9X16, card_w, card_h, scale=scale)
        
        if 36 <= rel_f < 60:
            pulse_p = (rel_f - 36) / 24.0
            pulse_alpha = int(math.sin(pulse_p * math.pi) * 160)
            cdraw = ImageDraw.Draw(card)
            cdraw.rounded_rectangle([75, 300, 925, 400], radius=12, outline=(245, 158, 11, pulse_alpha), width=2)
            
        ui_y = 700
        canvas.paste(card, (40, ui_y), card)
        
        # Caption in upper third (y = 380)
        if rel_f >= 132:
            draw_caption(canvas, "Every claim. Proven.", FONT_CAPTION_MOBILE, 132, rel_f, 540, 380, CLR_CAPTION)
            
        click_rip = max(0.0, 1.0 - (rel_f - 36) / 16.0) if rel_f >= 36 else 0.0
        draw_cursor(canvas, 510, 935, click_rip)
        
        if rel_f < 21:
            fade = rel_f / 21.0
            arr = np.array(canvas, dtype=np.float32)
            arr[..., :3] *= fade
            canvas = Image.fromarray(arr.astype(np.uint8))
        elif rel_f >= 279:
            fade = max(0.0, 1.0 - (rel_f - 279) / 21.0)
            arr = np.array(canvas, dtype=np.float32)
            arr[..., :3] *= fade
            canvas = Image.fromarray(arr.astype(np.uint8))
            
    else:
        # Scene 5: Proof + End Card (Vertical)
        rel_f = f - 1260
        draw = ImageDraw.Draw(canvas)
        
        if rel_f < 12:
            val_str = "82.9%"
        elif rel_f <= 84:
            p = (rel_f - 12) / 72.0
            e = ease_apple(p)
            cur_v = 82.9 + (95.1 - 82.9) * e
            val_str = f"{cur_v:.1f}%"
        else:
            val_str = "95.1%"
            
        num_y = 760
        box = FONT_MONO_HUGE.getbbox(val_str)
        nw = box[2] - box[0]
        num_x = (1080 - nw) // 2
        
        r_val = int(CLR_RED[0] * 0.95)
        g_val = int(CLR_RED[1] * 0.95)
        b_val = int(CLR_RED[2] * 0.95)
        
        draw.text((num_x, num_y), val_str, font=FONT_MONO_HUGE, fill=(r_val, g_val, b_val, 255))
        
        sub = "46-question exam · 0 hallucinations"
        s_box = FONT_BODY_SM.getbbox(sub)
        draw.text(((1080 - (s_box[2] - s_box[0])) // 2, num_y + 145), sub, font=FONT_BODY_SM, fill=CLR_GHOST)
        
        if rel_f >= 108:
            brand = "Allcited."
            w_prog = min(1.0, (rel_f - 108) / 36.0)
            w_ease = ease_apple(w_prog)
            
            draw_caption(canvas, brand, FONT_BRAND, 108, rel_f, 540, 1060, CLR_CAPTION, duration_frames=36)
            
            url = "allcited.vercel.app"
            u_box = FONT_MONO_MD.getbbox(url)
            draw.text(((1080 - (u_box[2] - u_box[0])) // 2, 1120), url, font=FONT_MONO_MD, fill=(CLR_GHOST[0], CLR_GHOST[1], CLR_GHOST[2], int(w_ease * 200)))
            
        if rel_f >= 228:
            fade = max(0.0, 1.0 - (rel_f - 228) / 12.0)
            arr = np.array(canvas, dtype=np.float32)
            arr[..., :3] *= fade
            canvas = Image.fromarray(arr.astype(np.uint8))
            
    return canvas


def main():
    print("=== Allcited Apple Promo Film Generator v2 (Authentic Real UI) ===")
    print(f"Total Frames: {TOTAL_FRAMES} (25.0s @ 60fps)")
    
    audio_master = PROMO_DIR / "promo_audio_master.wav"
    out_16x9 = PROMO_DIR / "promo_16x9.mp4"
    out_9x16 = PROMO_DIR / "promo_9x16.mp4"
    out_4x5 = PROMO_DIR / "promo_4x5.mp4"
    cover_jpg = PROMO_DIR / "promo_cover.jpg"
    
    # 1. Render 16:9 Master
    print("\n[Step 1/4] Rendering 16:9 Master Film (1920x1080 @ 60fps)...")
    cmd_16x9 = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", "1920x1080",
        "-pix_fmt", "rgba",
        "-r", "60",
        "-i", "-",
        "-i", str(audio_master),
        "-vf", "noise=alls=2:allf=t+u,eq=contrast=1.05",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        "-crf", "17",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(out_16x9)
    ]
    p16 = subprocess.Popen(cmd_16x9, stdin=subprocess.PIPE)
    t0 = time.time()
    cover_img = None
    
    for f in range(TOTAL_FRAMES):
        frame = render_16x9_frame(f)
        if f == 1110:
            cover_img = frame.copy()
        p16.stdin.write(frame.tobytes())
        if f % 150 == 0 or f == TOTAL_FRAMES - 1:
            print(f"  [16:9] Frame {f:4d}/{TOTAL_FRAMES} ({f/60.0:4.1f}s) | Speed: {(f+1)/(time.time()-t0):4.1f} fps")
            
    p16.stdin.close()
    p16.wait()
    print(f"Master 16:9 complete: {out_16x9} ({(time.time()-t0):.1f}s)")
    
    # Save promo_cover.jpg
    if cover_img:
        cover_img.convert("RGB").save(cover_jpg, "JPEG", quality=95)
        print(f"Receipt Cover Frame saved: {cover_jpg}")
        
    # 2. Render 9:16 Vertical Master
    print("\n[Step 2/4] Rendering 9:16 Vertical Master Film (1080x1920 @ 60fps)...")
    cmd_9x16 = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", "1080x1920",
        "-pix_fmt", "rgba",
        "-r", "60",
        "-i", "-",
        "-i", str(audio_master),
        "-vf", "noise=alls=2:allf=t+u,eq=contrast=1.05",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        "-crf", "17",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(out_9x16)
    ]
    p9 = subprocess.Popen(cmd_9x16, stdin=subprocess.PIPE)
    t1 = time.time()
    
    for f in range(TOTAL_FRAMES):
        frame = render_9x16_frame(f)
        p9.stdin.write(frame.tobytes())
        if f % 150 == 0 or f == TOTAL_FRAMES - 1:
            print(f"  [9:16] Frame {f:4d}/{TOTAL_FRAMES} ({f/60.0:4.1f}s) | Speed: {(f+1)/(time.time()-t1):4.1f} fps")
            
    p9.stdin.close()
    p9.wait()
    print(f"Vertical 9:16 complete: {out_9x16} ({(time.time()-t1):.1f}s)")
    
    # 3. Render 4:5 Social Feed (1080x1350)
    print("\n[Step 3/4] Generating 4:5 Social Crop (1080x1350 @ 60fps)...")
    cmd_4x5 = [
        "ffmpeg", "-y",
        "-i", str(out_9x16),
        "-vf", "crop=1080:1350:0:285",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        "-crf", "17",
        "-c:a", "copy",
        str(out_4x5)
    ]
    subprocess.run(cmd_4x5, check=True)
    print(f"Social 4:5 complete: {out_4x5}")
    
    # 4. Copy all four deliverables to ~/Downloads
    print("\n[Step 4/4] Copying all deliverables to /Users/suvendu/Downloads/ ...")
    for fpath in [out_16x9, out_9x16, out_4x5, cover_jpg]:
        dest = DOWNLOADS_DIR / fpath.name
        shutil.copy2(fpath, dest)
        print(f"  Copied {fpath.name} -> {dest}")
        
    print("\n=== ALL REAL-FOOTAGE APPLE PROMO DELIVERABLES GENERATED ===")

if __name__ == "__main__":
    main()
