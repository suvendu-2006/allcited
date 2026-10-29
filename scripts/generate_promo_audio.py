#!/usr/bin/env python3
"""
Generate the §7.4 conforming sound design for the Allcited Apple promo film.
Exact 4 sound elements, zero voiceover, zero music beds.
Duration: exactly 25.0s @ 48kHz stereo, normalized to -16 LUFS (-6 dB true peak).
"""

import math
import numpy as np
import wave
import subprocess
from pathlib import Path

SAMPLE_RATE = 48000
DURATION = 25.0
NUM_SAMPLES = int(SAMPLE_RATE * DURATION)

def generate_sub_bass_swell(duration=1.5, sr=48000):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # Sine swell starting at 42 Hz rising to 58 Hz
    freq = 42.0 + 16.0 * (t / duration)
    phase = 2 * np.pi * np.cumsum(freq) / sr
    # Swell envelope: smooth rise, peak around 0.6s, gentle decay
    env = np.sin(np.pi * (t / duration)) ** 1.8
    tone = np.sin(phase) * env
    # Level at -24 dBFS (amplitude approx 0.063)
    tone = tone * 0.063
    return tone

def generate_soft_tick(duration=0.03, sr=48000):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # Crisp high-frequency transient click
    tone = np.sin(2 * np.pi * 2400.0 * t) * np.exp(-t * 220.0)
    # Level at -30 dBFS (amplitude approx 0.0316)
    tone = tone * 0.0316
    return tone

def generate_whoosh(duration=0.35, sr=48000):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # Airy swept filtered noise + smooth sine undertone
    np.random.seed(42)
    noise = np.random.normal(0, 1, len(t))
    # Soft bell envelope
    env = np.sin(np.pi * (t / duration)) ** 2.0
    # Swept tone 350Hz -> 850Hz -> 200Hz
    freq = 350.0 + 500.0 * np.sin(np.pi * (t / duration))
    phase = 2 * np.pi * np.cumsum(freq) / sr
    sweep = np.sin(phase) * 0.5 + noise * 0.5
    whoosh = sweep * env
    # Level at -26 dBFS (amplitude approx 0.05)
    whoosh = whoosh * 0.05
    return whoosh

def generate_warm_pad(duration=2.5, sr=48000):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # Warm C major 9th chord: C3 (130.81), G3 (196.00), B3 (246.94), D4 (293.66), E4 (329.63)
    freqs = [130.81, 196.00, 246.94, 293.66, 329.63]
    chord_l = np.zeros_like(t)
    chord_r = np.zeros_like(t)
    
    # Envelope: gentle attack 0.4s, hold, fade out to 2.5s
    attack_samples = int(0.4 * sr)
    decay_samples = int(1.2 * sr)
    env = np.ones_like(t)
    env[:attack_samples] = np.sin(np.linspace(0, np.pi/2, attack_samples)) ** 2
    env[-decay_samples:] = np.cos(np.linspace(0, np.pi/2, decay_samples)) ** 2
    
    for i, f in enumerate(freqs):
        # Subtle analog stereo detuning
        detune = 0.35 * (1 if i % 2 == 0 else -1)
        chord_l += np.sin(2 * np.pi * (f - detune) * t) * (1.0 / len(freqs))
        chord_r += np.sin(2 * np.pi * (f + detune) * t) * (1.0 / len(freqs))
        
    # Level at -22 dBFS (amplitude approx 0.079)
    chord_l = chord_l * env * 0.079
    chord_r = chord_r * env * 0.079
    return chord_l, chord_r

def main():
    out_dir = Path("assets/promo")
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_audio_path = out_dir / "promo_audio_raw.wav"
    master_audio_path = out_dir / "promo_audio_master.wav"
    
    left = np.zeros(NUM_SAMPLES, dtype=np.float32)
    right = np.zeros(NUM_SAMPLES, dtype=np.float32)
    
    # 1. Low sub-bass swell @ 0.0s
    swell = generate_sub_bass_swell(1.5, SAMPLE_RATE)
    idx_0 = 0
    left[idx_0:idx_0+len(swell)] += swell
    right[idx_0:idx_0+len(swell)] += swell
    
    # 2. Soft tick cues @ 0.4s, 2.6s, 6.0s, 7.2s, 10.8s, 18.2s
    tick_times = [0.4, 2.6, 6.0, 7.2, 10.8, 18.2]
    tick = generate_soft_tick(0.03, SAMPLE_RATE)
    for t_cue in tick_times:
        idx = int(t_cue * SAMPLE_RATE)
        left[idx:idx+len(tick)] += tick
        right[idx:idx+len(tick)] += tick
        
    # 3. Gentle whoosh @ 16.6s
    whoosh = generate_whoosh(0.35, SAMPLE_RATE)
    idx_w = int(16.6 * SAMPLE_RATE)
    left[idx_w:idx_w+len(whoosh)] += whoosh
    right[idx_w:idx_w+len(whoosh)] += whoosh
    
    # 4. Warm major-resolve pad @ 21.2s (duration 2.5s)
    pad_l, pad_r = generate_warm_pad(2.5, SAMPLE_RATE)
    idx_p = int(21.2 * SAMPLE_RATE)
    left[idx_p:idx_p+len(pad_l)] += pad_l
    right[idx_p:idx_p+len(pad_r)] += pad_r
    
    # Write raw 32-bit float or 16-bit PCM wav
    # Scale to 16-bit int
    max_val = max(np.max(np.abs(left)), np.max(np.abs(right)), 1e-6)
    left_16 = np.clip(left * 32767, -32768, 32767).astype(np.int16)
    right_16 = np.clip(right * 32767, -32768, 32767).astype(np.int16)
    
    stereo_interleaved = np.empty((NUM_SAMPLES * 2,), dtype=np.int16)
    stereo_interleaved[0::2] = left_16
    stereo_interleaved[1::2] = right_16
    
    with wave.open(str(raw_audio_path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(stereo_interleaved.tobytes())
        
    print(f"Generated raw audio: {raw_audio_path}")
    
    # Conform to -16 LUFS master target (-6 dB TP) using ffmpeg loudnorm
    # Note: Because the piece is mostly silence and subtle cues, standard two-pass loudnorm can elevate noise floor;
    # we calibrate the level so peak is -6 dBFS and integrated loudness is at -16 LUFS.
    cmd = [
        "ffmpeg", "-y",
        "-i", str(raw_audio_path),
        "-af", "loudnorm=I=-16:TP=-6:LRA=11",
        "-ar", "48000",
        str(master_audio_path)
    ]
    subprocess.run(cmd, check=True)
    print(f"Conformed audio master generated: {master_audio_path}")

if __name__ == "__main__":
    main()
