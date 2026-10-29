#!/usr/bin/env python3
"""
Allcited Promotional Video Generator v2 (Authentic Apple Keynote Edition)
Rebuilt from scratch using REAL PHOTOGRAPHY & SCREENSHOTS captured directly
from the live Allcited website (https://allcited.vercel.app).

Features:
- Photorealistic Apple Studio Display floating in deep obsidian space
- 100% Real captures of the live site: Hero, LiveMiniDemo, Receipts Drawer, 7-Stage Pipeline, Exam Scorecard
- Fluid 3D camera pan & zoom across real UI components
- Synced narration (Daniel - UK keynote cadence) with audio ducking
- Ambient analog synth score with sub-bass drone and UI sound design
- Full HD 1920x1080 @ 30fps (58.0 seconds / 1740 frames)
"""

import math
import os
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = REPO_ROOT / "assets"
REAL_PHOTOS_DIR = ASSETS_DIR / "real_site_photos"
STILLS_DIR = ASSETS_DIR / "promo_stills_v2"
STILLS_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_VIDEO = ASSETS_DIR / "allcited_apple_promo.mp4"
TEMP_DIR = Path("/tmp/allcited_promo_v2")
TEMP_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR = TEMP_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

WIDTH, HEIGHT = 1920, 1080
FPS = 30
DURATION_SEC = 58.0
TOTAL_FRAMES = int(FPS * DURATION_SEC)  # 1740 frames

# Load fonts
FONT_SF_PATH = "/System/Library/Fonts/SFNS.ttf"
FONT_MONO_PATH = "/System/Library/Fonts/SFNSMono.ttf"
FONT_HN_PATH = "/System/Library/Fonts/HelveticaNeue.ttc"

def get_font(size: int, bold: bool = False, mono: bool = False):
    try:
        if mono:
            return ImageFont.truetype(FONT_MONO_PATH, size)
        if bold:
            return ImageFont.truetype(FONT_HN_PATH, size, index=1)
        return ImageFont.truetype(FONT_SF_PATH, size)
    except Exception:
        try:
            return ImageFont.truetype(FONT_HN_PATH, size, index=1 if bold else 0)
        except Exception:
            return ImageFont.load_default()

FONT_HERO = get_font(90, bold=True)
FONT_TITLE = get_font(52, bold=True)
FONT_SUBTITLE = get_font(30, bold=False)
FONT_BODY = get_font(22, bold=False)
FONT_BODY_BOLD = get_font(22, bold=True)
FONT_CAPTION = get_font(16, bold=False)
FONT_MONO = get_font(20, mono=True)
FONT_MONO_SM = get_font(16, mono=True)

# Easing
def ease_out_cubic(x: float) -> float:
    return 1.0 - math.pow(1.0 - max(0.0, min(1.0, x)), 3.0)

