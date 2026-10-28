"""
Replace one LTX shot with a real public-domain photo and a fast camera move, no GPU.

The photo is placed on black space with a light starfield, then the camera pushes in on
an eased curve (fast from frame 0) with a slight roll, so the subject is unmistakably
moving. Length and audio are copied from the LTX clip it replaces (kept as .ltx.mp4), so
beat timing and the ambient=ltx mix are unchanged.

  python photo_push_shot.py VIDEO_ID SHOT_N IMAGE [--width 0.98] [--zoom 2.2]
      [--cx 0.5 --cy 0.5] [--y 0.42] [--roll 4] [--streaks]

--width: photo width as a fraction of frame width at frame 0
--cx/--cy: point in the photo (fractions) the push ends on
--y: vertical frame position of that point at frame 0
--zoom: scale at the last frame relative to frame 0
--roll: degrees of rotation across the shot
"""
import argparse
import math
import os
import shutil
import subprocess

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 24


def probe(path, entry):
    return subprocess.check_output(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", entry,
         "-of", "default=noprint_wrappers=1:nokey=1", path], text=True).strip()


def ease_out(t):
    return 1 - (1 - t) ** 2.4


def stars(seed=11):
    rng = np.random.default_rng(seed)
    sky = np.zeros((H, W, 3), np.uint8)
    n = 700
    ys, xs = rng.integers(0, H, n), rng.integers(0, W, n)
    sky[ys, xs] = (rng.random(n) ** 3 * 190 + 25).astype(np.uint8)[:, None]
    return Image.fromarray(sky)


def streak_stars(i, n, seed=5, count=260):
    """Stars rushing outward from the frame centre (fly-in parallax), as an RGB array."""
    from PIL import ImageDraw
    rng = np.random.default_rng(seed)
    ang = rng.uniform(0, 2 * math.pi, count)
    r0 = rng.uniform(0.02, 1.0, count)
    spd = rng.uniform(0.6, 1.6, count)
    img = Image.new("RGB", (W, H)); d = ImageDraw.Draw(img)
    rmax = math.hypot(W, H) / 2
    for k in range(count):
        t = (r0[k] + spd[k] * i / max(1, n)) % 1.0
        r = rmax * t ** 2  # accelerate toward the edges like real parallax
        r_prev = rmax * max(0.0, t - 0.035 * spd[k]) ** 2
        b = int(60 + 195 * t)
        x0, y0 = W / 2 + r_prev * math.cos(ang[k]), H / 2 + r_prev * math.sin(ang[k])
        x1, y1 = W / 2 + r * math.cos(ang[k]), H / 2 + r * math.sin(ang[k])
        d.line((x0, y0, x1, y1), fill=(b, b, b), width=2 if t > 0.6 else 1)
    return np.asarray(img)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id"); ap.add_argument("shot", type=int); ap.add_argument("image")
    ap.add_argument("--width", type=float, default=0.98)
    ap.add_argument("--zoom", type=float, default=2.2)
    ap.add_argument("--cx", type=float, default=0.5); ap.add_argument("--cy", type=float, default=0.5)
    ap.add_argument("--y", type=float, default=0.42)
    ap.add_argument("--roll", type=float, default=4.0)
    ap.add_argument("--streaks", action="store_true", help="stars rushing past (fly-in feel)")
    a = ap.parse_args()

    shot = os.path.join(HERE, "temp_clips", f"{a.video_id}_shot_{a.shot}.mp4")
    ltx = os.path.join(HERE, "temp_clips", f"{a.video_id}_shot_{a.shot}.ltx.mp4")
    if not os.path.isfile(ltx):
        shutil.copy2(shot, ltx)
    n = int(probe(ltx, "stream=nb_frames") or round(float(probe(ltx, "format=duration")) * FPS))
    img_path = a.image if os.path.isabs(a.image) else os.path.join(HERE, "i2v_stills", a.video_id, a.image)
    photo = Image.open(img_path).convert("RGB")
    sky = stars()
    # Photo pixels per output pixel at frame 0; the push scales this by up to --zoom.
    base = a.width * W / photo.width
    px, py = a.cx * photo.width, a.cy * photo.height

    tmp = shot + ".video.mp4"
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
         "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(n):
        e = ease_out(i / max(1, n - 1))
        s = base * a.zoom ** e
        ang = math.radians(a.roll * (e - 0.5))
        # Target point drifts from (0.5W, y*H) to the frame centre as we push in.
        tx, ty = W / 2, (a.y + (0.5 - a.y) * e) * H
        # Affine map output -> photo: rotate about (tx, ty), scale 1/s, translate onto (px, py).
        c, sn = math.cos(ang) / s, math.sin(ang) / s
        coeffs = (c, sn, px - c * tx - sn * ty, -sn, c, py + sn * tx - c * ty)
        layer = photo.transform((W, H), Image.AFFINE, coeffs, resample=Image.BICUBIC, fillcolor=(0, 0, 0))
        # Stars only show where the photo is black space.
        bg = streak_stars(i, n) if a.streaks else np.asarray(sky)
        frame = np.maximum(np.asarray(layer), bg)
        enc.stdin.write(frame.astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-i", ltx, "-map", "0:v:0", "-map", "1:a:0?",
                    "-c:v", "copy", "-c:a", "copy", "-t", f"{n / FPS:.4f}", shot], check=True)
    os.remove(tmp)
    print(f"✅ {shot} ({n} frames; LTX original kept as {os.path.basename(ltx)})")


if __name__ == "__main__":
    main()
