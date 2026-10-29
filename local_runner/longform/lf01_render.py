"""
LF01 step 2: render "How Big Is the Universe? A True-Scale Journey" (16:9, 1920x1080, 24 fps).

Every visual is timed to the spoken sentences in temp_clips/lf01_universe_scale_audio/timeline.json
(lf01_voice.py). Real public-domain NASA imagery + true-scale diagrams; scale is Earth = 1 cm.
Renders in parallel (one ffmpeg segment per worker), then lf01_finish.py mixes audio.

  python longform/lf01_render.py              # full render
  python longform/lf01_render.py --preview T1 T2 ...   # stills at given seconds -> scratch png
"""
import json
import math
import os
import subprocess
import sys
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
os.environ.setdefault("CHANNEL", "b")

W, H, FPS = 1920, 1080, 30  # 30 fps: smoother pulls and zooms on phones
ASSETS = os.path.join(ROOT, "i2v_stills", "lf01_universe_scale")
WORK = os.path.join(ROOT, "temp_clips", "lf01_universe_scale_audio")
SEG_DIR = os.path.join(ROOT, "temp_clips", "lf01_segments")
OUTRO_S = 12.0
XFADE = 0.6
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
AMBER = (255, 176, 72); WHITE = (255, 255, 255); CYAN = (140, 210, 255); GREEN = (150, 255, 190)
DIM = (175, 185, 205)

TL = json.load(open(os.path.join(WORK, "timeline.json")))
BEATS = TL["beats"]
TOTAL = TL["total"] + OUTRO_S


def S(prefix):
    """Start time of the sentence starting with prefix."""
    for b in BEATS:
        if b["text"].startswith(prefix):
            return b["start"]
    raise KeyError(prefix)


def E(prefix):
    for b in BEATS:
        if b["text"].startswith(prefix):
            return b["end"]
    raise KeyError(prefix)


CH = [(b["start"] - (0.35 if i == 0 else 0.0), b["ch"]) for i, b in enumerate(BEATS) if b["ch"]]


# ---------- easing ---------------------------------------------------------------------

