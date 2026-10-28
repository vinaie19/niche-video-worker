"""
ep21 beat 2 without a GPU: exactly 760 real Earths pour into Saturn and pack its disc.

Saturn is the public-domain Cassini portrait (2004-10-06) and each Earth is the
public-domain Apollo 17 "Blue Marble", so the picture literally shows the line
"760 Earths could fit inside it". Earths stream in from the top, shrink as they fly and
settle into a hexagonal packing of Saturn's disc, filling it from the bottom up, while the
camera drifts slowly in. Length and audio come from the LTX clip it replaces (kept as
.ltx.mp4).

Run from local_runner/ after fetch_still_assets.py for ep21 and ep17:
  python fill_earths_shot.py
"""
import math
import os
import shutil
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
VID = "sci_ep21_saturn_float"
SATURN = os.path.join(HERE, "i2v_stills", VID, "saturn.jpg")
EARTH = os.path.join(HERE, "i2v_stills", "sci_ep17_sun_black_hole", "earth.jpg")
SHOT = os.path.join(HERE, "temp_clips", f"{VID}_shot_2.mp4")
LTX = os.path.join(HERE, "temp_clips", f"{VID}_shot_2.ltx.mp4")
W, H, FPS = 1080, 1920, 24
N_EARTHS = 760
# Saturn's body in the Cassini photo: centre (fractions of width/height) and semi-axes
# (half-width as a fraction of photo width, half-height as a fraction of photo height),
# measured off a grid overlay. The visible disc is oblate, so pack an ellipse.
BODY_CX, BODY_CY, BODY_A, BODY_B = 0.4875, 0.555, 0.1725, 0.255
A_SCREEN = 420  # body half-width on screen
CX, CY = W / 2, 0.45 * H


def probe_frames(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "stream=nb_frames", "-of", "csv=p=0", path], text=True).strip()
    return int(out)


def hex_slots(a, b, n):
    """n centres of equal discs packed hexagonally inside an ellipse (semi-axes a, b)."""
    r = math.sqrt(a * b * 0.9069 / n) * 1.05
    while True:
        pts, dy, row, y = [], r * math.sqrt(3), 0, -b
        while y <= b:
            x = -a + (r if row % 2 else 0.0)
            while x <= a:
                if (x / (a - r)) ** 2 + (y / (b - r)) ** 2 <= 1:
                    pts.append((x, y))
                x += 2 * r
            y += dy
            row += 1
        if len(pts) >= n:
            pts.sort(key=lambda p: (p[0] / a) ** 2 + (p[1] / b) ** 2)
            return pts[:n], r
        r *= 0.99


def earth_sprite(src, d, cache={}):
    d = max(4, int(round(d)))
    if d not in cache:
        im = src.resize((d, d), Image.LANCZOS)
        mask = Image.new("L", (d, d), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, d - 1, d - 1), fill=255)
        cache[d] = (im, mask)
    return cache[d]


def ease_in_out(t):
    return t * t * (3 - 2 * t)


def main():
    if not os.path.isfile(LTX):
        shutil.copy2(SHOT, LTX)
    n = probe_frames(LTX)
    saturn = Image.open(SATURN).convert("RGB")
    earth = Image.open(EARTH).convert("RGB")
    side = min(earth.size)
    earth = earth.crop(((earth.width - side) // 2, (earth.height - side) // 2,
                        (earth.width + side) // 2, (earth.height + side) // 2)).resize((256, 256), Image.LANCZOS)
    # At ~25px the cloud-white Blue Marble reads grey; push colour so each dot reads as Earth.
    earth = ImageEnhance.Contrast(ImageEnhance.Color(earth).enhance(2.2)).enhance(1.25)
    s0 = A_SCREEN / (BODY_A * saturn.width)  # photo -> screen scale at frame 0
    b_screen = BODY_B * saturn.height * s0
    slots, r = hex_slots(A_SCREEN, b_screen, N_EARTHS)
    # Fill from the bottom up so it reads like pouring into a container.
    order = sorted(range(N_EARTHS), key=lambda k: -slots[k][1])
    rng = np.random.default_rng(3)
    start_x = rng.uniform(-0.2 * W, 1.2 * W, N_EARTHS)
    land_by = 0.82 * n  # all settled with a beat to spare
    fly = 0.30 * n
    launch = {k: (rank / N_EARTHS) * (land_by - fly) for rank, k in enumerate(order)}

    tmp = SHOT + ".video.mp4"
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
         "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(n):
        push = 1.0 + 0.07 * (i / max(1, n - 1))  # slow camera drift in
        s = s0 * push
        px, py = BODY_CX * saturn.width, BODY_CY * saturn.height
        coeffs = (1 / s, 0, px - CX / s, 0, 1 / s, py - CY / s)
        frame = saturn.transform((W, H), Image.AFFINE, coeffs, resample=Image.BICUBIC, fillcolor=(0, 0, 0))
        for k in order:
            t0 = launch[k]
            if i < t0:
                continue
            u = min(1.0, (i - t0) / fly)
            e = ease_in_out(u)
            sx, sy = slots[k][0] * push + CX, slots[k][1] * push + CY
            bx, by = start_x[k], -60.0
            # Curve in: fall mostly vertically, swing sideways late.
            x = bx + (sx - bx) * e
            y = by + (sy - by) * (1 - (1 - u) ** 2)
            d = 2 * r * push * (1 + 1.6 * (1 - e))
            im, mask = earth_sprite(earth, d)
            frame.paste(im, (int(x - im.width / 2), int(y - im.height / 2)), mask)
        enc.stdin.write(np.asarray(frame).tobytes())
    enc.stdin.close(); enc.wait()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-i", LTX, "-map", "0:v:0", "-map", "1:a:0?",
                    "-c:v", "copy", "-c:a", "copy", "-t", f"{n / FPS:.4f}", SHOT], check=True)
    os.remove(tmp)
    print(f"✅ {SHOT} ({n} frames, {N_EARTHS} Earths of radius {r:.1f}px; LTX kept as {os.path.basename(LTX)})")


if __name__ == "__main__":
    main()
