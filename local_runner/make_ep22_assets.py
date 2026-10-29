"""
Draw the ep22 ("The Sun is not yellow") graphics in code, no GPU and no image model.

Writes to i2v_stills/sci_ep22_sun_white/ (git-ignored). The real photos (sun_iss.jpg,
astronaut.jpg, earth_limb.jpg) come from fetch_still_assets.py; everything else is here.

  python make_ep22_assets.py

crayon_sun.png      a child's crayon drawing of a yellow sun on paper (9:16 background)
white_beam.png      soft white sunbeam (RGBA layer)
spectrum.png        a smooth rainbow arc, red outside, violet inside (RGBA layer)
spectrum_noblue.png the same arc with the blue end faded away
yellow_sun.png      what is left after the blue goes: a soft yellowish disc
white_sun.png       the real answer: a blazing white disc
disc_<colour>.png   one soft disc per colour, for the "mix every colour back" slide

If SDXL-Turbo is installed, a generated crayon drawing can replace crayon_sun.png as long as
the file name stays the same.
"""
import colorsys
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "i2v_stills", "sci_ep22_sun_white")
W, H = 1080, 1920
COLOURS = {
    "red": (235, 40, 40), "orange": (250, 140, 30), "yellow": (250, 225, 50),
    "green": (60, 200, 80), "blue": (50, 110, 250), "violet": (150, 60, 220),
}


def soft_disc(size, colour, alpha=255, blur=0.06):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pad = int(size * 0.12)
    ImageDraw.Draw(im).ellipse((pad, pad, size - pad, size - pad), fill=(*colour, alpha))
    return im.filter(ImageFilter.GaussianBlur(size * blur))