def ease_in_out_cubic(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return 4.0 * x * x * x if x < 0.5 else 1.0 - math.pow(-2.0 * x + 2.0, 3.0) / 2.0

def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def generate_audio():
    """Generates authentic voiceover narration and cinematic score."""
    print("Generating voiceover narration and master cinematic soundtrack...")
    
    scenes = [
        ('scene1', "This is Allcited. Built on a simple, uncompromising premise: AI answers, with verifiable receipts.", 165),
        ('scene2', "Upload any document. Ask any question. Instead of guessing, Allcited retrieves the exact passages and stamps every claim with an interactive citation.", 170),
        ('scene3', "Click any citation, and the receipts drawer slides open. Revealing the original sentence, the exact page number, and the full contextual paragraph. Zero hallucinations.", 165),
        ('scene4', "Under the hood: a seven-stage inspection pipeline. BM25 keyword matching. FAISS semantic vectors. Cross-encoder re-ranking. And automatic two-hop reference resolution.", 175),
        ('scene5', "Tested publicly. Eighty-seven percent passage accuracy across forty-six rigorous enterprise test questions on every release.", 170),
        ('scene6', "Allcited. Don't take AI's word for it. Check the receipts.", 160)
    ]

    for sid, text, rate in scenes:
        aiff = AUDIO_DIR / f"{sid}.aiff"
        wav = AUDIO_DIR / f"{sid}.wav"
        if not wav.exists():
            subprocess.run(['say', '-v', 'Daniel', '-r', str(rate), text, '-o', str(aiff)], check=True)
            subprocess.run(['ffmpeg', '-y', '-i', str(aiff), str(wav)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    sr = 44100
    num_samples = int(sr * DURATION_SEC)
    t = np.linspace(0, DURATION_SEC, num_samples, endpoint=False)

    left = np.zeros(num_samples, dtype=np.float32)
    right = np.zeros(num_samples, dtype=np.float32)

    # Ambient deep drone (55Hz A1)
    drone = 0.09 * np.sin(2 * np.pi * 55.0 * t) + 0.03 * np.sin(2 * np.pi * 110.0 * t)
    left += drone
    right += drone

    # Emotional Apple chord progression
    chords = [
        (0.0, 8.5, [110.0, 130.81, 164.81, 246.94]),    # Am9
        (8.5, 19.5, [87.31, 110.0, 130.81, 164.81]),    # Fmaj7
        (19.5, 32.5, [73.42, 110.0, 130.81, 174.61]),   # Dm7
        (32.5, 45.5, [87.31, 110.0, 146.83, 196.0]),    # Fadd9 / Gsus
        (45.5, 53.5, [65.41, 98.0, 130.81, 164.81]),    # Cmaj
        (53.5, 58.0, [55.0, 110.0, 164.81, 220.0])     # Am resolution
    ]

    for start, end, freqs in chords:
        idx_s = int(start * sr)
        idx_e = min(num_samples, int(end * sr))
        t_c = t[idx_s:idx_e] - start
        chord_len = end - start
        att = np.clip(t_c / 1.5, 0, 1)
        rel = np.clip((chord_len - t_c) / 1.5, 0, 1)
        env = np.sin(att * np.pi / 2) * np.sin(rel * np.pi / 2)
        for i, f in enumerate(freqs):
            detune = 0.25 * (i % 2 * 2 - 1)
            left[idx_s:idx_e] += 0.07 * np.sin(2 * np.pi * (f - detune) * t_c) * env
            right[idx_s:idx_e] += 0.07 * np.sin(2 * np.pi * (f + detune) * t_c) * env

    # Sub pulse in technical pipeline (32.5s to 45.5s)
    p_s, p_e = int(32.5 * sr), int(45.5 * sr)
    p_t = t[p_s:p_e]
    pulse = 0.07 * np.sin(2 * np.pi * 65.0 * p_t) * (np.sin(2 * np.pi * 2.0 * p_t) ** 16)
    left[p_s:p_e] += pulse
    right[p_s:p_e] += pulse

    # Timeline cues for voiceover
    cues = [
        ('scene1', 0.8),
        ('scene2', 9.2),
        ('scene3', 20.2),
        ('scene4', 33.2),
        ('scene5', 45.8),
        ('scene6', 53.8),
    ]

    master_l = left * 0.40
    master_r = right * 0.40

    for name, offset in cues:
        wav_path = AUDIO_DIR / f"{name}.wav"
        with wave.open(str(wav_path), 'rb') as wf:
            n_frames = wf.getnframes()
            f_rate = wf.getframerate()
            raw = wf.readframes(n_frames)
            voice = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            if f_rate != sr:
                t_orig = np.linspace(0, n_frames / f_rate, n_frames)
                t_new = np.linspace(0, n_frames / f_rate, int(n_frames * sr / f_rate))
                voice = np.interp(t_new, t_orig, voice)
        idx_s = int(offset * sr)
        idx_e = min(num_samples, idx_s + len(voice))
        c_len = idx_e - idx_s
        duck_s = max(0, idx_s - int(0.2 * sr))
        duck_e = min(num_samples, idx_e + int(0.3 * sr))
        master_l[duck_s:duck_e] *= 0.65
        master_r[duck_s:duck_e] *= 0.65
        master_l[idx_s:idx_e] += voice[:c_len] * 0.95
        master_r[idx_s:idx_e] += voice[:c_len] * 0.95

    # Sound effects
    # 1. Glass chime at 1.0s (Hero reveal)
    t_ch1 = np.linspace(0, 1.5, int(sr * 1.5))
    ch1 = 0.16 * np.sin(2 * np.pi * 1760.0 * t_ch1) * np.exp(-3.5 * t_ch1)
    c1_idx = int(0.9 * sr)
    master_l[c1_idx:c1_idx+len(ch1)] += ch1
    master_r[c1_idx:c1_idx+len(ch1)] += ch1

    # 2. Haptic click at 20.8s (Click citation [S1])
    t_click = np.linspace(0, 0.08, int(sr * 0.08))
    click = 0.25 * np.sin(2 * np.pi * 1200.0 * t_click) * np.exp(-40.0 * t_click)
    cl_idx = int(20.8 * sr)
    master_l[cl_idx:cl_idx+len(click)] += click
    master_r[cl_idx:cl_idx+len(click)] += click

    # 3. Slide whoosh at 21.0s (Receipts Drawer opens)
    t_whoosh = np.linspace(0, 0.8, int(sr * 0.8))
    whoosh = 0.14 * np.sin(2 * np.pi * (400.0 + 800.0 * (1.0 - t_whoosh)) * t_whoosh) * np.exp(-4.5 * t_whoosh)
    w_idx = int(21.0 * sr)
    master_l[w_idx:w_idx+len(whoosh)] += whoosh
    master_r[w_idx:w_idx+len(whoosh)] += whoosh

    # 4. Final chime at 54.0s (Allcited logo)
    t_fin = np.linspace(0, 2.0, int(sr * 2.0))
    fin_chime = 0.18 * np.sin(2 * np.pi * 880.0 * t_fin) * np.exp(-2.5 * t_fin) + 0.10 * np.sin(2 * np.pi * 1760.0 * t_fin) * np.exp(-3.5 * t_fin)
    f_idx = int(54.0 * sr)
    master_l[f_idx:f_idx+len(fin_chime)] += fin_chime
    master_r[f_idx:f_idx+len(fin_chime)] += fin_chime

    # Normalize
    m_max = max(np.max(np.abs(master_l)), np.max(np.abs(master_r)), 1e-6)
    master_l = (master_l / m_max * 0.92 * 32767).astype(np.int16)
    master_r = (master_r / m_max * 0.92 * 32767).astype(np.int16)

    master = np.empty((num_samples * 2,), dtype=np.int16)
    master[0::2] = master_l
    master[1::2] = master_r

    master_path = TEMP_DIR / "master_soundtrack.wav"
    with wave.open(str(master_path), 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(master.tobytes())

    print(f"Master soundtrack generated: {master_path}")
    return master_path


# --- Image Caching & High-Performance Rendering ---

print("Pre-loading and preparing high-resolution real site captures...")
RAW_PHOTOS = {
    'hero': Image.open(REAL_PHOTOS_DIR / "01_hero_landing.png").convert("RGB"),
    'streaming': Image.open(REAL_PHOTOS_DIR / "02_live_demo_streaming.png").convert("RGB"),
    'citations': Image.open(REAL_PHOTOS_DIR / "03_live_demo_citations.png").convert("RGB"),
    'drawer': Image.open(REAL_PHOTOS_DIR / "04_receipts_drawer_open.png").convert("RGB"),
    'pipeline_head': Image.open(REAL_PHOTOS_DIR / "05_pipeline_stages.png").convert("RGB"),
    'pipeline_grid': Image.open(REAL_PHOTOS_DIR / "06_pipeline_grid.png").convert("RGB"),
    'exam': Image.open(REAL_PHOTOS_DIR / "07_exam_scorecard.png").convert("RGB"),
    'workspace': Image.open(REAL_PHOTOS_DIR / "10_workspace_chat.png").convert("RGB"),
}

# Pre-scale standard views to 2560px width for fast 3.3ms crop/scaling
SCALED_2560 = {}
for k, im in RAW_PHOTOS.items():
    w2560 = 2560
    h2560 = int(im.height * 2560 / im.width)
    SCALED_2560[k] = im.resize((w2560, h2560), Image.Resampling.LANCZOS)

# Pre-render Apple Studio Display frame mask
DISP_W, DISP_H = 1580, 890
DISPLAY_MASK = Image.new("L", (DISP_W, DISP_H), 0)
d_draw = ImageDraw.Draw(DISPLAY_MASK)
d_draw.rounded_rectangle([0, 0, DISP_W, DISP_H], radius=20, fill=255)

print("All site photo caches ready!")


def draw_apple_studio_display(canvas: Image.Image, screen_content: Image.Image, cx: int, cy: int, w: int, h: int, alpha: float = 1.0):
    """Draws a photorealistic Apple Studio Display housing the real website screenshot."""
    if alpha <= 0.02:
        return
    x0 = cx - w // 2
    y0 = cy - h // 2
    x1 = cx + w // 2
    y1 = cy + h // 2

    draw = ImageDraw.Draw(canvas)

    # 1. Soft ambient shadow behind display
    shadow_pad = 28
    draw.rounded_rectangle([x0 - shadow_pad, y0 - shadow_pad, x1 + shadow_pad, y1 + shadow_pad + 16], radius=32, fill=(0, 0, 0, int(160 * alpha)))

    # 2. Outer Aluminum Bezel (Space Grey titanium finish)
    bezel = 10
    draw.rounded_rectangle([x0 - bezel, y0 - bezel, x1 + bezel, y1 + bezel], radius=26, fill=(28, 30, 36), outline=(70, 75, 88), width=2)

    # 3. Inner Screen Content
    screen_resized = screen_content.resize((w, h), Image.Resampling.BILINEAR)
    # Mask to rounded inner corners
    if (w, h) == (DISP_W, DISP_H):
        canvas.paste(screen_resized, (x0, y0), DISPLAY_MASK)
    else:
        m = Image.new("L", (w, h), 0)
        md = ImageDraw.Draw(m)
        md.rounded_rectangle([0, 0, w, h], radius=16, fill=255)
        canvas.paste(screen_resized, (x0, y0), m)

    # 4. Glass reflection sheen across the top-right corner
    glare = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glare)
    g_draw.polygon([(w - 300, 0), (w, 0), (w, 200)], fill=(255, 255, 255, int(15 * alpha)))
    canvas.paste(glare, (x0, y0), glare)

    # 5. Display stand (minimalist aluminum foot at bottom)
    stand_w = 260
    stand_top = y1 + bezel
    stand_bot = stand_top + 45
    draw.rectangle([cx - stand_w // 2, stand_top, cx + stand_w // 2, stand_bot], fill=(38, 41, 48), outline=(60, 65, 75), width=1)
    # Base foot
    foot_w = 420
    draw.rounded_rectangle([cx - foot_w // 2, stand_bot - 4, cx + foot_w // 2, stand_bot + 8], radius=4, fill=(50, 54, 62), outline=(75, 80, 92), width=1)


def draw_cursor(canvas: Image.Image, x: int, y: int, click_pulse: float = 0.0):
    """Draws a crisp macOS cursor at (x, y) with optional click ripple."""
    draw = ImageDraw.Draw(canvas)
    # Click ripple
    if click_pulse > 0.01:
        r = int(click_pulse * 40)
        a = int((1.0 - click_pulse) * 200)
        draw.ellipse([x - r, y - r, x + r, y + r], outline=(56, 189, 248, a), width=2)

    # macOS pointer arrow
    points = [
        (x, y),
        (x, y + 24),
        (x + 6, y + 19),
        (x + 11, y + 29),
        (x + 15, y + 27),
        (x + 10, y + 17),
        (x + 18, y + 17)
    ]
    draw.polygon(points, fill=(255, 255, 255), outline=(0, 0, 0))


# --- Scene Renderers ---

def render_scene_1(frame_idx: int) -> Image.Image:
    """Act 1: The Reveal — Floating Studio Display with Real Homepage (0.0s – 8.5s | Frames 0 to 255)"""
    sec = frame_idx / FPS
    img = Image.new("RGBA", (WIDTH, HEIGHT), (2, 4, 8, 255))
    draw = ImageDraw.Draw(img)

    # Ambient deep sea aurora glow
    pulse = 0.25 + 0.10 * math.sin(sec * 1.2)
    # Soft background glow
    glow = Image.new("RGBA", (320, 180), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([60, 30, 260, 150], fill=(30, 64, 175, int(70 * pulse)))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=25)).resize((WIDTH, HEIGHT))
    img.paste(glow, (0, 0), glow)

    # Camera push-in animation (starts wide and glides into center view)
    t_cam = ease_out_cubic(min(1.0, sec / 6.0))
    scale = 0.82 + 0.18 * t_cam
    cur_w = int(DISP_W * scale)
    cur_h = int(DISP_H * scale)
    cy = int(500 - (1.0 - t_cam) * 30)

    # Screen content: real homepage screenshot
    screen_crop = SCALED_2560['hero'].crop((0, 0, 2560, 1440))
    draw_apple_studio_display(img, screen_crop, WIDTH // 2, cy, cur_w, cur_h)

    # Overlay Tagline & Wordmark
    t_text = smoothstep(0.6, 2.0, sec)
    if sec > 6.8:
        t_text *= (1.0 - smoothstep(6.8, 8.5, sec))
    alpha_text = ease_out_cubic(t_text)

    if alpha_text > 0.02:
        draw.text((WIDTH // 2, 70), "Allcited", font=FONT_TITLE, fill=(255, 255, 255, int(255 * alpha_text)), anchor="mm")
        draw.text((WIDTH // 2, 115), "AI Answers, with Verifiable Receipts.", font=FONT_SUBTITLE, fill=(147, 197, 253, int(230 * alpha_text)), anchor="mm")

    return img.convert("RGB")


def render_scene_2(frame_idx: int) -> Image.Image:
    """Act 2: The Real Live Question & Streaming Answer (8.5s – 19.5s | Frames 255 to 585)"""
    sec = (frame_idx - 255) / FPS
    img = Image.new("RGBA", (WIDTH, HEIGHT), (3, 6, 12, 255))
    draw = ImageDraw.Draw(img)

    # Smooth macro zoom into the live demo box
    # On 2560px cache, the demo box is roughly at x=[500..2060], y=[500..1200]
    t_zoom = ease_out_cubic(smoothstep(0.0, 2.5, sec))
    
    # Switch from streaming screenshot (02) to citations screenshot (03) at 4.5s
    source_img = SCALED_2560['streaming'] if sec < 4.5 else SCALED_2560['citations']

    # Interpolate crop region for macro camera move
    # Start: overview (crop 2560 x 1440)
    # End: tight macro on the Q&A box (crop 1600 x 900)
    crop_w = int(2400 - t_zoom * 900)
    crop_h = int(1350 - t_zoom * 506)
    crop_x = int(80 + t_zoom * 400)
    crop_y = int(60 + t_zoom * 380)

    cropped = source_img.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
    draw_apple_studio_display(img, cropped, WIDTH // 2, 530, DISP_W, DISP_H)

    # Highlight Pill Callout over citation chip after 5.0s
    if sec > 5.0:
        t_pill = smoothstep(5.0, 6.2, sec)
        p_alpha = ease_out_cubic(t_pill)
        # Callout card at top
        draw.rounded_rectangle([WIDTH // 2 - 280, 50, WIDTH // 2 + 280, 110], radius=16, fill=(15, 23, 42, int(220 * p_alpha)), outline=(56, 189, 248, int(240 * p_alpha)), width=2)
        draw.text((WIDTH // 2, 80), "[S1] INTERACTIVE CITATION STAMP", font=FONT_MONO, fill=(240, 253, 250, int(255 * p_alpha)), anchor="mm")

    return img.convert("RGB")


def render_scene_3(frame_idx: int) -> Image.Image:
    """Act 3: The Climax — Clicking [S1] & Opening Real Receipts Drawer (19.5s – 32.5s | Frames 585 to 975)"""
    sec = (frame_idx - 585) / FPS
    img = Image.new("RGBA", (WIDTH, HEIGHT), (2, 4, 10, 255))
    draw = ImageDraw.Draw(img)

    # From 0.0s to 1.8s: Cursor moves to citation chip [S1]
    # At 1.8s: Click sound + ripple
    # From 1.8s onward: Cut to real receipts drawer open (04_receipts_drawer_open.png) with camera tracking across the drawer
    
    if sec < 1.8:
        # Show citations view
        screen_content = SCALED_2560['citations'].crop((350, 400, 2150, 1412))
        draw_apple_studio_display(img, screen_content, WIDTH // 2, 530, DISP_W, DISP_H)

        # Animate cursor moving toward citation chip
        t_cursor = ease_in_out_cubic(sec / 1.8)
        cur_x = int(600 + t_cursor * 480)
        cur_y = int(750 - t_cursor * 120)
        draw_cursor(img, cur_x, cur_y)
    else:
        # Click happened! Show 04_receipts_drawer_open.png
        drawer_time = sec - 1.8
        click_pulse = max(0.0, 1.0 - drawer_time / 0.4) if drawer_time < 0.4 else 0.0

        # Camera smoothly pans right to frame the real Receipts Drawer
        t_pan = ease_out_cubic(smoothstep(0.0, 2.5, drawer_time))
        # Crop region moves toward the right third of the screen where the real drawer lives
        crop_w = int(2000 - t_pan * 400)
        crop_h = int(1125 - t_pan * 225)
        crop_x = int(300 + t_pan * 580)
        crop_y = int(250 + t_pan * 80)

        cropped = SCALED_2560['drawer'].crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
        draw_apple_studio_display(img, cropped, WIDTH // 2, 530, DISP_W, DISP_H)

        if click_pulse > 0:
            draw_cursor(img, 1080, 630, click_pulse=click_pulse)

        # Callout Banner: "100% GROUNDED · VERIFIED SOURCE RECEIPT"
        t_badge = smoothstep(1.5, 2.8, drawer_time)
        b_alpha = ease_out_cubic(t_badge)
        if b_alpha > 0.02:
            draw.rounded_rectangle([WIDTH // 2 - 320, 50, WIDTH // 2 + 320, 110], radius=18, fill=(10, 25, 47, int(230 * b_alpha)), outline=(16, 185, 129, int(240 * b_alpha)), width=2)
            draw.text((WIDTH // 2, 80), "VERIFIED DOWN TO PAGE, PARAGRAPH & CELL", font=FONT_MONO, fill=(52, 211, 153, int(255 * b_alpha)), anchor="mm")

    return img.convert("RGB")


def render_scene_4(frame_idx: int) -> Image.Image:
    """Act 4: Under The Hood — The 7-Stage Pipeline (32.5s – 45.5s | Frames 975 to 1365)"""
    sec = (frame_idx - 975) / FPS
    img = Image.new("RGBA", (WIDTH, HEIGHT), (4, 7, 15, 255))
    draw = ImageDraw.Draw(img)

    # Rhythmic camera glide across the real /how-it-works pipeline grid
    # 06_pipeline_grid has height 3285px.
    # Camera slowly scrolls down the real stage cards:
    # 01 Ingest -> 02 Chunking -> 03 Hybrid BM25+FAISS -> 04 Cross-Encoder -> 05 Two-Hop -> 06 Grounded -> 07 Post-Pass
    t_scroll = ease_in_out_cubic(sec / 13.0)
    scroll_y = int(200 + t_scroll * 1200)

    cropped = SCALED_2560['pipeline_grid'].crop((150, scroll_y, 150 + 2260, scroll_y + 1270))
    draw_apple_studio_display(img, cropped, WIDTH // 2, 540, DISP_W, DISP_H)

    # Apple Keynote Header Badge
    draw.rounded_rectangle([WIDTH // 2 - 250, 45, WIDTH // 2 + 250, 95], radius=16, fill=(15, 23, 42, 230), outline=(99, 102, 241, 200), width=2)
    draw.text((WIDTH // 2, 70), "7-STAGE INSPECTION PIPELINE", font=FONT_MONO, fill=(199, 210, 254), anchor="mm")

    return img.convert("RGB")


def render_scene_5(frame_idx: int) -> Image.Image:
    """Act 5: Public Proof — The Empirical Scoreboard (45.5s – 53.5s | Frames 1365 to 1605)"""
    sec = (frame_idx - 1365) / FPS
    img = Image.new("RGBA", (WIDTH, HEIGHT), (3, 5, 12, 255))
    draw = ImageDraw.Draw(img)

    # Cut to real /exam scoreboard
    t_pan = ease_out_cubic(min(1.0, sec / 3.0))
    crop_y = int(300 + t_pan * 250)

    cropped = SCALED_2560['exam'].crop((100, crop_y, 100 + 2360, crop_y + 1327))
    draw_apple_studio_display(img, cropped, WIDTH // 2, 540, DISP_W, DISP_H)

    # Top Metric Banner
    draw.rounded_rectangle([WIDTH // 2 - 300, 45, WIDTH // 2 + 300, 95], radius=16, fill=(15, 23, 42, 230), outline=(56, 189, 248, 200), width=2)
    draw.text((WIDTH // 2, 70), "TESTED PUBLICLY ON EVERY RELEASE", font=FONT_MONO, fill=(147, 197, 253), anchor="mm")

    return img.convert("RGB")


def render_scene_6(frame_idx: int) -> Image.Image:
    """Act 6: The Signature Finale (53.5s – 58.0s | Frames 1605 to 1740)"""
    sec = (frame_idx - 1605) / FPS
    img = Image.new("RGBA", (WIDTH, HEIGHT), (2, 3, 6, 255))
    draw = ImageDraw.Draw(img)

    t_in = smoothstep(0.0, 1.2, sec)
    t_out = 1.0 - smoothstep(3.8, 4.5, sec)
    alpha = ease_out_cubic(t_in) * t_out

    # Pull-back Studio Display showing the real workspace
    scale = 0.90 - 0.08 * t_in
    cur_w = int(DISP_W * scale)
    cur_h = int(DISP_H * scale)
    
    screen_crop = SCALED_2560['workspace'].crop((0, 0, 2560, 1440))
    draw_apple_studio_display(img, screen_crop, WIDTH // 2, 590, cur_w, cur_h, alpha=0.85)

    # Center Typography: Apple Keynote Signature
    c_white = int(255 * alpha)
    draw.text((WIDTH // 2, 120), "Allcited", font=FONT_HERO, fill=(c_white, c_white, c_white), anchor="mm")
    draw.text((WIDTH // 2, 190), "Answers, with receipts.", font=FONT_TITLE, fill=(147, 197, 253, int(240 * alpha)), anchor="mm")

    # Domain Pill
    draw.rounded_rectangle([WIDTH // 2 - 180, 230, WIDTH // 2 + 180, 280], radius=25, fill=(15, 23, 42, int(200 * alpha)), outline=(56, 189, 248, int(220 * alpha)), width=2)
    draw.text((WIDTH // 2, 255), "allcited.vercel.app", font=FONT_MONO, fill=(240, 253, 250, int(255 * alpha)), anchor="mm")

    return img.convert("RGB")


def render_frame(frame_idx: int) -> Image.Image:
    """Dispatches frame index to corresponding scene."""
    if frame_idx < 255:
        return render_scene_1(frame_idx)
    elif frame_idx < 585:
        return render_scene_2(frame_idx)
    elif frame_idx < 975:
        return render_scene_3(frame_idx)
    elif frame_idx < 1365:
        return render_scene_4(frame_idx)
    elif frame_idx < 1605:
        return render_scene_5(frame_idx)
    else:
        return render_scene_6(frame_idx)


def compile_video():
    """Generates audio and renders 1740 frames directly into ffmpeg."""
    master_audio_path = generate_audio()

    print(f"Starting video frame rendering: {TOTAL_FRAMES} frames ({DURATION_SEC}s @ {FPS}fps)...")
    
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",                       # stdin pipe for raw frames
        "-i", str(master_audio_path),     # master soundtrack
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "faster",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(OUTPUT_VIDEO)
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    key_stills = {
        120: "01_studio_display_hero.png",
        420: "02_live_demo_streaming.png",
        720: "03_receipts_drawer_inspection.png",
        1150: "04_seven_stage_pipeline.png",
        1480: "05_public_exam_scorecard.png",
        1680: "06_apple_signature_verdict.png"
    }

    for i in range(TOTAL_FRAMES):
        frame = render_frame(i)
        
        # Save keyframe still
        if i in key_stills:
            frame.save(STILLS_DIR / key_stills[i])

        # Write raw bytes to ffmpeg
        proc.stdin.write(frame.tobytes())

        if i % 180 == 0 or i == TOTAL_FRAMES - 1:
            print(f"Render progress: frame {i}/{TOTAL_FRAMES} ({(i/TOTAL_FRAMES)*100:.1f}%)")

    proc.stdin.close()
    proc.wait()

    if proc.returncode != 0:
        print("FFmpeg error during compilation")
        sys.exit(1)

    print(f"Authentic Apple Keynote Film generated successfully! Output: {OUTPUT_VIDEO}")
    file_size_mb = OUTPUT_VIDEO.stat().st_size / (1024 * 1024)
    print(f"Output file size: {file_size_mb:.2f} MB")

    # Copy to user's ~/Downloads immediately
    downloads_path = Path("/Users/suvendu/Downloads/allcited_apple_promo.mp4")
    subprocess.run(["cp", str(OUTPUT_VIDEO), str(downloads_path)], check=True)
    print(f"Saved directly to Downloads: {downloads_path}")


if __name__ == "__main__":
    compile_video()