def sm(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def ramp(t, t0, d=0.6):
    return sm((t - t0) / d) if d > 0 else float(t >= t0)


def eo(x):
    x = min(1.0, max(0.0, x)); return 1 - (1 - x) ** 3


def lerp(a, b, u):
    return a + (b - a) * u


def lerp_log(a, b, u):
    return math.exp(math.log(a) + (math.log(b) - math.log(a)) * u)


# ---------- assets -----------------------------------------------------------------------

class Assets:
    def __init__(self):
        from ep23_planet_stack import disc_sprite, jupiter_sprite
        self.disc = {n: disc_sprite(os.path.join(ASSETS, f"{n}.jpg"))
                     for n in ["earth", "moon", "sun", "mercury", "venus", "mars", "uranus", "neptune"]}
        self.disc["jupiter"] = jupiter_sprite(700)
        self.photo = {}
        for n, crop in [("milkyway", None), ("andromeda", (0.12, 0.12, 0.88, 0.88)), ("udf", None),
                        ("voyager", None), ("city", None)]:
            im = Image.open(os.path.join(ASSETS, f"{n}.jpg")).convert("RGB")
            if crop:
                w, h = im.size
                im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
            im.thumbnail((2600, 2600), Image.LANCZOS)
            self.photo[n] = im
        rng = np.random.default_rng(7)
        n = 1400
        self.sx, self.sy = rng.uniform(0, 1, n), rng.uniform(0, 1, n)
        self.sb = rng.random(n) ** 3 * 210 + 30
        self.ss = (rng.random(n) > 0.97)

    @lru_cache(maxsize=512)
    def sprite(self, name, d):
        d = max(2, int(round(d)))
        return self.disc[name].resize((d, d), Image.LANCZOS)


A = None


def assets():
    global A
    if A is None:
        A = Assets()
    return A


@lru_cache(maxsize=512)
def label_img(text, size, color, bold=True, glow=True):
    fnt = ImageFont.truetype(BOLD if bold else REG, size)
    l, t, r, b = fnt.getbbox(text)
    pad = int(size * 0.6) + 6
    im = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if glow:
        g = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(g).text((pad - l, pad - t), text, font=fnt, fill=(0, 0, 0, 230),
                               stroke_width=max(2, size // 10))
        im = Image.alpha_composite(im, g.filter(ImageFilter.GaussianBlur(max(2, size // 6))))
        d = ImageDraw.Draw(im)
    d.text((pad - l, pad - t), text, font=fnt, fill=color + (255,), stroke_width=max(1, size // 22),
           stroke_fill=(8, 8, 16, 255))
    return im


# ---------- drawing primitives ---------------------------------------------------------------

class Frame:
    def __init__(self):
        # RGB canvas: ImageDraw(..., "RGBA") then *blends* translucent fills/lines onto it.
        self.im = Image.new("RGB", (W, H), (0, 0, 0))

    def stars(self, alpha=1.0, drift=(0.0, 0.0), zoom=1.0):
        if alpha <= 0:
            return
        a = assets()
        arr = np.asarray(self.im).copy()
        x = ((a.sx - 0.5) * zoom + 0.5 + drift[0]) % 1.0 * W
        y = ((a.sy - 0.5) * zoom + 0.5 + drift[1]) % 1.0 * H
        b = (a.sb * alpha).astype(np.uint8)
        xi, yi = x.astype(int), y.astype(int)
        arr[yi, xi, :3] = np.maximum(arr[yi, xi, :3], b[:, None])
        big = a.ss
        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            xx, yy = np.clip(xi[big] + dx, 0, W - 1), np.clip(yi[big] + dy, 0, H - 1)
            arr[yy, xx, :3] = np.maximum(arr[yy, xx, :3], (b[big] * 0.6).astype(np.uint8)[:, None])
        self.im = Image.fromarray(arr, "RGB")

    def paste(self, img, cx, cy, alpha=1.0):
        if alpha <= 0.01:
            return
        if alpha < 0.999:
            img = img.copy(); img.putalpha(img.getchannel("A").point(lambda v: int(v * alpha)))
        x0, y0 = int(round(cx - img.width / 2)), int(round(cy - img.height / 2))
        bx0, by0 = max(0, -x0), max(0, -y0)
        bx1, by1 = min(img.width, W - x0), min(img.height, H - y0)
        if bx1 <= bx0 or by1 <= by0:
            return
        if (bx0, by0, bx1, by1) != (0, 0, img.width, img.height):
            img = img.crop((bx0, by0, bx1, by1))
        self.im.paste(img, (x0 + bx0, y0 + by0), img)

    def planet(self, name, cx, cy, d, alpha=1.0, halo=0.0, halo_col=(255, 225, 170)):
        if halo > 0:
            r = d * 1.6 + 14
            g = halo_img(int(r), halo_col)
            self.paste(g, cx, cy, alpha * halo)
        self.paste(assets().sprite(name, d), cx, cy, alpha)

    def label(self, text, cx, cy, size=44, color=WHITE, alpha=1.0, bold=True):
        self.paste(label_img(text, size, color, bold), cx, cy, alpha)

    def photo(self, name, zoom=1.0, cx=0.5, cy=0.5, alpha=1.0, rot=0.0, fit="cover", box=None):
        """Photo with Ken-Burns zoom about (cx, cy) in photo fractions. box=(x0,y0,x1,y1) to draw in."""
        if alpha <= 0.01:
            return
        p = assets().photo[name]
        bx0, by0, bx1, by1 = box or (0, 0, W, H)
        bw, bh = bx1 - bx0, by1 - by0
        base = max(bw / p.width, bh / p.height) if fit == "cover" else min(bw / p.width, bh / p.height)
        s = base * zoom
        c, sn = math.cos(math.radians(rot)) / s, math.sin(math.radians(rot)) / s
        px, py = cx * p.width, cy * p.height
        tx, ty = bw / 2, bh / 2
        coeffs = (c, sn, px - c * tx - sn * ty, -sn, c, py + sn * tx - c * ty)
        layer = p.transform((bw, bh), Image.AFFINE, coeffs, resample=Image.BILINEAR, fillcolor=(0, 0, 0))
        if alpha < 0.999:
            self.im.paste(layer, (bx0, by0), Image.new("L", layer.size, int(255 * alpha)))
        else:
            self.im.paste(layer, (bx0, by0))

    def draw(self):
        return ImageDraw.Draw(self.im, "RGBA")

    def line(self, pts, color, width=3, alpha=1.0):
        if alpha > 0:
            self.draw().line(pts, fill=color + (int(255 * alpha),), width=width)

    def dashed(self, x0, y0, x1, y1, color, width=3, dash=16, gap=14, alpha=1.0):
        L = math.hypot(x1 - x0, y1 - y0)
        if L < 1 or alpha <= 0:
            return
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        d, dr = 0.0, self.draw()
        while d < L:
            e = min(L, d + dash)
            dr.line((x0 + ux * d, y0 + uy * d, x0 + ux * e, y0 + uy * e), fill=color + (int(255 * alpha),), width=width)
            d += dash + gap

    def pulse(self, x, y, alpha=1.0, r=9):
        self.paste(halo_img(r * 3, (255, 250, 220)), x, y, alpha)
        self.draw().ellipse((x - r / 2, y - r / 2, x + r / 2, y + r / 2), fill=(255, 255, 240, int(255 * alpha)))

    def ruler(self, x0, x1, y, cm_px, n_cm, step_lbl=5, alpha=1.0, upto=None):
        """A ruler from x0 with a tick every cm, labels every step_lbl cm; drawn up to x 'upto'."""
        if alpha <= 0:
            return
        upto = x1 if upto is None else upto
        dr = self.draw()
        a = int(255 * alpha)
        dr.rectangle((x0, y - 6, upto, y + 22), fill=(235, 215, 160, int(70 * alpha)),
                     outline=(235, 215, 160, int(170 * alpha)))
        for k in range(n_cm + 1):
            x = x0 + k * cm_px
            if x > upto + 0.5:
                break
            h = 20 if k % step_lbl == 0 else 10
            dr.line((x, y - 6, x, y - 6 + h), fill=(255, 240, 200, a), width=2)
            if k % step_lbl == 0:
                self.label(f"{k}", x, y + 44, 26, (255, 235, 190), alpha, bold=False)

    def big_text(self, text, cy, size=96, color=WHITE, alpha=1.0):
        self.label(text, W / 2, cy, size, color, alpha)

    def fade(self, k):
        """Fade to black by k (0..1)."""
        if k > 0:
            self.im = Image.blend(self.im, Image.new("RGB", (W, H)), min(1.0, k))

    def rgb(self):
        return self.im


@lru_cache(maxsize=128)
def halo_img(r, col):
    s = int(r * 2 + 8)
    g = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse((s / 2 - r / 2, s / 2 - r / 2, s / 2 + r / 2, s / 2 + r / 2), fill=col + (200,))
    return g.filter(ImageFilter.GaussianBlur(r / 3))


# ---------- chapters ---------------------------------------------------------------------------

def ch_marble(F, t):
    t1, t2, t3, t4, t5 = (S("Shrink"), S("Now, let's"), S("Every size"), S("By the end"), S("It won't even"))
    F.stars(0.8, drift=(t * 0.002, 0))
    u = eo((t - t1) / 3.2)
    push = sm((t - t1 - 3.2) / max(1.0, t4 - t1 - 3.2))  # slow push on the marble after the shrink
    d = lerp_log(880, 70, u) * (1 + 0.45 * push)
    cx, cy = 960, lerp(540, 430, u)
    F.planet("earth", cx, cy, d)
    k = ramp(t, t1 + 2.8)
    if k > 0:
        F.ruler(cx - 35, cx + 35, cy + 70, 70, 1, step_lbl=1, alpha=k)
        F.label("EARTH = 1 cm", cx, cy + 170, 46, AMBER, k)
    k2 = ramp(t, t2 + 0.3)
    F.label("1 cm  =  12,742 km", cx, cy + 235, 34, DIM, k2)
    # The promise: flashes of where we're going
    for i, (name, t0) in enumerate((("milkyway", t4 + 0.2), ("andromeda", t5 + 0.1), ("udf", t5 + 1.0))):
        k3 = ramp(t, t0, 0.25) * (1 - ramp(t, t0 + 1.0, 0.35))
        if k3 > 0:
            F.photo(name, zoom=1.05 + 0.05 * (t - t0), alpha=0.75 * k3)
            F.planet("earth", cx, cy, d)
    if t > t3 - 0.1 and t < t4 + 0.4:
        kk = ramp(t, t3, 0.4) * (1 - ramp(t, t4, 0.4))
        F.label("same scale for everything", cx, 140, 34, DIM, kk)
        # teaser strip of what's coming, sliding in
        for j, (kind, name) in enumerate((("disc", "sun"), ("photo", "milkyway"), ("photo", "udf"))):
            kj = ramp(t, t3 + 0.25 * j, 0.5) * kk
            x = 560 + 400 * j + 60 * (1 - kj)
            if kind == "disc":
                F.planet(name, x, 860, 220, kj, halo=0.4 * kj, halo_col=(255, 150, 60))
            else:
                F.photo(name, zoom=1.0, alpha=kj, fit="cover", box=(int(x - 150), 750, int(x + 150), 970))


def ch_moon(F, t):
    t0, tg, td, tf, t24, tl = (S("Let's start"), S("The Moon becomes"), S("And it sits"), S("That ruler"),
                               S("Twenty four"), S("Light crosses"))
    F.stars(0.7, drift=(0.02 + t * 0.001, 0))
    cm = 50
    ex, ey = 205, 520
    u = eo((t - t0) / 1.4)
    F.planet("earth", lerp(960, ex, u), lerp(470, ey, u), lerp(70, 50, u))
    mx = ex + 30.2 * cm
    km = ramp(t, tg + 0.3)
    F.planet("moon", mx, ey, 13.6, km, halo=1.6 * km, halo_col=(230, 230, 255))
    if km > 0:
        F.draw().ellipse((mx - 26, ey - 26, mx + 26, ey + 26), outline=(230, 230, 255, int(200 * km)), width=2)
    F.label("MOON  ·  2.7 mm", mx, ey - 70, 34, WHITE, km)
    F.label("EARTH", ex, ey - 70, 30, DIM, ramp(t, t0 + 1.2))
    kr = sm((t - td - 0.2) / 2.0)
    if kr > 0:
        F.ruler(ex, mx, ey + 60, cm, 30, alpha=1.0, upto=lerp(ex, mx, kr))
        F.label("30 cm", (ex + mx) / 2, ey + 150, 56, AMBER, ramp(t, td + 1.6))
    kh = ramp(t, tf + 0.2) * (1 - ramp(t, tl - 0.3))
    if kh > 0:
        F.line((ex, ey, mx, ey), (255, 200, 120), 3, 0.5 * kh)
        F.label("the farthest any human has ever been", (ex + mx) / 2, ey - 150, 38, WHITE, kh)
    k24 = ramp(t, t24 + 0.1) * (1 - ramp(t, tl - 0.3))
    if k24 > 0:
        F.label("24 crossed it  ·  12 walked on it", (ex + mx) / 2, ey + 250, 40, CYAN, k24)
        dr = F.draw()
        for j in range(24):  # the Apollo crews, one dot each, flying Earth -> Moon
            x = sm((t - t24 - 0.1 - j * 0.12) / 1.6)
            if x <= 0:
                continue
            walked = j % 2 == 0
            px = lerp(ex + 30, mx - 30, x)
            py = ey - 22 - (j % 6) * 7
            col = (255, 220, 120) if (walked and x >= 1) else (140, 210, 255)
            if x >= 1:  # landed: 12 gold (walked) and 12 blue (stayed in orbit) in two rows below the Moon
                px = mx - 66 + (j // 2) * 12; py = ey + 30 if walked else ey + 44
            dr.ellipse((px - 4, py - 4, px + 4, py + 4), fill=col + (int(255 * k24),))
    if t >= tl + 0.6:
        x = min(1.0, (t - tl - 0.6) / 1.28)
        F.pulse(lerp(ex, mx, x), ey, 1.0 - max(0, (t - tl - 2.4)) * 2)
        F.label(f"light: {min(1.28, t - tl - 0.6):.2f} s", (ex + mx) / 2, ey - 150, 48, (255, 245, 210))


def ch_sun(F, t):
    t0, tb, t109, th, tfar, tlight, tplay = (S("Now, the Sun"), S("At this scale"), S("You could line"),
                                             S("And if it were"), S("And it isn't"), S("Even light"), S("The sunlight"))
    F.stars(0.6, drift=(0.04 + t * 0.001, 0.01))
    sun_d = 860
    scx, scy = 960, 540
    if t < tfar + 0.3:
        kg = eo((t - t0) / 1.6)
        F.planet("sun", scx, scy, lerp(20, sun_d, kg), halo=0.35 * kg, halo_col=(255, 150, 60))
        F.label("SUN  ·  1.09 m wide", scx, 70, 46, AMBER, ramp(t, tb + 0.3))
        # 109 Earths across the diameter
        n = int(109 * sm((t - t109 - 0.2) / 2.2))
        ed = sun_d / 109
        for i in range(n):
            F.planet("earth", scx - sun_d / 2 + ed * (i + 0.5), scy, ed)
        if n:
            F.label(f"{n} Earths", scx, scy + 80, 52, WHITE)
        kf = ramp(t, th + 0.2)
        if kf > 0:
            rng = np.random.default_rng(3)
            m = int(2600 * sm((t - th - 0.2) / 2.5))
            ang, rad = rng.uniform(0, 2 * math.pi, 2600), np.sqrt(rng.uniform(0, 1, 2600)) * sun_d / 2 * 0.95
            dr = F.draw()
            for k in range(m):
                x, y = scx + rad[k] * math.cos(ang[k]), scy + rad[k] * math.sin(ang[k])
                dr.ellipse((x - 2.2, y - 2.2, x + 2.2, y + 2.2), fill=(90, 150, 255, 230))
            F.label("1,300,000 Earths inside", scx, H - 70, 46, CYAN, kf)
    else:
        # Zoom out to the football pitch: Earth at one end, the Sun 117 m away
        u = eo((t - tfar - 0.3) / 1.6)
        ppm = 1560 / 117.4 * (1 + 0.04 * sm((t - tfar) / max(1.0, tplay + 3 - tfar)))
        ex = 960 - 117.4 * ppm / 2
        sx, y = ex + 117.4 * ppm, 560
        fx0, fx1 = ex + 6.2 * ppm, ex + 111.2 * ppm
        fy0, fy1 = y - 34 * ppm, y + 34 * ppm
        kf = u
        dr = F.draw()
        dr.rectangle((fx0, fy0, fx1, fy1), fill=(30, 110, 45, int(150 * kf)), outline=(235, 255, 235, int(200 * kf)), width=3)
        mid = (fx0 + fx1) / 2
        dr.line((mid, fy0, mid, fy1), fill=(235, 255, 235, int(200 * kf)), width=3)
        r = 9.15 * ppm
        dr.ellipse((mid - r, y - r, mid + r, y + r), outline=(235, 255, 235, int(200 * kf)), width=3)
        for gx, sgn in ((fx0, 1), (fx1, -1)):
            dr.rectangle((min(gx, gx + sgn * 16.5 * ppm), y - 20.2 * ppm, max(gx, gx + sgn * 16.5 * ppm), y + 20.2 * ppm),
                         outline=(235, 255, 235, int(200 * kf)), width=3)
        sd = lerp(sun_d, 1.09 * ppm, u)
        F.planet("sun", lerp(scx, sx, u), lerp(scy, y, u), max(4, sd), halo=0.9, halo_col=(255, 170, 70))
        F.planet("earth", ex, y, 4, alpha=kf, halo=0.8 * kf, halo_col=(120, 170, 255))
        F.label("EARTH", ex, y - 70, 30, DIM, kf)
        F.label("SUN", sx, y - 70, 30, AMBER, kf)
        kd = ramp(t, tfar + 1.6)
        F.dashed(ex, fy1 + 55, sx, fy1 + 55, (255, 220, 150), 3, alpha=kd)
        F.label("117 m", (ex + sx) / 2, fy1 + 100, 60, AMBER, kd)
        F.label("longer than a football pitch", (ex + sx) / 2, fy0 - 60, 38, WHITE, kd * (1 - ramp(t, tlight)))
        if t >= tlight + 0.3:
            x = min(1.0, (t - tlight - 0.3) / max(2.0, (tplay - tlight) - 0.5))
            F.pulse(lerp(sx, ex, x), y, 1.0)
            secs = int(499 * x)
            F.label(f"light travel: {secs // 60} min {secs % 60:02d} s", (ex + sx) / 2, fy0 - 60, 48, (255, 245, 210))
        if t >= tplay + 0.4:
            F.label("that sunlight left before you pressed play", (ex + sx) / 2, fy1 + 170, 38, CYAN, ramp(t, tplay + 0.4))


PLANET_KM = [("mercury", 0.0454, 14), ("venus", 0.0849, 20), ("earth", 0.1174, 20), ("mars", 0.1789, 16),
             ("jupiter", 0.611, 46), ("saturn", 1.124, 0), ("uranus", 2.253, 28), ("neptune", 3.533, 28)]


def ch_planets(F, t):
    t0, tj, tn, tp, tb, tv, tv2, tt = (S("Keep walking"), S("Jupiter, the giant"), S("Neptune, the last"), S("Pluto is"),
                                       S("And in between"), S("And Voyager"), S("is only about"), S("Everything humanity"))
    F.stars(0.5, drift=(0.06 + t * 0.0012, 0.01))
    # camera: px per km eases 0.7 km -> 4.9 km -> 22 km windows
    w1, w2, w3 = 1700 / 0.72, 1700 / 4.9, 1700 / 22.0
    if t < tn:
        ppk = w1
    elif t < tv:
        ppk = lerp_log(w1, w2, eo((t - tn) / 2.0))
    else:
        ppk = lerp_log(w2, w3, eo((t - tv) / 3.0))
    x0, y = 110, 560
    F.planet("sun", x0, y, 26, halo=0.8, halo_col=(255, 170, 70))
    F.label("SUN", x0, y + 60, 30, AMBER)
    F.line((x0, y, W, y), (120, 140, 180), 2, 0.6)
    dim_mid = 1 - 0.7 * ramp(t, tb + 0.2) * (1 - ramp(t, tv))
    for name, km, d in PLANET_KM:
        x = x0 + km * ppk
        if x > W + 50 or d == 0:
            if name == "saturn" and x < W + 50:
                F.draw().ellipse((x - 9, y - 9, x + 9, y + 9), fill=(230, 210, 160, int(255 * dim_mid)))
                F.label("Saturn", x, y - 46, 30, DIM, dim_mid * (1 - ramp(t, tv + 1.0)))
            continue
        F.planet(name, x, y, d * (0.6 if ppk < w1 * 0.5 else 1.0), alpha=dim_mid)
        inner = name in ("mercury", "venus", "earth", "mars")
        zoomed_out = ppk < w1 * 0.5
        if inner and zoomed_out:
            continue  # one shared "inner planets" label below instead of four overlapping ones
        below = name in ("venus", "mars")  # stagger the crowded inner-planet labels
        F.label(name.capitalize(), x, y + (46 if below else -46), 30, DIM, dim_mid * (1 - ramp(t, tv + 1.0)))
    if ppk < w1 * 0.5:
        F.label("inner planets", x0 + 0.12 * ppk + 150, y + 46, 26, DIM, dim_mid * (1 - ramp(t, tv + 1.0)))
    kj = ramp(t, tj + 0.3) * (1 - ramp(t, tn))
    if kj > 0:
        xj = x0 + 0.611 * ppk
        F.label("JUPITER  ·  grapefruit-sized  ·  611 m", xj - 120, y + 120, 40, WHITE, kj)
    kn = ramp(t, tn + 1.8) * (1 - ramp(t, tv))
    if kn > 0:
        xn = x0 + 3.533 * ppk
        F.label("NEPTUNE  ·  3.5 km", min(xn, W - 260), y + 120, 44, WHITE, kn)
        F.label("a long walk across a city", min(xn, W - 260), y + 175, 32, DIM, kn)
    kp = ramp(t, tp + 0.2)
    xp = x0 + 4.64 * ppk
    if kp > 0 and xp < W:
        F.draw().ellipse((xp - 3, y - 3, xp + 3, y + 3), fill=(220, 200, 180, int(255 * kp * dim_mid)))
        F.label("Pluto", xp, y - 40, 30, DIM, kp * dim_mid * (1 - ramp(t, tv + 1.0)))
        F.label("PLUTO  ·  a speck, 4.6 km", xp - 60, y + 230, 34, DIM, kp * (1 - ramp(t, tb)))
    kb = ramp(t, tb + 0.2) * (1 - ramp(t, tv))
    F.label("almost entirely empty", W / 2, 200, 52, WHITE, kb)
    # Voyager
    kv = ramp(t, tv + 0.8)
    if kv > 0:
        xv = x0 + 20.3 * ppk
        F.paste(voyager_img(), xv, y - 150, kv)
        F.draw().ellipse((xv - 5, y - 5, xv + 5, y + 5), fill=(255, 255, 255, int(255 * kv)))
        F.line((xv, y - 70, xv, y - 6), (255, 255, 255), 2, kv)
        F.label("VOYAGER 1", xv, y + 60, 34, WHITE, kv)
        F.label("49 years  ·  17 km/s", xv - 30, y + 105, 30, DIM, kv * (1 - ramp(t, tv2)))
        k2 = ramp(t, tv2 + 0.2)
        F.label("20 km", xv, y + 110, 64, AMBER, k2)
    kt = ramp(t, tt + 0.2)
    if kt > 0:
        xv = x0 + 20.3 * ppk
        r = xv - x0
        F.draw().ellipse((x0 - r, y - r, x0 + r, y + r), outline=(150, 255, 190, int(180 * kt)), width=4)
        F.label("everything we've ever launched", W / 2 - 200, 170, 50, GREEN, kt)


@lru_cache(maxsize=1)
def voyager_img():
    p = assets().photo["voyager"]
    w, h = p.size
    crop = p.crop((int(0.22 * w), int(0.18 * h), int(0.70 * w), int(0.62 * h))).resize((230, 210), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", crop.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, crop.width - 1, crop.height - 1), 18, fill=255)
    crop.putalpha(m)
    return crop


def ch_star(F, t):
    t0, tp, tw, twk, tn, tl, tv, tm = (S("Now, the nearest"), S("Proxima"), S("That's most"), S("Walking there"),
                                       S("And between"), S("Its light"), S("Even Voyager"), S("If you remember"))
    k_on = 1 - ramp(t, tn + 0.3, 1.5)
    F.stars(0.5 * k_on + 0.05, drift=(0.08, 0.02))
    # the star, far right
    ks = ramp(t, t0 + 0.2)
    F.paste(halo_img(40, (255, 160, 120)), 1760, 300, ks)
    F.draw().ellipse((1754, 294, 1766, 306), fill=(255, 220, 200, int(255 * ks)))
    F.label("PROXIMA CENTAURI", 1680, 360, 30, (255, 200, 180), ks * (1 - ramp(t, tm)))
    # Earth with the 31,500 km arc
    ke = ramp(t, tp + 0.2) * k_on
    if ke > 0:
        ex, ey, ed = 820, 560, 620
        F.planet("earth", ex, ey, ed, ke)
        frac = 0.787 * sm((t - tp - 0.6) / 2.6)
        r = ed / 2 + 26
        dr = F.draw()
        if frac > 0:
            dr.arc((ex - r, ey - r, ex + r, ey + r), -90, -90 + 360 * frac, fill=(255, 190, 90, int(255 * ke)), width=9)
            a = math.radians(-90 + 360 * frac)
            F.pulse(ex + r * math.cos(a), ey + r * math.sin(a), ke)
        F.label("31,500 km", ex, 120, 64, AMBER, ramp(t, tp + 1.0) * k_on)
        F.label("most of the way around the real Earth", ex, 190, 36, WHITE, ramp(t, tw + 0.2) * k_on)
        F.label("on foot, non-stop: ~260 days", ex, H - 80, 40, CYAN, ramp(t, twk + 0.3) * k_on)
    kn = ramp(t, tn + 1.0) * (1 - ramp(t, tl))
    F.big_text("nothing", 540, 88, DIM, kn)
    kl = ramp(t, tl + 0.2) * (1 - ramp(t, tm))
    if kl > 0:
        F.dashed(160, 600, 1754, 300, (255, 245, 210), 3, alpha=kl * 0.7)
        x = sm((t - tl - 0.3) / 2.2)
        F.pulse(lerp(1754, 160, x), lerp(300, 600, x), kl)
        F.label("its light: 4.2 years to reach us", W / 2, 760, 46, (255, 245, 210), kl)
        F.label("Voyager: ~70,000 years", W / 2, 840, 46, CYAN, ramp(t, tv + 0.3) * kl)
    km = ramp(t, tm + 1.6)
    F.big_text("SPACE IS MOSTLY NOTHING", 540, 100, WHITE, km)


def ch_galaxy(F, t):
    t0, tl, th, tlap, tfit, tj, tout = (S("Our Sun is just"), S("Light takes a hundred"), S("We live"), S("One lap"),
                                        S("At marble scale, the galaxy"), S("It would stretch"), S("Our model has outgrown"))
    if t < tfit + 0.2:
        z = 1.0 + 0.10 * (t - t0) / max(1.0, tfit - t0)
        rot = -4 * (t - t0) / max(1.0, tfit - t0)
        F.photo("milkyway", zoom=z * 0.95, cx=0.5, cy=0.5, rot=rot, fit="contain")
        F.label("a few hundred billion stars", W / 2, 80, 46, WHITE, ramp(t, t0 + 0.5) * (1 - ramp(t, tl)))
        F.label("100,000 light-years across", W / 2, 80, 52, AMBER, ramp(t, tl + 0.2) * (1 - ramp(t, th)))
        F.label("longer than farming, writing, all of history", W / 2, H - 70, 36, DIM, ramp(t, tl + 2.0) * (1 - ramp(t, th)))
        # you are here, ~halfway out
        kh = ramp(t, th + 0.3)
        if kh > 0:
            scale = min(W / 2400, H / 2589) * z * 0.95
            ang = math.radians(100 + rot)
            rr = 0.27 * 2589 * scale
            x, y = W / 2 + rr * math.cos(ang), H / 2 + rr * math.sin(ang)
            F.draw().ellipse((x - 16, y - 16, x + 16, y + 16), outline=(255, 210, 90, int(255 * kh)), width=4)
            F.label("YOU ARE HERE", x + 160, y + 10, 34, AMBER, kh)
            kl = ramp(t, tlap + 0.2)
            if kl > 0:
                sweep = 360 * sm((t - tlap - 0.2) / 4.0)
                F.draw().arc((W / 2 - rr, H / 2 - rr, W / 2 + rr, H / 2 + rr), 100 + rot, 100 + rot + sweep,
                             fill=(255, 210, 90, int(220 * kl)), width=4)
                F.label("1 lap = 230 million years", W / 2, 80, 48, WHITE, kl)
    else:
        # Solar System top-down: model Milky Way spans Sun -> Jupiter
        u = eo((t - tfit - 0.2) / 1.6)
        F.stars(0.5 * u)
        ppa = 1500 / 5.2
        sx, sy = 230, 560
        dr = F.draw()
        for au, nm in ((1.0, "Earth"), (1.52, "Mars"), (5.2, "Jupiter")):
            r = au * ppa
            dr.ellipse((sx - r, sy - r, sx + r, sy + r), outline=(150, 175, 220, int(170 * u)), width=2)
            F.label(nm, sx + r, sy - 30, 30, DIM, u)
        F.planet("sun", sx, sy, 18, u, halo=0.8 * u, halo_col=(255, 170, 70))
        kg = ramp(t, tj + 0.3)
        gd = 4.96 * ppa
        F.photo("milkyway", zoom=1.0, alpha=0.9 * kg, fit="contain",
                box=(int(sx), int(sy - gd / 2 * 2589 / 2400), int(sx + gd), int(sy + gd / 2 * 2589 / 2400)))
        F.label("our model Milky Way", sx + gd / 2, 120, 52, AMBER, kg)
        F.label("as wide as the Sun-to-Jupiter distance", sx + gd / 2, 185, 36, WHITE, kg)
        F.label("too big for Earth. Now it needs the Solar System.", W / 2, H - 70, 40, CYAN, ramp(t, tout + 0.3))


def ch_andromeda(F, t):
    t0, td, tm, tp, tv, te, tsp, tmg = (S("And the Milky Way isn't"), S("Andromeda, our"), S("In our model, that's"),
                                        S("Three times"), S("And here's the strange"), S("It's the most"),
                                        S("The light you'd see"), S("And it's coming"))
    if t < tm or (t >= te and t < tmg):
        tt = t - (t0 if t < tm else te)
        F.photo("andromeda", zoom=1.0 + 0.03 * tt, cx=0.5, cy=0.5, rot=-30 + 0.6 * tt)
        F.label("ANDROMEDA", W / 2, 80, 56, WHITE, ramp(t, td + 0.2) * (1 - ramp(t, tm)) if t < tm else 0)
        F.label("2.5 million light-years away", W / 2, 150, 44, AMBER, ramp(t, td + 1.0) * (1 - ramp(t, tm)) if t < tm else 0)
        if t >= te:
            F.label("visible to the naked eye", W / 2, 90, 50, WHITE, ramp(t, te + 0.2))
            F.label("that light left before our species existed", W / 2, H - 80, 40, CYAN, ramp(t, tsp + 0.2))
    elif t < te:
        u = ramp(t, tm, 0.8)
        F.stars(0.5)
        ppa = 1640 / 185
        x0, y = 120, 560
        F.line((x0, y, W, y), (120, 140, 180), 2, u)
        F.planet("sun", x0, y, 24, u, halo=0.8 * u, halo_col=(255, 170, 70))
        F.label("SUN", x0, y + 60, 30, AMBER, u)
        xpl = x0 + 39.5 * ppa
        F.draw().ellipse((xpl - 5, y - 5, xpl + 5, y + 5), fill=(220, 200, 180, int(255 * u)))
        F.label("Pluto  ·  40 AU", xpl, y - 50, 30, DIM, u)
        xa = x0 + 126 * ppa
        ka = ramp(t, tm + 0.6)
        F.paste(andromeda_thumb(), xa, y - 150, ka)
        F.line((xa, y - 80, xa, y), (200, 220, 255), 2, ka)
        F.label("model Andromeda  ·  125 AU", xa, y + 70, 40, AMBER, ka)
        kp = ramp(t, tp + 0.2)
        if kp > 0:
            F.dashed(x0, y + 140, xpl, y + 140, (220, 200, 180), 3, alpha=kp)
            F.dashed(x0, y + 175, xa, y + 175, (255, 200, 120), 3, alpha=kp)
            F.label("3× farther than Pluto", (x0 + xa) / 2, y + 230, 40, WHITE, kp)
        kv = ramp(t, tv + 1.2)
        if kv > 0:
            xv = x0 + 173 * ppa
            F.draw().ellipse((xv - 6, y - 6, xv + 6, y + 6), fill=(255, 255, 255, int(255 * kv)))
            F.paste(voyager_img().resize((150, 137)), xv, y - 130, kv)
            F.label("real Voyager 1  ·  173 AU", xv - 80, y + 70, 34, WHITE, kv)
            F.label("closer than Voyager really is", W / 2, 150, 54, GREEN, kv)
    else:
        u = sm((t - tmg - 0.2) / max(2.0, (TL["beats"][-1]["end"] - tmg) * 0.0 + 4.5))
        F.stars(0.4)
        d = lerp(780, 380, u)
        F.paste(galaxy_thumb("milkyway", 700), lerp(400, 760, u), 560, 1.0)
        F.paste(galaxy_thumb("andromeda", 760), lerp(1500, 1160, u), 520, 1.0)
        F.label("4–5 billion years: they merge", W / 2, 90, 50, WHITE, ramp(t, tmg + 0.6))


@lru_cache(maxsize=4)
def galaxy_thumb(name, size):
    p = assets().photo[name].copy()
    p.thumbnail((size, size), Image.LANCZOS)
    a = np.asarray(p.convert("RGB")).astype(np.float32)
    alpha = np.clip((a.max(axis=2) - 14) * 4, 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([a.astype(np.uint8), alpha]), "RGBA")


@lru_cache(maxsize=1)
def andromeda_thumb():
    return galaxy_thumb("andromeda", 260)


NEAR_STARS = [("Proxima", 4.24, 20), ("Sirius", 8.6, 140), ("Procyon", 11.5, 200), ("Altair", 16.7, 300),
              ("Vega", 25.0, 60), ("Pollux", 33.8, 230), ("Arcturus", 36.7, 330), ("Aldebaran", 65.0, 110)]


def ch_universe(F, t):
    t0, th, tg, tf, tb, tm, tlt, tbe = (S("Now, zoom out"), S("This is one tiny"), S("Hubble stared"), S("The light from the faintest"),
                                        S("The observable universe holds"), S("Build that"), S("Light itself"), S("And that's only"))
    if t < tm:
        z = lerp_log(9.0, 1.0, eo((t - t0) / 6.0))
        F.photo("udf", zoom=z, cx=0.55, cy=0.45)
        F.label("Hubble Ultra Deep Field", W / 2, 70, 44, WHITE, ramp(t, th + 0.3) * (1 - ramp(t, tg)))
        F.label("almost every dot is a galaxy", W / 2, H - 70, 44, AMBER, ramp(t, th + 2.5) * (1 - ramp(t, tg)))
        F.label("a grain of sand at arm's length  ·  11+ days of exposure", W / 2, 70, 38, WHITE, ramp(t, tg + 0.3) * (1 - ramp(t, tf)))
        kf = ramp(t, tf + 0.3) * (1 - ramp(t, tb))
        if kf > 0:
            x, y = 1270, 700
            F.draw().ellipse((x - 40, y - 40, x + 40, y + 40), outline=(255, 120, 90, int(255 * kf)), width=4)
            F.label("light left 13 billion years ago", x, y + 80, 36, (255, 170, 140), kf)
        kb = ramp(t, tb + 0.3)
        F.big_text("93 BILLION LIGHT-YEARS", 540, 96, WHITE, kb)
        F.label("hundreds of billions of galaxies", W / 2, 640, 44, AMBER, kb)
    else:
        F.stars(0.45, zoom=1.2)
        u = ramp(t, tm, 1.0)
        zoom_u = 1 + 0.12 * sm((t - tm) / max(1.0, tbe - tm))
        cx, cy, R = 960, 560, 420 * zoom_u
        ppl = R / 36.5
        spin = 6.0 * (t - tm)  # degrees: slow rotation of the neighbourhood
        dr = F.draw()
        dr.ellipse((cx - R, cy - R, cx + R, cy + R), outline=(255, 200, 120, int(230 * u)), width=4,
                   fill=(255, 190, 110, int(18 * u)))
        F.planet("sun", cx, cy, 14, u, halo=0.8 * u, halo_col=(255, 180, 80))
        F.label("Sun", cx, cy + 34, 30, AMBER, u)
        for nm, ly, ang in NEAR_STARS:
            a = math.radians(ang + spin)
            x, y = cx + ly * ppl * math.cos(a), cy + ly * ppl * math.sin(a)
            if 0 < x < W and 0 < y < H:
                F.paste(halo_img(12, (220, 230, 255)), x, y, u)
                F.label(nm, x, y - 24, 30, DIM, u)
        F.label("our model universe: 73 light-years across", W / 2, 70, 50, AMBER, ramp(t, tm + 0.5))
        kl = ramp(t, tlt + 0.2) * (1 - ramp(t, tbe))
        if kl > 0:
            x = sm((t - tlt - 0.3) / 3.0)
            F.line((cx - R, cy, cx + R, cy), (255, 245, 210), 2, 0.5 * kl)
            F.pulse(lerp(cx - R, cx + R, x), cy, kl)
            F.label(f"light: {int(73 * x)} years", W / 2, H - 70, 50, (255, 245, 210), kl)
        kbe = ramp(t, tbe + 0.3)
        if kbe > 0:
            F.dashed(cx - R - 60, cy, 0, cy, DIM, 2, alpha=kbe)
            F.dashed(cx + R + 60, cy, W, cy, DIM, 2, alpha=kbe)
            F.label("…and beyond, we can't see", W / 2, H - 70, 44, DIM, kbe)


def ch_end(F, t):
    t0, tm, tp, tu = (S("A model so big"), S("And somewhere in"), S("Every person"), S("That's us"))
    seq = [("udf", 0.0), ("andromeda", 0.8), ("milkyway", 1.6)]
    if t < t0 + 2.4:
        for name, off in seq:
            k = ramp(t, t0 + off, 0.25) * (1 - ramp(t, t0 + off + 0.8, 0.25))
            if k > 0:
                F.photo(name, zoom=1.6 - 0.5 * (t - t0 - off), alpha=k)
        F.planet("sun", 960, 540, lerp(10, 300, ramp(t, t0 + 2.0, 0.4)), ramp(t, t0 + 2.0, 0.3), halo=0.4)
    else:
        F.stars(0.7, drift=(t * 0.002, 0))
        u = ramp(t, t0 + 2.4, 0.5)
        zoom = ramp(t, tp + 0.2, 4.0)
        d = lerp_log(70, 760, eo(zoom)) if zoom > 0 else 70
        F.planet("earth", 960, lerp(470, 520, zoom), d, u)
        kr = u * (1 - ramp(t, tp))
        if kr > 0:
            F.ruler(925, 995, 540, 70, 1, step_lbl=1, alpha=kr)
            F.label("1 cm", 960, 640, 48, AMBER, kr)
        F.label("THAT'S US.", 960, 980, 64, WHITE, ramp(t, tu + 0.15, 0.4) * (1 - ramp(t, TL["total"] + 6.0, 1.5)))
        ko = ramp(t, TL["total"] + 1.5, 1.0)
        F.label("THRESHOLD PHYSICS", 960, 120, 40, DIM, ko)


CHAPTERS = [ch_marble, ch_moon, ch_sun, ch_planets, ch_star, ch_galaxy, ch_andromeda, ch_universe, ch_end]
BOUNDS = [c[0] for c in CH] + [TOTAL]


def render_frame(t):
    i = max(k for k in range(len(CHAPTERS)) if BOUNDS[k] <= t or k == 0)
    F = Frame()
    CHAPTERS[i](F, t)
    if i > 0 and t < BOUNDS[i] + XFADE:
        P = Frame()
        CHAPTERS[i - 1](P, t)
        k = (t - BOUNDS[i]) / XFADE
        img = Image.blend(P.rgb(), F.rgb(), sm(k))
    else:
        img = F.rgb()
    if t < 0.3:
        img = Image.blend(Image.new("RGB", (W, H)), img, sm(t / 0.3))
    if t > TOTAL - 1.2:
        img = Image.blend(img, Image.new("RGB", (W, H)), sm((t - TOTAL + 1.2) / 1.2))
    return img


def render_segment(args):
    k, f0, f1 = args
    path = os.path.join(SEG_DIR, f"seg_{k:02d}.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                            "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        enc.stdin.write(render_frame(f / FPS).tobytes())
    enc.stdin.close(); enc.wait()
    return path


def main():
    if "--preview" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--preview") + 1:]]
        out = os.path.join(os.environ.get("PREVIEW_DIR", "/tmp"), "lf01_preview.png")
        ims = [render_frame(t).resize((480, 270)) for t in ts]
        cols = 4
        rows = (len(ims) + cols - 1) // cols
        sheet = Image.new("RGB", (480 * cols, 270 * rows))
        for i, im in enumerate(ims):
            sheet.paste(im, ((i % cols) * 480, (i // cols) * 270))
        sheet.save(out); print("preview ->", out)
        return
    from multiprocessing import Pool
    os.makedirs(SEG_DIR, exist_ok=True)
    n = int(round(TOTAL * FPS))
    workers = int(os.getenv("WORKERS", "7"))
    per = -(-n // (workers * 3))
    jobs = [(k, f0, min(n, f0 + per)) for k, f0 in enumerate(range(0, n, per))]
    print(f"{n} frames, {len(jobs)} segments, {workers} workers, total {TOTAL:.1f}s")
    with Pool(workers) as pool:
        paths = []
        for p in pool.imap(render_segment, jobs):
            paths.append(p); print("  ✅", os.path.basename(p), flush=True)
    lst = os.path.join(SEG_DIR, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in paths)
    out = os.path.join(ROOT, "temp_clips", "lf01_universe_scale_silent.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
    print("silent ->", out)


if __name__ == "__main__":
    main()