def glow_disc(size, colour, core=(255, 255, 255)):
    """A bright core with a smooth radial halo, like a sun seen without an atmosphere."""
    yy, xx = np.mgrid[0:size, 0:size]
    r = np.hypot(xx - size / 2, yy - size / 2) / (size / 2)
    core_a = np.clip((0.30 - r) / 0.02, 0, 1)             # hard-ish disc edge at 30% radius
    halo_a = np.clip(1 - (r - 0.26) / 0.74, 0, 1) ** 2.2    # falls off to the image edge
    rgb = np.zeros((size, size, 3), np.float32)
    for k in range(3):
        rgb[..., k] = colour[k] * (1 - core_a) + core[k] * core_a
    alpha = np.clip(core_a + halo_a * 0.85, 0, 1) * 255
    out = np.dstack([rgb, alpha]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def rainbow_arc(no_blue=False, w=1400, h=760):
    """A smooth rainbow arc, red on the outside, violet inside, centred on the bottom edge."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w / 2, h * 1.02
    r = np.hypot(xx - cx, yy - cy) / (w / 2)
    r_in, r_out = 0.66, 1.0
    t = (r_out - r) / (r_out - r_in)          # 0 at the red edge, 1 at the violet edge
    inside = (t >= 0) & (t <= 1) & (yy < cy)
    hue = np.clip(t, 0, 1) * 0.78             # 0 red .. 0.78 violet
    rgb = np.zeros((h, w, 3), np.float32)
    lut = np.array([colorsys.hsv_to_rgb(hh, 0.92, 1.0) for hh in np.linspace(0, 0.78, 256)]) * 255
    idx = np.clip((hue / 0.78 * 255).astype(int), 0, 255)
    rgb[inside] = lut[idx[inside]]
    edge = np.clip(np.minimum(t, 1 - t) / 0.06, 0, 1)   # soft inner/outer edges
    alpha = np.where(inside, edge, 0.0)
    if no_blue:                               # the blue end thins out, red..yellow stay
        alpha = alpha * np.clip(1 - (t - 0.45) / 0.3, 0.08, 1)
    out = np.dstack([rgb, alpha * 255]).astype(np.uint8)
    return Image.fromarray(out, "RGBA").filter(ImageFilter.GaussianBlur(1.2))


def white_beam():
    """A white light source at the top with a soft beam fanning down and fading out."""
    w, h = 700, 900
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w / 2, h * 0.12
    glow = np.clip(1 - np.hypot(xx - cx, yy - cy) / (w * 0.22), 0, 1) ** 1.6
    half = w * 0.05 + (yy - cy) * 0.22                      # beam widens as it falls
    across = np.clip(1 - np.abs(xx - cx) / np.maximum(half, 1), 0, 1) ** 0.8
    down = np.clip(1 - (yy - cy) / (h - cy), 0, 1) * (yy > cy)
    alpha = np.clip(glow + across * down * 0.55, 0, 1) * 255
    out = np.dstack([np.full((h, w, 3), 255, np.float32), alpha]).astype(np.uint8)
    return Image.fromarray(out, "RGBA").filter(ImageFilter.GaussianBlur(6))


def crayon_sun(seed=22):
    """Yellow crayon sun with wobbly rays on off-white paper, 1080 x 1920."""
    rnd = random.Random(seed)
    paper = Image.new("RGB", (W, H), (246, 242, 230))
    noise = Image.effect_noise((W, H), 18).convert("L")
    paper = Image.composite(paper, Image.new("RGB", (W, H), (225, 220, 205)), noise.point(lambda v: 255 if v > 90 else 200))
    d = ImageDraw.Draw(paper)
    cx, cy, r = W * 0.5, H * 0.42, W * 0.22
    yellow = (250, 205, 40)
    # the disc, drawn as many slightly offset strokes so it looks hand coloured
    for _ in range(140):
        ox, oy = rnd.uniform(-r * 0.06, r * 0.06), rnd.uniform(-r * 0.06, r * 0.06)
        rr = r * rnd.uniform(0.86, 1.0)
        d.ellipse((cx + ox - rr, cy + oy - rr, cx + ox + rr, cy + oy + rr), outline=yellow, width=14)
    d.ellipse((cx - r * 0.86, cy - r * 0.86, cx + r * 0.86, cy + r * 0.86), fill=(252, 215, 60))
    # rays
    for k in range(14):
        ang = k * 2 * math.pi / 14 + rnd.uniform(-0.08, 0.08)
        r0, r1 = r * 1.12, r * rnd.uniform(1.45, 1.75)
        pts = []
        for s in range(6):
            t = s / 5
            rr = r0 + (r1 - r0) * t
            pts.append((cx + math.cos(ang) * rr + rnd.uniform(-6, 6), cy + math.sin(ang) * rr + rnd.uniform(-6, 6)))
        d.line(pts, fill=(245, 180, 30), width=22, joint="curve")
    # a smiling face, because every child draws one
    d.arc((cx - r * 0.45, cy - r * 0.1, cx + r * 0.45, cy + r * 0.55), 20, 160, fill=(120, 80, 20), width=16)
    for ex in (-0.28, 0.28):
        d.ellipse((cx + ex * r - 22, cy - r * 0.3 - 22, cx + ex * r + 22, cy - r * 0.3 + 22), fill=(120, 80, 20))
    # soften like wax on paper
    return Image.blend(paper, paper.filter(ImageFilter.GaussianBlur(2)), 0.5)


def main():
    os.makedirs(OUT, exist_ok=True)
    crayon_sun().save(os.path.join(OUT, "crayon_sun.png"))
    white_beam().save(os.path.join(OUT, "white_beam.png"))
    rainbow_arc().save(os.path.join(OUT, "spectrum.png"))
    rainbow_arc(no_blue=True).save(os.path.join(OUT, "spectrum_noblue.png"))
    glow_disc(900, (255, 205, 90), core=(255, 240, 170)).save(os.path.join(OUT, "yellow_sun.png"))
    glow_disc(900, (235, 240, 255)).save(os.path.join(OUT, "white_sun.png"))
    for name, colour in COLOURS.items():
        soft_disc(600, colour).save(os.path.join(OUT, f"disc_{name}.png"))
    for f in sorted(os.listdir(OUT)):
        print(f"✅ {f}")


if __name__ == "__main__":
    main()
