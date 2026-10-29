#!/usr/bin/env python3
"""
Allcited Promotional Video Generator (Apple Keynote Style)
Generates a Full HD (1920x1080 @ 30fps) Apple-style product film with:
- Minimalist space-black aesthetic & Apple Intelligence chromatic radial aura
- SF / Helvetica Neue typography with precision tracking and hierarchy
- Timed voiceover narration (Daniel - UK keynote cadence)
- Synthesized cinematic ambient score with sub-bass drone and chord progression
- Live mock UI showing the 4 RAG Traps, streaming answer, and sliding Receipts Drawer
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
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_VIDEO = ASSETS_DIR / "allcited_apple_promo.mp4"
TEMP_DIR = Path("/tmp/allcited_promo")
TEMP_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR = TEMP_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

WIDTH, HEIGHT = 1920, 1080
FPS = 30
DURATION_SEC = 46.0
TOTAL_FRAMES = int(FPS * DURATION_SEC)  # 1380 frames

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

# Pre-load common fonts
FONT_TITLE_HERO = get_font(100, bold=True)
FONT_TITLE_LG = get_font(64, bold=True)
FONT_TITLE_MD = get_font(44, bold=True)
FONT_SUBTITLE = get_font(32, bold=False)
FONT_BODY = get_font(24, bold=False)
FONT_BODY_BOLD = get_font(24, bold=True)
FONT_CAPTION = get_font(18, bold=False)
FONT_MONO_SM = get_font(20, mono=True)
FONT_MONO_XS = get_font(16, mono=True)
FONT_MONO_MD = get_font(26, mono=True)

# Easing functions
def ease_out_cubic(x: float) -> float:
    return 1.0 - math.pow(1.0 - max(0.0, min(1.0, x)), 3.0)

def ease_in_out_cubic(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return 4.0 * x * x * x if x < 0.5 else 1.0 - math.pow(-2.0 * x + 2.0, 3.0) / 2.0

def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def generate_audio():
    """Generates the voiceovers, ambient music, sound effects, and mixes master audio."""
    print("Generating voiceover narration and cinematic soundtrack...")
    
    scenes = [
        ('scene1', "Every day, critical decisions rely on complex documents. And increasingly, on AI.", 165),
        ('scene2', "But conventional AI has a flaw. When context gets split, it hallucinates. It guesses.", 170),
        ('scene3', "We believed there had to be a better way. Introducing Allcited.", 160),
        ('scene4', "Engineered to solve the four fatal RAG traps. Hierarchical breadcrumbs. Cross-encoder re-ranking. Two-hop graph expansion. And query decomposition.", 175),
        ('scene5', "Every claim comes with receipts. Verifiable down to the exact page, paragraph, and cell. With zero cloud egress.", 170),
        ('scene6', "Allcited. Don't take AI's word for it. Check the receipts.", 160),
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

    # Ambient sub drone
    drone = 0.08 * np.sin(2 * np.pi * 55.0 * t) + 0.03 * np.sin(2 * np.pi * 110.0 * t)
    left += drone
    right += drone

    # Chords
    chords = [
        (0.0, 14.0, [110.0, 130.81, 164.81, 220.0]),
        (14.0, 22.0, [87.31, 110.0, 130.81, 164.81, 261.63]),
        (22.0, 33.0, [65.41, 98.0, 130.81, 164.81, 196.0]),
        (33.0, 40.5, [98.0, 146.83, 196.0, 246.94, 293.66]),
        (40.5, 46.0, [55.0, 110.0, 164.81, 220.0])
    ]

    for start, end, freqs in chords:
        idx_s = int(start * sr)
        idx_e = min(num_samples, int(end * sr))
        t_c = t[idx_s:idx_e] - start
        chord_len = end - start
        att = np.clip(t_c / 1.2, 0, 1)
        rel = np.clip((chord_len - t_c) / 1.2, 0, 1)
        env = np.sin(att * np.pi / 2) * np.sin(rel * np.pi / 2)
        for i, f in enumerate(freqs):
            detune = 0.25 * (i % 2 * 2 - 1)
            left[idx_s:idx_e] += 0.07 * np.sin(2 * np.pi * (f - detune) * t_c) * env
            right[idx_s:idx_e] += 0.07 * np.sin(2 * np.pi * (f + detune) * t_c) * env

    # Rhythmic pulse (22.0s to 33.0s)
    p_s, p_e = int(22.0 * sr), int(33.0 * sr)
    p_t = t[p_s:p_e]
    pulse = 0.07 * np.sin(2 * np.pi * 65.0 * p_t) * (np.sin(2 * np.pi * 2.0 * p_t) ** 16)
    left[p_s:p_e] += pulse
    right[p_s:p_e] += pulse

    # Mixed with voiceover cues
    cues = [
        ('scene1', 0.8),
        ('scene2', 7.4),
        ('scene3', 14.5),
        ('scene4', 20.0),
        ('scene5', 31.5),
        ('scene6', 41.0),
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

    # Glass chime at 14.4s
    t_chime = np.linspace(0, 1.5, int(sr * 1.5))
    chime = 0.16 * np.sin(2 * np.pi * 1760.0 * t_chime) * np.exp(-3.5 * t_chime) + 0.09 * np.sin(2 * np.pi * 3520.0 * t_chime) * np.exp(-5.0 * t_chime)
    c_idx = int(14.3 * sr)
    master_l[c_idx:c_idx+len(chime)] += chime
    master_r[c_idx:c_idx+len(chime)] += chime

    # Drawer ping at 33.6s
    t_ping = np.linspace(0, 0.8, int(sr * 0.8))
    ping = 0.18 * np.sin(2 * np.pi * 2093.0 * t_ping) * np.exp(-5.5 * t_ping)
    p_idx = int(33.6 * sr)
    master_l[p_idx:p_idx+len(ping)] += ping
    master_r[p_idx:p_idx+len(ping)] += ping

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


# --- Graphics Primitives ---

def draw_radial_aura(img: Image.Image, cx: int, cy: int, rx: int, ry: int, color: tuple, intensity: float):
    """Draws a soft, dynamic radial glow."""
    if intensity <= 0.01:
        return
    # Fast overlay using low-res blur
    glow_size = (320, 180)
    glow_img = Image.new("RGBA", glow_size, (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow_img)
    gcx = int(cx * 320 / WIDTH)
    gcy = int(cy * 180 / HEIGHT)
    grx = int(rx * 320 / WIDTH)
    gry = int(ry * 180 / HEIGHT)
    
    alpha = int(min(255, 255 * intensity))
    g_draw.ellipse([gcx - grx, gcy - gry, gcx + grx, gcy + gry], fill=(color[0], color[1], color[2], alpha))
    glow_img = glow_img.filter(ImageFilter.GaussianBlur(radius=28))
    glow_full = glow_img.resize((WIDTH, HEIGHT), Image.Resampling.BILINEAR)
    img.paste(glow_full, (0, 0), glow_full)


def render_scene_1(frame_idx: int) -> Image.Image:
    """Scene 1: The Fragile Reality (0.0s – 7.0s | Frames 0 to 210)"""
    sec = frame_idx / FPS
    img = Image.new("RGBA", (WIDTH, HEIGHT), (3, 6, 12, 255))
    draw = ImageDraw.Draw(img)

    # Subtle ambient breathing particle light
    aura_pulse = 0.20 + 0.10 * math.sin(sec * 1.5)
    draw_radial_aura(img, WIDTH // 2, HEIGHT // 2, 600, 400, (37, 99, 235), aura_pulse)

    # Floating abstract document stack silhouette
    doc_y = int(580 - ease_out_cubic(min(1.0, sec / 3.0)) * 20)
    for i, offset in enumerate([( -12, 16 ), ( 10, 8 ), ( 0, 0 )]):
        ox, oy = offset
        alpha = 30 + i * 25
        card_rect = [WIDTH // 2 - 200 + ox, doc_y - 120 + oy, WIDTH // 2 + 200 + ox, doc_y + 160 + oy]
        draw.rounded_rectangle(card_rect, radius=12, fill=(18, 24, 38, alpha), outline=(50, 65, 95, alpha + 30), width=1)
        # simulated lines of text in the document
        for line_y in range(card_rect[1] + 28, card_rect[3] - 20, 18):
            draw.line([(card_rect[0] + 30, line_y), (card_rect[2] - 30, line_y)], fill=(70, 85, 120, alpha // 2), width=3)

    # Typography Phase 1 (0s to 3.4s)
    if sec < 3.8:
        t_fade = ease_out_cubic(smoothstep(0.4, 1.8, sec))
        if sec > 3.0:
            t_fade *= (1.0 - ease_out_cubic(smoothstep(3.0, 3.8, sec)))
        c_val = int(255 * t_fade)
        if c_val > 5:
            draw.text((WIDTH // 2, 320), "Every day, critical decisions", font=FONT_TITLE_LG, fill=(c_val, c_val, c_val), anchor="mm")
            c_sub = int(180 * t_fade)
            draw.text((WIDTH // 2, 400), "rely on complex documents.", font=FONT_TITLE_MD, fill=(c_sub, c_sub, c_sub), anchor="mm")
    else:
        # Typography Phase 2 (3.8s to 7.0s)
        t_fade = ease_out_cubic(smoothstep(3.8, 4.8, sec))
        if sec > 6.4:
            t_fade *= (1.0 - ease_out_cubic(smoothstep(6.4, 7.0, sec)))
        c_val = int(255 * t_fade)
        if c_val > 5:
            draw.text((WIDTH // 2, 320), "And increasingly...", font=FONT_TITLE_MD, fill=(int(180 * t_fade), int(190 * t_fade), int(210 * t_fade)), anchor="mm")
            draw.text((WIDTH // 2, 400), "on AI.", font=FONT_TITLE_HERO, fill=(c_val, c_val, c_val), anchor="mm")

    return img.convert("RGB")


def render_scene_2(frame_idx: int) -> Image.Image:
    """Scene 2: The Fatal Flaw (7.0s – 14.0s | Frames 210 to 420)"""
    sec = (frame_idx - 210) / FPS
    img = Image.new("RGBA", (WIDTH, HEIGHT), (6, 4, 8, 255))
    draw = ImageDraw.Draw(img)

    # Warning amber / crimson pulse
    pulse = 0.25 + 0.15 * math.sin(sec * 4.0)
    draw_radial_aura(img, WIDTH // 2, 400, 700, 450, (220, 38, 38), pulse)

    # Title
    t_in = smoothstep(0.0, 1.0, sec)
    t_out = 1.0 - smoothstep(6.2, 7.0, sec)
    alpha_master = ease_out_cubic(t_in) * t_out

    c_title = int(255 * alpha_master)
    draw.text((WIDTH // 2, 140), "Conventional AI has a flaw.", font=FONT_TITLE_LG, fill=(c_title, c_title, c_title), anchor="mm")
    draw.text((WIDTH // 2, 210), "When context gets severed, it hallucinates. It guesses.", font=FONT_SUBTITLE, fill=(int(248 * alpha_master), int(113 * alpha_master), int(113 * alpha_master)), anchor="mm")

    # 4 Traps cards in a grid
    traps = [
        ("P1: Boundary Straddle", "Clauses cut across arbitrary 500-token chunks.", "Blanket rule cited without condition."),
        ("P2: Distractor Clauses", "Cosine similarity tricked by superficial keywords.", "Irrelevant jurisdiction retrieved."),
        ("P3: Two-Hop References", "Rule cited pursuant to another schedule.", "Crucial cross-referenced definition lost."),
        ("P4: Multi-Aspect Queries", "Complex questions span multiple provisions.", "Partial retrieval yields misleading answers.")
    ]

    card_w, card_h = 420, 220
    coords = [
        (WIDTH // 2 - card_w - 20, 290),
        (WIDTH // 2 + 20, 290),
        (WIDTH // 2 - card_w - 20, 540),
        (WIDTH // 2 + 20, 540),
    ]

    for i, (title, d1, d2) in enumerate(traps):
        entry_t = 1.2 + i * 0.4
        card_alpha = smoothstep(entry_t, entry_t + 0.5, sec) * t_out
        if card_alpha <= 0.02:
            continue
        cx, cy = coords[i]
        slide = (1.0 - ease_out_cubic(card_alpha)) * 25
        cy = int(cy + slide)
        
        # Draw glass warning card
        fill_a = int(35 * card_alpha)
        border_a = int(120 * card_alpha)
        draw.rounded_rectangle([cx, cy, cx + card_w, cy + card_h], radius=16, fill=(28, 18, 24, fill_a), outline=(239, 68, 68, border_a), width=2)

        # Danger pill
        draw.rounded_rectangle([cx + 20, cy + 20, cx + 180, cy + 50], radius=6, fill=(239, 68, 68, int(40 * card_alpha)))
        draw.text((cx + 100, cy + 35), "RAG FAILURE TRAP", font=FONT_MONO_XS, fill=(252, 165, 165, int(220 * card_alpha)), anchor="mm")

        # Texts
        draw.text((cx + 20, cy + 70), title, font=FONT_BODY_BOLD, fill=(255, 255, 255, int(240 * card_alpha)))
        draw.text((cx + 20, cy + 115), d1, font=FONT_CAPTION, fill=(209, 213, 219, int(200 * card_alpha)))
        draw.text((cx + 20, cy + 145), d2, font=FONT_CAPTION, fill=(248, 113, 113, int(210 * card_alpha)))

    # Banner stat at bottom (after 3.5s)
    if sec > 3.6:
        b_alpha = smoothstep(3.6, 4.4, sec) * t_out
        by = int(820 + (1.0 - ease_out_cubic(b_alpha)) * 30)
        draw.rounded_rectangle([WIDTH // 2 - 400, by, WIDTH // 2 + 400, by + 80], radius=40, fill=(30, 10, 15, int(180 * b_alpha)), outline=(239, 68, 68, int(160 * b_alpha)), width=2)
        draw.text((WIDTH // 2, by + 40), "NAIVE RETRIEVAL ACCURACY: ONLY 55% – 65%", font=FONT_MONO_SM, fill=(254, 202, 202, int(255 * b_alpha)), anchor="mm")

    return img.convert("RGB")


def render_scene_3(frame_idx: int) -> Image.Image:
    """Scene 3: The Reveal: Introducing Allcited (14.0s – 19.5s | Frames 420 to 585)"""
    sec = (frame_idx - 420) / FPS
    img = Image.new("RGBA", (WIDTH, HEIGHT), (2, 4, 10, 255))
    draw = ImageDraw.Draw(img)

    # Apple Intelligence chromatic radial bloom
    aura_intensity = min(1.0, sec * 0.8)
    draw_radial_aura(img, WIDTH // 2, 520, 800, 500, (99, 102, 241), 0.40 * aura_intensity)
    draw_radial_aura(img, WIDTH // 2, 500, 500, 300, (6, 182, 212), 0.35 * aura_intensity)
    draw_radial_aura(img, WIDTH // 2, 480, 300, 180, (236, 72, 153), 0.20 * aura_intensity)

    t_in = smoothstep(0.0, 1.2, sec)
    t_out = 1.0 - smoothstep(4.8, 5.5, sec)
    alpha = ease_out_cubic(t_in) * t_out

    # Pre-headline
    c_sub = int(180 * alpha)
    draw.text((WIDTH // 2, 280), "A NEW STANDARD FOR CERTAINTY", font=FONT_MONO_SM, fill=(147, 197, 253, c_sub), anchor="mm")

    # Hero Wordmark
    c_hero = int(255 * alpha)
    draw.text((WIDTH // 2, 380), "Allcited", font=FONT_TITLE_HERO, fill=(c_hero, c_hero, c_hero), anchor="mm")

    # Tagline
    draw.text((WIDTH // 2, 470), "Document Q&A with Receipts. No Hallucinations.", font=FONT_TITLE_MD, fill=(224, 231, 255, int(230 * alpha)), anchor="mm")

    # Floating Titanium Glass Pill
    pill_w, pill_h = 680, 72
    pill_x = WIDTH // 2 - pill_w // 2
    pill_y = int(560 + (1.0 - ease_out_cubic(smoothstep(0.6, 1.8, sec))) * 40)
    pill_a = smoothstep(0.6, 1.8, sec) * t_out

    draw.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + pill_h], radius=36, fill=(15, 23, 42, int(160 * pill_a)), outline=(56, 189, 248, int(180 * pill_a)), width=2)
    
    # Pill content: Emerald check + Citation chip
    draw.ellipse([pill_x + 30, pill_y + 24, pill_x + 54, pill_y + 48], fill=(16, 185, 129, int(220 * pill_a)))
    draw.line([(pill_x + 36, pill_y + 36), (pill_x + 41, pill_y + 42), (pill_x + 48, pill_y + 30)], fill=(255, 255, 255, int(255 * pill_a)), width=2)
    draw.text((pill_x + 70, pill_y + 36), "100% VERIFIED RECEIPT", font=FONT_MONO_SM, fill=(240, 253, 250, int(240 * pill_a)), anchor="lm")
    
    # Chip [S1]
    chip_x = pill_x + 380
    draw.rounded_rectangle([chip_x, pill_y + 18, chip_x + 270, pill_y + 54], radius=6, fill=(30, 58, 138, int(200 * pill_a)), outline=(96, 165, 250, int(220 * pill_a)), width=1)
    draw.text((chip_x + 135, pill_y + 36), "[S1] Page 42 · Paragraph 3", font=FONT_MONO_XS, fill=(191, 219, 254, int(240 * pill_a)), anchor="mm")

    # Triple feature icons
    feats = ["Zero Cloud Egress", "95.1% Retrieval Accuracy", "Sub-1.1ms Re-Ranking"]
    fx_start = WIDTH // 2 - 420
    for i, f in enumerate(feats):
        fx = fx_start + i * 290
        fa = smoothstep(1.5 + i * 0.3, 2.3 + i * 0.3, sec) * t_out
        draw.text((fx + 120, 690), f"• {f}", font=FONT_CAPTION, fill=(148, 163, 184, int(200 * fa)), anchor="mm")

    return img.convert("RGB")


def render_scene_4(frame_idx: int) -> Image.Image:
    """Scene 4: The 4 Breakthrough Pillars (19.5s – 31.0s | Frames 585 to 930)"""
    sec = (frame_idx - 585) / FPS
    img = Image.new("RGBA", (WIDTH, HEIGHT), (4, 8, 16, 255))
    draw = ImageDraw.Draw(img)

    t_in = smoothstep(0.0, 1.0, sec)
    t_out = 1.0 - smoothstep(10.5, 11.5, sec)
    alpha = ease_out_cubic(t_in) * t_out

    # Chromatic background
    draw_radial_aura(img, WIDTH // 2, 450, 750, 450, (30, 58, 138), 0.30)

    # Category badge
    draw.rounded_rectangle([WIDTH // 2 - 190, 80, WIDTH // 2 + 190, 116], radius=18, fill=(30, 41, 59, int(180 * alpha)), outline=(99, 102, 241, int(150 * alpha)))
    draw.text((WIDTH // 2, 98), "FOUR FOUNDATIONAL PILLARS", font=FONT_MONO_XS, fill=(165, 180, 252, int(240 * alpha)), anchor="mm")

    draw.text((WIDTH // 2, 160), "Engineered to Solve the RAG Traps.", font=FONT_TITLE_LG, fill=(255, 255, 255, int(255 * alpha)), anchor="mm")

    # 4 Pillars cards layout
    pillars = [
        (
            "P1: Section Breadcrumbs",
            "Hierarchical context injection",
            "Doc > Section > Clause",
            "Sliding-window overlap ensures critical conditions never get severed by arbitrary chunk boundaries.",
            (56, 189, 248)
        ),
        (
            "P2: Cross-Encoder Re-Ranking",
            "Full token-level interaction",
            "ms-marco-MiniLM-L-6-v2",
            "Evaluates full query-passage attention to filter distractor clauses with calibrated score thresholds.",
            (168, 85, 247)
        ),
        (
            "P3: Graph Reference Expansion",
            "Multi-hop definition resolution",
            "Target Schedule Definition Link",
            "Automatically identifies cross-referenced rules at ingestion, attaching secondary context definitions.",
            (52, 211, 153)
        ),
        (
            "P4: Agentic Sufficiency Loop",
            "Dynamic query decomposition",
            "Bounded Multi-Pass (<= 3 passes)",
            "Splits multi-aspect questions into atomic sub-queries until the answer is mathematically complete.",
            (251, 191, 36)
        )
    ]

    card_w = 400
    card_h = 440
    gap = 25
    total_w = 4 * card_w + 3 * gap
    start_x = (WIDTH - total_w) // 2

    # Active highlight cycles over time:
    # 0.0 - 2.8: P1
    # 2.8 - 5.5: P2
    # 5.5 - 8.2: P3
    # 8.2 - 11.5: P4
    active_idx = min(3, int(sec / 2.8))

    for i, (title, sub, badge, desc, accent) in enumerate(pillars):
        cx = start_x + i * (card_w + gap)
        entry_t = 0.5 + i * 0.3
        card_a = smoothstep(entry_t, entry_t + 0.6, sec) * t_out
        if card_a <= 0.02:
            continue
        
        is_active = (i == active_idx)
        scale_offset = -15 if is_active else 0
        cy = int(230 + (1.0 - ease_out_cubic(card_a)) * 40 + scale_offset)

        border_col = accent if is_active else (51, 65, 85)
        border_w = 2 if is_active else 1
        fill_col = (20, 30, 48, int(180 * card_a)) if is_active else (15, 23, 38, int(130 * card_a))

        draw.rounded_rectangle([cx, cy, cx + card_w, cy + card_h], radius=18, fill=fill_col, outline=border_col, width=border_w)

        # Active indicator top bar
        if is_active:
            draw.rounded_rectangle([cx + 20, cy + 2, cx + card_w - 20, cy + 6], radius=2, fill=accent)

        # Pill badge
        draw.rounded_rectangle([cx + 24, cy + 28, cx + card_w - 24, cy + 64], radius=6, fill=(30, 41, 59, int(180 * card_a)), outline=border_col)
        draw.text((cx + card_w // 2, cy + 46), badge, font=FONT_MONO_XS, fill=accent, anchor="mm")

        # Titles
        draw.text((cx + 24, cy + 95), title, font=FONT_BODY_BOLD, fill=(255, 255, 255, int(250 * card_a)))
        draw.text((cx + 24, cy + 130), sub, font=FONT_CAPTION, fill=(148, 163, 184, int(200 * card_a)))

        # Separator line
        draw.line([(cx + 24, cy + 165), (cx + card_w - 24, cy + 165)], fill=(51, 65, 85, int(150 * card_a)), width=1)

        # Description text
        # Simple word wrap
        words = desc.split()
        lines = []
        cur_line = []
        for w in words:
            cur_line.append(w)
            if len(" ".join(cur_line)) > 30:
                lines.append(" ".join(cur_line))
                cur_line = []
        if cur_line:
            lines.append(" ".join(cur_line))

        for li, line in enumerate(lines[:6]):
            draw.text((cx + 24, cy + 185 + li * 26), line, font=FONT_CAPTION, fill=(203, 213, 225, int(210 * card_a)))

    return img.convert("RGB")


def render_scene_5(frame_idx: int) -> Image.Image:
    """Scene 5: Grounded Precision & Live UI (31.0s – 40.5s | Frames 930 to 1215)"""
    sec = (frame_idx - 930) / FPS
    img = Image.new("RGBA", (WIDTH, HEIGHT), (3, 7, 18, 255))
    draw = ImageDraw.Draw(img)

    t_in = smoothstep(0.0, 1.0, sec)
    t_out = 1.0 - smoothstep(8.5, 9.5, sec)
    alpha = ease_out_cubic(t_in) * t_out

    draw_radial_aura(img, WIDTH // 2, 500, 800, 500, (30, 64, 175), 0.35)

    # Title
    draw.text((WIDTH // 2, 80), "Every Answer Grounded with Receipts.", font=FONT_TITLE_MD, fill=(255, 255, 255, int(255 * alpha)), anchor="mm")
    draw.text((WIDTH // 2, 125), "Verified down to the exact page, paragraph, and cell.", font=FONT_BODY, fill=(148, 163, 184, int(220 * alpha)), anchor="mm")

    # The macOS / Apple Glass Application Window
    win_w, win_h = 1380, 620
    win_x = (WIDTH - win_w) // 2
    win_y = 170

    # Window container
    draw.rounded_rectangle([win_x, win_y, win_x + win_w, win_y + win_h], radius=16, fill=(15, 23, 42, int(240 * alpha)), outline=(51, 65, 85, int(200 * alpha)), width=2)

    # Window header bar
    draw.rounded_rectangle([win_x, win_y, win_x + win_w, win_y + 50], radius=16, fill=(30, 41, 59, int(200 * alpha)))
    draw.rectangle([win_x, win_y + 35, win_x + win_w, win_y + 50], fill=(30, 41, 59, int(200 * alpha)))
    draw.line([(win_x, win_y + 50), (win_x + win_w, win_y + 50)], fill=(51, 65, 85, int(180 * alpha)), width=1)

    # Traffic lights
    draw.ellipse([win_x + 20, win_y + 18, win_x + 34, win_y + 32], fill=(239, 68, 68))
    draw.ellipse([win_x + 42, win_y + 18, win_x + 56, win_y + 32], fill=(245, 158, 11))
    draw.ellipse([win_x + 64, win_y + 18, win_x + 78, win_y + 32], fill=(16, 185, 129))

    draw.text((win_x + win_w // 2, win_y + 25), "Allcited · Global_MSA_2026.pdf · 95.1% Retrieval Verified", font=FONT_CAPTION, fill=(148, 163, 184), anchor="mm")

    # Main Left Panel (Q&A Workspace)
    drawer_progress = ease_out_cubic(smoothstep(2.4, 3.6, sec))  # Receipts Drawer slides out at 2.4s
    drawer_w = 460
    left_w = win_w - int(drawer_w * drawer_progress)

    # Question Box
    draw.rounded_rectangle([win_x + 35, win_y + 75, win_x + left_w - 35, win_y + 145], radius=10, fill=(24, 33, 52), outline=(59, 130, 246), width=1)
    
    # Typing question
    full_q = "What is the liability cap under Section 11.2, and are there carve-outs?"
    char_count = int(min(len(full_q), sec * 35))
    disp_q = full_q[:char_count] + ("|" if (int(sec * 4) % 2 == 0 and char_count < len(full_q)) else "")
    draw.text((win_x + 55, win_y + 110), f"Q: {disp_q}", font=FONT_BODY_BOLD, fill=(255, 255, 255), anchor="lm")

    # Streaming Answer Box
    if sec > 1.2:
        draw.rounded_rectangle([win_x + 35, win_y + 170, win_x + left_w - 35, win_y + 440], radius=12, fill=(18, 27, 43), outline=(51, 65, 85), width=1)
        draw.text((win_x + 60, win_y + 205), "Allcited Answer (Grounded Retrieval Engine):", font=FONT_CAPTION, fill=(148, 163, 184))

        # Answer text with interactive citation chips
        a_line1 = "Under Section 11.2, aggregate liability is strictly capped at two times (2x)"
        draw.text((win_x + 60, win_y + 245), a_line1, font=FONT_BODY, fill=(243, 244, 246))

        # Chip [S1]
        chip_active = (sec > 2.4)
        chip_col = (56, 189, 248) if chip_active else (96, 165, 250)
        draw.rounded_rectangle([win_x + 60, win_y + 280, win_x + 230, win_y + 315], radius=6, fill=(30, 58, 138), outline=chip_col, width=2 if chip_active else 1)
        draw.text((win_x + 145, win_y + 297), "[S1] p.24 § 11.2", font=FONT_MONO_SM, fill=(255, 255, 255), anchor="mm")

        a_line2 = "fees paid. However, indemnification obligations for IP infringement"
        draw.text((win_x + 245, win_y + 297), a_line2, font=FONT_BODY, fill=(243, 244, 246), anchor="lm")

        a_line3 = "are expressly excluded from this limitation pursuant to Schedule B."
        draw.text((win_x + 60, win_y + 345), a_line3, font=FONT_BODY, fill=(243, 244, 246))

        # Chip [S2 (2nd-hop)]
        draw.rounded_rectangle([win_x + 60, win_y + 375, win_x + 290, win_y + 410], radius=6, fill=(19, 78, 74), outline=(45, 212, 191), width=1)
        draw.text((win_x + 175, win_y + 392), "[S2 (2nd-hop)] Sched. B", font=FONT_MONO_SM, fill=(204, 251, 241), anchor="mm")

    # Sliding Receipts Drawer (from right edge)
    if drawer_progress > 0.01:
        dr_x = win_x + win_w - int(drawer_w * drawer_progress)
        draw.rounded_rectangle([dr_x, win_y + 51, win_x + win_w, win_y + win_h], radius=0, fill=(10, 15, 28, 255), outline=(56, 189, 248), width=2)

        # Drawer header
        draw.rounded_rectangle([dr_x + 20, win_y + 70, dr_x + drawer_w - 20, win_y + 110], radius=6, fill=(16, 185, 129, 40), outline=(16, 185, 129))
        draw.text((dr_x + 40, win_y + 90), "RECEIPT [S1] · VERIFIED GROUNDING", font=FONT_MONO_XS, fill=(52, 211, 153), anchor="lm")

        draw.text((dr_x + 24, win_y + 135), "Source Document Location:", font=FONT_CAPTION, fill=(148, 163, 184))
        draw.text((dr_x + 24, win_y + 160), "Master Agreement > Article XI > § 11.2", font=FONT_MONO_XS, fill=(56, 189, 248))
        draw.text((dr_x + 24, win_y + 185), "Page 24 · Paragraph 4 · Cell Match", font=FONT_MONO_XS, fill=(203, 213, 225))

        # Exact Quote Card with gold highlight
        draw.rounded_rectangle([dr_x + 20, win_y + 225, dr_x + drawer_w - 20, win_y + 480], radius=8, fill=(20, 27, 45), outline=(51, 65, 85))
        draw.text((dr_x + 35, win_y + 250), "Exact Source Text:", font=FONT_CAPTION, fill=(156, 163, 175))

        quote_lines = [
            "\"Neither party's aggregate liability",
            "arising out of or related to this",
            "Agreement shall exceed two times (2x)",
            "the total fees paid in the twelve (12)",
            "months preceding the incident...\""
        ]
        for qli, ql in enumerate(quote_lines):
            # Highlight 2x
            draw.text((dr_x + 35, win_y + 290 + qli * 32), ql, font=FONT_BODY, fill=(254, 240, 138) if qli == 2 else (226, 232, 240))

        # 1-Click Verification Link
        draw.rounded_rectangle([dr_x + 20, win_y + 510, dr_x + drawer_w - 20, win_y + 560], radius=8, fill=(37, 99, 235), outline=(96, 165, 250))
        draw.text((dr_x + drawer_w // 2, win_y + 535), "Open Page 24 in Document Viewer ->", font=FONT_BODY_BOLD, fill=(255, 255, 255), anchor="mm")

    # Triple Stats Bar at window footer
    draw.line([(win_x, win_y + 530), (win_x + left_w, win_y + 530)], fill=(51, 65, 85), width=1)
    stats = [
        ("95.1%", "Retrieval Accuracy"),
        ("0 Egress", "Air-Gapped Private Edition"),
        ("< 1.1ms", "p95 Re-Ranking Latency")
    ]
    for si, (num, lbl) in enumerate(stats):
        sx = win_x + 60 + si * 260
        draw.text((sx, win_y + 555), num, font=FONT_BODY_BOLD, fill=(56, 189, 248))
        draw.text((sx, win_y + 585), lbl, font=FONT_CAPTION, fill=(148, 163, 184))

    return img.convert("RGB")


def render_scene_6(frame_idx: int) -> Image.Image:
    """Scene 6: Apple Signature Finale (40.5s – 46.0s | Frames 1215 to 1380)"""
    sec = (frame_idx - 1215) / FPS
    img = Image.new("RGBA", (WIDTH, HEIGHT), (2, 3, 6, 255))
    draw = ImageDraw.Draw(img)

    t_in = smoothstep(0.0, 1.2, sec)
    t_out = 1.0 - smoothstep(4.5, 5.5, sec)
    alpha = ease_out_cubic(t_in) * t_out

    # Gentle ambient breathing aura
    draw_radial_aura(img, WIDTH // 2, 450, 600, 350, (59, 130, 246), 0.25 * alpha)

    # Wordmark
    c_mark = int(255 * alpha)
    draw.text((WIDTH // 2, 380), "Allcited", font=FONT_TITLE_HERO, fill=(c_mark, c_mark, c_mark), anchor="mm")

    # Tagline
    draw.text((WIDTH // 2, 480), "Trust, verified.", font=FONT_TITLE_MD, fill=(224, 231, 255, int(230 * alpha)), anchor="mm")

    # Domain CTA
    draw.rounded_rectangle([WIDTH // 2 - 200, 570, WIDTH // 2 + 200, 630], radius=30, fill=(30, 41, 59, int(180 * alpha)), outline=(56, 189, 248, int(200 * alpha)), width=2)
    draw.text((WIDTH // 2, 600), "allcited.vercel.app", font=FONT_MONO_MD, fill=(147, 197, 253, int(255 * alpha)), anchor="mm")

    # Footer note
    draw.text((WIDTH // 2, 700), "Open Source • Air-Gapped Private Edition • MIT Licensed", font=FONT_CAPTION, fill=(100, 116, 139, int(180 * alpha)), anchor="mm")

    return img.convert("RGB")


def render_frame(frame_idx: int) -> Image.Image:
    """Dispatches frame index to corresponding scene."""
    if frame_idx < 210:
        return render_scene_1(frame_idx)
    elif frame_idx < 420:
        return render_scene_2(frame_idx)
    elif frame_idx < 585:
        return render_scene_3(frame_idx)
    elif frame_idx < 930:
        return render_scene_4(frame_idx)
    elif frame_idx < 1215:
        return render_scene_5(frame_idx)
    else:
        return render_scene_6(frame_idx)


def compile_video():
    """Generates audio and renders 1380 frames directly into ffmpeg."""
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
        100: "scene1_document_reality.png",
        320: "scene2_rag_failure_traps.png",
        490: "scene3_introducing_allcited.png",
        720: "scene4_four_breakthrough_pillars.png",
        1080: "scene5_live_receipts_ui.png",
        1290: "scene6_apple_signature_finale.png"
    }

    stills_dir = ASSETS_DIR / "promo_stills"
    stills_dir.mkdir(parents=True, exist_ok=True)

    for i in range(TOTAL_FRAMES):
        frame = render_frame(i)
        
        # Save keyframe still
        if i in key_stills:
            frame.save(stills_dir / key_stills[i])

        # Write raw bytes to ffmpeg
        proc.stdin.write(frame.tobytes())

        if i % 150 == 0 or i == TOTAL_FRAMES - 1:
            print(f"Render progress: frame {i}/{TOTAL_FRAMES} ({(i/TOTAL_FRAMES)*100:.1f}%)")

    proc.stdin.close()
    proc.wait()

    if proc.returncode != 0:
        print("FFmpeg error during compilation")
        sys.exit(1)

    print(f"Video created successfully! Output: {OUTPUT_VIDEO}")
    file_size_mb = OUTPUT_VIDEO.stat().st_size / (1024 * 1024)
    print(f"Output file size: {file_size_mb:.2f} MB")


if __name__ == "__main__":
    compile_video()
