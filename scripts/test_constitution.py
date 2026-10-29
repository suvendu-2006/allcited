#!/usr/bin/env python3
"""
Test script to verify Apple motion constitution, cubic bezier lookup,
font rendering, and caption blur-in.
"""

import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pathlib import Path

# Precompute Apple cubic-bezier(0.16, 1, 0.3, 1) lookup table
def build_bezier_lut(p1x=0.16, p1y=1.0, p2x=0.3, p2y=1.0, n_points=2000):
    lut_s = np.linspace(0.0, 1.0, n_points)
    # x(s) and y(s)
    # B(s) = (1-s)^3 * 0 + 3(1-s)^2*s * P1 + 3(1-s)*s^2 * P2 + s^3 * 1
    lut_x = 3 * (1 - lut_s)**2 * lut_s * p1x + 3 * (1 - lut_s) * lut_s**2 * p2x + lut_s**3
    lut_y = 3 * (1 - lut_s)**2 * lut_s * p1y + 3 * (1 - lut_s) * lut_s**2 * p2y + lut_s**3
    
    # Create uniform x grid from 0 to 1
    grid_x = np.linspace(0.0, 1.0, 1001)
    grid_y = np.interp(grid_x, lut_x, lut_y)
    return grid_y

BEZIER_LUT = build_bezier_lut()

def ease_apple(t: float) -> float:
    t = max(0.0, min(1.0, float(t)))
    idx = int(t * 1000)
    return float(BEZIER_LUT[idx])

# Verify fonts
FONT_INTER_PATH = "assets/fonts/Inter.ttf"
FONT_MONO_PATH = "assets/fonts/JetBrainsMono.ttf"

def render_caption_reveal_test():
    img = Image.new("RGBA", (1920, 1080), (0, 0, 0, 255))
    font = ImageFont.truetype(FONT_INTER_PATH, 56)
    
    words = ["The", "answer", "is", "on", "page", "23."]
    # Render with blur-in at t=0.5
    # word 0 at t=0.7 (ease=1.0), word 5 at t=0.2 (ease ~0.6)
    test_layer = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    
    cur_x = 100
    y_base = 400
    for i, w in enumerate(words):
        # simulate progress
        w_progress = max(0.0, min(1.0, 1.0 - i * 0.15))
        ease = ease_apple(w_progress)
        blur_r = 14.0 * (1.0 - ease)
        dy = 24.0 * (1.0 - ease)
        alpha = int(ease * 0.92 * 255)
        
        # Word surface
        w_box = font.getbbox(w)
        w_width = w_box[2] - w_box[0]
        w_height = w_box[3] - w_box[1]
        
        pad = 20
        word_img = Image.new("RGBA", (w_width + pad*2, w_height + pad*2), (0, 0, 0, 0))
        wd = ImageDraw.Draw(word_img)
        wd.text((pad - w_box[0], pad - w_box[1]), w, font=font, fill=(242, 239, 224, alpha))
        
        if blur_r > 0.5:
            word_img = word_img.filter(ImageFilter.GaussianBlur(blur_r))
            
        test_layer.alpha_composite(word_img, (int(cur_x - pad), int(y_base + dy - pad)))
        cur_x += w_width + 18
        
    img.alpha_composite(test_layer)
    out_path = Path("/tmp/test_caption.png")
    img.save(out_path)
    print("Test caption saved to", out_path)

if __name__ == "__main__":
    render_caption_reveal_test()
