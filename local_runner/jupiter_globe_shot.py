"""
ep20 shot 1 without a GPU: a real Jupiter globe from Hubble's public-domain OPAL map.

The cylindrical map is projected onto a sphere (orthographic), so the planet is a true
round disc. Over the shot the camera rotates the Great Red Spot to face us and pushes in
from the whole planet to a tight view of the Spot, while an orange glow swells beneath
the clouds and dies away ("...it just never got to burn").

Run from local_runner/ after:  VIDEO_ID=sci_ep20_jupiter_star python fetch_still_assets.py
  python jupiter_globe_shot.py
Writes temp_clips/sci_ep20_jupiter_star_shot_1.mp4 (the LTX clip is kept as .ltx.mp4 and
its audio bed is reused, so the stitch's ambient=ltx mix still works).
"""
import math
import os
import shutil
import subprocess

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
VID = "sci_ep20_jupiter_star"
MAP = os.path.join(HERE, "i2v_stills", VID, "jupiter.jpg")
SHOT = os.path.join(HERE, "temp_clips", f"{VID}_shot_1.mp4")
LTX = os.path.join(HERE, "temp_clips", f"{VID}_shot_1.ltx.mp4")
W, H, FPS = 1080, 1920, 24
DUR = 121 / 24.0  # same length as the LTX shot it replaces

# Map covers about +/-79 deg latitude (3600x1577 px over 360 deg of longitude).
LAT_SPAN = 1577 / 3600 * 360.0
GRS_LON = 0.645 * 360.0 - 180.0  # Great Red Spot, read off the map (x 0.645, y 0.635)
GRS_LAT = LAT_SPAN / 2 - 0.635 * LAT_SPAN
R0, R1 = 0.43 * W, 2.4 * W  # whole planet with space around it -> tight on the Spot
CY = 0.42 * H  # disc centre sits above the captions


def ease_out(t):
    return 1 - (1 - t) ** 2.2


def bilinear(tex, u, v):
    """Sample tex (h, w, 3 float) at fractional pixel coords u (x, wraps) and v (y, clamped)."""
    h, w, _ = tex.shape
    u = np.mod(u, w)
    v = np.clip(v, 0, h - 1.001)
    x0 = np.floor(u).astype(np.int64); y0 = np.floor(v).astype(np.int64)
    x1 = (x0 + 1) % w; y1 = y0 + 1
    fx = (u - x0)[..., None]; fy = (v - y0)[..., None]
    top = tex[y0, x0] * (1 - fx) + tex[y0, x1] * fx
    bot = tex[y1, x0] * (1 - fx) + tex[y1, x1] * fx
    return top * (1 - fy) + bot * fy


def stars(seed=7):
    rng = np.random.default_rng(seed)
    sky = np.zeros((H, W, 3), np.float32)
    n = 900
    ys, xs = rng.integers(0, H, n), rng.integers(0, W, n)
    sky[ys, xs] = (rng.random(n) ** 3 * 200 + 30)[:, None]
    return sky


def frame(tex, sky, t):
    e = ease_out(t / DUR)
    R = R0 * (R1 / R0) ** e  # exponential zoom reads as a steady dive
    lon0 = math.radians(GRS_LON - 55 * (1 - e))  # Spot rotates in from the left
    lat0 = math.radians(GRS_LAT * e)  # and tilts up to face the camera
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    x = (xs - W / 2) / R
    y = -(ys - CY) / R
    rho2 = x * x + y * y
    inside = rho2 < 1.0
    rho = np.sqrt(np.where(inside, rho2, 0)) + 1e-9
    c = np.arcsin(np.clip(rho, 0, 1))
    sin_c, cos_c = np.sin(c), np.cos(c)
    lat = np.arcsin(np.clip(cos_c * math.sin(lat0) + y * sin_c * math.cos(lat0) / rho, -1, 1))
    lon = lon0 + np.arctan2(x * sin_c, rho * cos_c * math.cos(lat0) - y * sin_c * math.sin(lat0))
    th, tw, _ = tex.shape
    u = (np.degrees(lon) + 180.0) / 360.0 * tw
    v = (LAT_SPAN / 2 - np.degrees(lat)) / LAT_SPAN * th
    col = bilinear(tex, u, v)
    mu = np.sqrt(np.clip(1 - rho2, 0, 1))[..., None]  # limb darkening
    col = col * (0.35 + 0.65 * mu ** 0.5) * 1.12
    # Glow under the clouds: swells to ~3.6s, then dies ("never got to burn").
    g = math.exp(-((t - 3.6) / 0.75) ** 2)
    flick = 0.85 + 0.15 * math.sin(t * 23.0)
    a = 0.6 * g * flick
    col = col * np.array([1 + 0.30 * a, 1 - 0.18 * a, 1 - 0.60 * a], np.float32)  # warm the clouds
    col = col + np.array([120, 35, 0], np.float32) * a * mu  # deep orange light from below
    # Thin atmospheric rim + soft halo outside the limb.
    halo = np.clip(1.0 - (np.sqrt(rho2) - 1.0) * R / 26.0, 0, 1) * (~inside)
    rim = np.array([255, 190, 120], np.float32) * (0.25 + 0.5 * g) * halo[..., None] ** 2
    out = np.where(inside[..., None], col, sky + rim)
    return np.clip(out, 0, 255).astype(np.uint8)


def main():
    tex = np.asarray(Image.open(MAP).convert("RGB"), np.float32)
    sky = stars()
    if not os.path.isfile(LTX):
        shutil.copy2(SHOT, LTX)
    tmp = SHOT + ".video.mp4"
    n = round(DUR * FPS)
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
         "-pix_fmt", "yuv420p", tmp],
        stdin=subprocess.PIPE,
    )
    for i in range(n):
        enc.stdin.write(frame(tex, sky, i / FPS).tobytes())
        if i % 24 == 0:
            print(f"   frame {i}/{n}")
    enc.stdin.close(); enc.wait()
    # Reuse the LTX clip's audio bed so ambient=ltx keeps working in the stitch.
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-i", LTX, "-map", "0:v:0", "-map", "1:a:0",
                    "-c:v", "copy", "-c:a", "copy", "-shortest", SHOT], check=True)
    os.remove(tmp)
    print(f"✅ {SHOT} (LTX original kept as {os.path.basename(LTX)})")


if __name__ == "__main__":
    main()
