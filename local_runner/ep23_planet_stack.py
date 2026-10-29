"""
ep23 "Every planet fits between Earth and the Moon", rendered entirely on the laptop ($0).

Real public-domain NASA photos (fetch_still_assets.py) of Earth, the Moon and every planet are
placed at true relative scale in a vertical column: Earth at the bottom, the Moon (at apogee)
at the top. Each planet drops in at the moment its name is spoken (Whisper word timings on
the real Edge-TTS voice-over), then a column of 30 Earths measures the distance for the
reveal. The animation is cut at the beat boundaries into temp_clips/{VID}_shot_N.mp4 so the
normal stitch (MISSING_SHOTS_ONLY=1 run_test_batch.py, no pod) adds voice, captions, ambience.

  python ep23_planet_stack.py              # VO -> word timings -> render -> per-beat clips
  python ep23_planet_stack.py --preview    # a few stills to scratch, no video
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("CHANNEL", "b")

VID = "sci_ep23_planets_moon_gap"
ASSETS = os.path.join(HERE, "i2v_stills", VID)
JUPITER_MAP = os.path.join(HERE, "i2v_stills", "sci_ep20_jupiter_star", "jupiter.jpg")
W, H, FPS = 1080, 1920, 24

# Mean diameters (km). Saturn and Jupiter use equatorial widths (that's what the stack lines up).
D = {"earth": 12742, "moon": 3474, "mercury": 4879, "venus": 12104, "mars": 6779,
     "jupiter": 139820, "saturn": 116460, "uranus": 50724, "neptune": 49244}
MOON_APOGEE = 405500  # centre to centre, km
STACK = ["jupiter", "saturn", "uranus", "neptune", "venus", "mars", "mercury"]  # Earth upward

# Overview framing: Earth's bottom at y=1380 (above the captions), the Moon's top at y=120.
EARTH_BOTTOM, MOON_TOP = 1380, 120
WORLD_SPAN = MOON_APOGEE + D["earth"] / 2 + D["moon"] / 2
S0 = (EARTH_BOTTOM - MOON_TOP) / WORLD_SPAN  # px per km at overview
EARTH_Y0 = EARTH_BOTTOM - D["earth"] / 2 * S0  # Earth centre on screen at overview


# ---------- sprites ----------------------------------------------------------------------

def disc_sprite(path, thresh=18):
    """Crop a planet-on-black photo to its disc and return a square RGBA with a round mask."""
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.int32).sum(axis=2)
    ys, xs = np.where(a > thresh * 3)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = max(x1 - x0, y1 - y0) / 2
    box = (int(cx - r), int(cy - r), int(cx + r), int(cy + r))
    sq = im.crop(box).resize((900, 900), Image.LANCZOS)
    mask = Image.new("L", sq.size, 0)
    ImageDraw.Draw(mask).ellipse((2, 2, 897, 897), fill=255)
    out = sq.convert("RGBA")
    out.putalpha(mask.filter(ImageFilter.GaussianBlur(1.5)))
    return out


def jupiter_sprite(size=900):
    """A true round Jupiter from Hubble's PD OPAL map (orthographic, Great Red Spot in view)."""
    from jupiter_globe_shot import GRS_LAT, GRS_LON, LAT_SPAN, bilinear
    tex = np.asarray(Image.open(JUPITER_MAP).convert("RGB"), np.float32)
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    x = (xs - size / 2) / (size / 2); y = -(ys - size / 2) / (size / 2)
    rho2 = x * x + y * y; inside = rho2 < 1
    rho = np.sqrt(np.where(inside, rho2, 0)) + 1e-9
    c = np.arcsin(np.clip(rho, 0, 1)); sc, cc = np.sin(c), np.cos(c)
    lat0, lon0 = 0.0, math.radians(GRS_LON + 25)
    lat = np.arcsin(np.clip(cc * math.sin(lat0) + y * sc * math.cos(lat0) / rho, -1, 1))
    lon = lon0 + np.arctan2(x * sc, rho * cc * math.cos(lat0) - y * sc * math.sin(lat0))
    th, tw, _ = tex.shape
    u = (np.degrees(lon) + 180) / 360 * tw
    v = (LAT_SPAN / 2 - np.degrees(lat)) / LAT_SPAN * th
    col = bilinear(tex, u, v) * (0.35 + 0.65 * np.sqrt(np.clip(1 - rho2, 0, 1))[..., None] ** 0.5) * 1.1
    rgba = np.zeros((size, size, 4), np.uint8)
    rgba[..., :3] = np.clip(col, 0, 255)
    rgba[..., 3] = np.where(inside, 255, 0)
    return Image.fromarray(rgba)


def saturn_sprite():
    """Cassini Saturn with rings, black keyed to alpha. Returns (sprite, body_width_px)."""
    im = Image.open(os.path.join(ASSETS, "saturn.jpg")).convert("RGB")
    w, h = im.size
    # Body centre/half-width measured for ep21 (fill_earths_shot.py); rings span ~0.81 w.
    crop = im.crop((int(0.08 * w), int(0.15 * h), int(0.92 * w), int(0.95 * h)))
    a = np.asarray(crop).astype(np.float32)
    lum = a.max(axis=2)
    alpha = np.clip((lum - 10) * 6, 0, 255).astype(np.uint8)
    rgba = np.dstack([a.astype(np.uint8), alpha])
    sprite = Image.fromarray(rgba, "RGBA")
    body_w = 2 * 0.1725 * w  # px in the source photo
    scale = 900 / body_w
    sprite = sprite.resize((int(sprite.width * scale), int(sprite.height * scale)), Image.LANCZOS)
    # body centre inside the sprite (fractions), for placement
    bcx = (0.4875 * w - 0.08 * w) * scale / sprite.width
    bcy = (0.555 * h - 0.15 * h) * scale / sprite.height
    return sprite, (bcx, bcy)


class Sprites:
    def __init__(self):
        self.base = {n: disc_sprite(os.path.join(ASSETS, f"{n}.jpg"))
                     for n in ["earth", "moon", "mercury", "venus", "mars", "uranus", "neptune"]}
        self.base["jupiter"] = jupiter_sprite()
        self.saturn, self.saturn_c = saturn_sprite()
        self.cache = {}

    def get(self, name, d_px):
        """Sprite scaled so the planet's (body) diameter is d_px; returns (img, cx_frac, cy_frac)."""
        d = max(3, int(round(d_px)))
        key = (name, d)
        if key not in self.cache:
            if name == "saturn":
                s = d / 900
                img = self.saturn.resize((max(3, int(self.saturn.width * s)), max(3, int(self.saturn.height * s))),
                                         Image.LANCZOS)
                self.cache[key] = (img, *self.saturn_c)
            else:
                self.cache[key] = (self.base[name].resize((d, d), Image.LANCZOS), 0.5, 0.5)
        return self.cache[key]


# ---------- timing -----------------------------------------------------------------------

def voice_timeline():
    """Generate the beat VO exactly as the stitch will, return (targets, word_times)."""
    import science_prompts as sp
    from audio_post import beat_shot_durations_s, generate_voiceover, normalize_script_beats
    import whisper

    job = next(j for j in sp.science_ltx_jobs if j["video_id"] == VID)
    work = os.path.join(HERE, "temp_clips", f"{VID}_audio")
    os.makedirs(work, exist_ok=True)
    stem = f"{VID}_complete_voice"
    beats = job["script_beats"]
    generate_voiceover(script_beats=beats, output_mp3=os.path.join(work, f"{stem}.mp3"),
                       voice=job.get("voice"), rate=job.get("voice_rate"), pitch=job.get("voice_pitch"),
                       work_dir=work)
    vo_delay = int(job.get("vo_delay_ms", 100))
    targets = beat_shot_durations_s(beats, work, stem, vo_delay_ms=vo_delay,
                                    default_rate=job.get("voice_rate"), default_pitch=job.get("voice_pitch"))
    model = whisper.load_model(os.getenv("WHISPER_MODEL", "base"))
    words, t = [], vo_delay / 1000.0
    for i, b in enumerate(normalize_script_beats(script_beats=beats), start=1):
        wav = os.path.join(work, f"{stem}_beat{i}.wav")
        res = model.transcribe(wav, word_timestamps=True, language="en")
        for seg in res.get("segments") or []:
            for w in seg["words"]:
                words.append((t + float(w["start"]), w["word"].strip().lower().strip(",.!?")))
        t = sum(targets[:i])
    return targets, words


def word_time(words, token, after=0.0, default=None, before=1e9, exact=False):
    for t, w in words:
        if after <= t <= before and (w == token if exact else token in w):
            return t
    return default


# ---------- drawing ----------------------------------------------------------------------

def ease_out(t):
    return 1 - (1 - t) ** 3


def ease_in(t):
    return t * t


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def stars(seed=21):
    rng = np.random.default_rng(seed)
    n = 900
    return rng.uniform(0, W, n), rng.uniform(-H, 2 * H, n), rng.random(n) ** 3 * 200 + 30


def render(targets, words, out_dir, preview_times=None):
    spr = Sprites()
    total = sum(targets)
    bounds = np.cumsum(targets)
    sx, sy, sb = stars()

    # World y (km, upward from Earth centre) of each stacked planet's centre.
    slot, y = {}, D["earth"] / 2
    for n in STACK:
        slot[n] = y + D[n] / 2
        y += D[n]
    top_of_stack = y
    moon_y = MOON_APOGEE

    # Event times from the voice-over.
    b1, b2, b3, b4 = bounds[0], bounds[1], bounds[2], bounds[3]
    drop = {
        "jupiter": word_time(words, "jupiter", b1 - 0.2, b1 + 0.2),
        "saturn": word_time(words, "saturn", b2 - 0.2, b2 + 0.1),
        "uranus": word_time(words, "uran", b2 - 0.2, b2 + 0.6),
        "neptune": word_time(words, "neptun", b2 - 0.2, b2 + 1.1),
        "venus": word_time(words, "venus", b3 - 0.2, b3 + 0.1),
        "mars": word_time(words, "mars", b3 - 0.2, b3 + 0.5),
        "mercury": word_time(words, "mercury", b3 - 0.2, b3 + 1.0),
    }
    fall = {"jupiter": 0.55, "saturn": 0.45, "uranus": 0.38, "neptune": 0.38,
            "venus": 0.32, "mars": 0.32, "mercury": 0.32}
    fit_t = word_time(words, "fit", b3 + 0.5, b4 - 0.5, before=b4, exact=True)
    thirty_t = word_time(words, "thirty", b4 - 0.2, word_time(words, "30", b4 - 0.2, b4 + 0.8))
    yes_t = word_time(words, "yes", b4 + 0.5, b4 + 2.5)
    print("events:", {k: round(v, 2) for k, v in drop.items()}, "fit", round(fit_t, 2),
          "thirty", round(thirty_t, 2), "yes", round(yes_t, 2))

    mid = WORLD_SPAN / 2 - D["earth"] / 2
    yc_over = EARTH_Y0 - mid * S0
    # Beat 1 camera ride: big Earth -> whoosh up the gap -> Moon close-up -> zoom out to reveal.
    # Moves from frame 0: drift in on Earth while starting to rise, then the whoosh.
    keys = [(0.00, 11.0, -900.0, 1060.0), (0.20 * b1, 15.0, 2500.0, 1000.0),
            (0.55 * b1, 14.0, moon_y, 700.0), (0.70 * b1, 14.0, moon_y, 700.0),
            (1.00 * b1, 1.0, mid, yc_over)]

    def camera(t):
        """(zoom, world y at screen focus, screen focus y, shake x)."""
        if t < b1:
            for (t0, z0, y0, c0), (t1, z1, y1, c1) in zip(keys, keys[1:]):
                if t <= t1:
                    u = smooth((t - t0) / max(1e-6, t1 - t0))
                    z = math.exp(math.log(z0) + (math.log(z1) - math.log(z0)) * u)
                    yf, yc = y0 + (y1 - y0) * u, c0 + (c1 - c0) * u
                    break
        else:
            # slow continuous push so the stack never sits still
            z = 1.0 + 0.07 * smooth((t - b1) / max(1.0, total - b1))
            yf, yc = mid, yc_over
        shake = 0.0
        for n, t0 in drop.items():
            land = t0 + fall[n]
            if land <= t < land + 0.35:
                k = 1 - (t - land) / 0.35
                shake += (14 if n in ("jupiter", "saturn") else 5) * k * math.sin((t - land) * 70)
        return z, yf, yc, shake

    def to_screen(wx_px, wy, z, yf, yc):
        return W / 2 + wx_px * z, yc - (wy - yf) * S0 * z

    def paste(frame, name, wy, z, yf, yc, shake, xoff_px=0.0, glow=0.0, flash=0.0):
        d_px = D[name] * S0 * z
        img, fx, fy = spr.get(name, d_px)
        X, Y = to_screen(xoff_px, wy, z, yf, yc)
        X += shake
        if glow > 0:
            g = Image.new("RGBA", (int(d_px * 4) + 40, int(d_px * 4) + 40), (0, 0, 0, 0))
            pad = g.width / 2 - d_px * 1.1
            ImageDraw.Draw(g).ellipse((pad, pad, g.width - pad, g.height - pad), fill=(255, 220, 160, int(110 * min(1.0, glow))))
            g = g.filter(ImageFilter.GaussianBlur(float(max(2.0, d_px * 0.25))))
            frame.alpha_composite(g, (int(X - g.width / 2), int(Y - g.height / 2)))
        if flash > 0:
            white = Image.new("RGBA", img.size, (255, 255, 255, 0))
            white.putalpha(img.getchannel("A").point(lambda a: int(a * flash)))
            img = Image.alpha_composite(img, white)
        x0, y0 = int(X - fx * img.width), int(Y - fy * img.height)
        if x0 > W or y0 > H or x0 + img.width < 0 or y0 + img.height < 0:
            return
        frame.alpha_composite(img, (x0, y0)) if x0 >= 0 and y0 >= 0 and x0 + img.width <= W and y0 + img.height <= H \
            else _paste_clipped(frame, img, x0, y0)

    def frame_at(t):
        z, yf, yc, shake = camera(t)
        f = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        # stars with slight parallax against the camera move
        arr = np.asarray(f).copy()
        par = 0.15
        px = (sx - W / 2) * (1 + (z - 1) * par) + W / 2
        py = (sy - yc) * (1 + (z - 1) * par) + yc - (yf * S0 * par) % H
        ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)
        arr[py[ok].astype(int), px[ok].astype(int), :3] = sb[ok, None].astype(np.uint8)
        f = Image.fromarray(arr, "RGBA")
        # Earth and Moon (Moon gets a halo so the 11px disc reads at overview)
        paste(f, "earth", 0, z, yf, yc, shake)
        mg = 0.8 + 0.2 * math.sin(t * 3)
        paste(f, "moon", moon_y, z, yf, yc, shake, glow=1.6 * mg)
        # Dashed Earth-Moon line, anchored in world space so it streams past during the
        # beat-1 camera ride (speed cue) and then marks the empty gap.
        step = 34 / S0  # km between dashes (34 px at overview)
        ln = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(ln)
        y_lo, y_hi = D["earth"] / 2, moon_y - D["moon"] / 2
        k0 = max(0, int((yf - (H / (S0 * z))) / step) - 1)
        k1 = int((yf + (H / (S0 * z))) / step) + 2
        for kk in range(k0, k1):
            wa = y_lo + kk * step
            wb = min(wa + 18 / S0, y_hi)
            if wa >= y_hi:
                break
            _, ya = to_screen(0, wa, z, yf, yc)
            _, yb = to_screen(0, wb, z, yf, yc)
            if max(ya, yb) < 0 or min(ya, yb) > H:
                continue
            dl.line((W / 2 + shake, ya, W / 2 + shake, yb), fill=(170, 200, 255, 160), width=int(min(10, 3 * z ** 0.5)))
        f.alpha_composite(ln)
        # Leftover gap bracket on "they all fit"
        if t >= fit_t:
            k = smooth((t - fit_t) / 0.4) * (0.75 + 0.25 * math.sin((t - fit_t) * 6))
            _, ya = to_screen(0, top_of_stack, z, yf, yc)
            _, yb = to_screen(0, moon_y - D["moon"] / 2, z, yf, yc)
            band = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(band)
            for yy in (ya, yb):
                dr.line((W / 2 - 110, yy, W / 2 + 110, yy), fill=(150, 255, 190, int(255 * k)), width=4)
            dr.line((W / 2 + 120, yb, W / 2 + 120, ya), fill=(150, 255, 190, int(200 * k)), width=3)
            glow_l = band.filter(ImageFilter.GaussianBlur(6))
            f.alpha_composite(glow_l); f.alpha_composite(band)
        # Planets falling in and stacking
        for n in STACK:
            t0 = drop[n]
            if t < t0:
                continue
            u = min(1.0, (t - t0) / fall[n])
            start_y = moon_y + 140000  # from above the top of frame
            wy = start_y + (slot[n] - start_y) * ease_in(u)
            flash = 0.0
            if t >= yes_t:
                flash = 0.35 * math.sin(min(1.0, (t - yes_t) / 1.0) * math.pi)
            paste(f, n, wy, z, yf, yc, shake, flash=flash)
        # 30 Earths column on "thirty" (left of the stack), Earth to the Moon
        if t >= thirty_t - 0.15:
            k = min(1.0, (t - thirty_t + 0.15) / 1.1)
            n_show = int(30 * k + 1e-6)
            for i in range(n_show):
                wy = D["earth"] / 2 + D["earth"] * (i + 0.5) * (MOON_APOGEE - D["earth"] / 2 - D["moon"] / 2) \
                     / (30 * D["earth"])
                paste(f, "earth", wy, z, yf, yc, shake, xoff_px=-400)
        return f.convert("RGB")

    if preview_times:
        return [frame_at(t) for t in preview_times]

    os.makedirs(out_dir, exist_ok=True)
    start = 0.0
    for i, dur in enumerate(targets, start=1):
        n = int(round(dur * FPS))
        path = os.path.join(out_dir, f"{VID}_shot_{i}.mp4")
        enc = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
             "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
             "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
        for k in range(n):
            enc.stdin.write(np.asarray(frame_at(start + k / FPS)).tobytes())
        enc.stdin.close(); enc.wait()
        print(f"✅ shot {i}: {n} frames ({dur:.2f}s) -> {path}")
        start += n / FPS


def _paste_clipped(frame, img, x0, y0):
    bx0, by0 = max(0, -x0), max(0, -y0)
    bx1, by1 = min(img.width, W - x0), min(img.height, H - y0)
    if bx1 <= bx0 or by1 <= by0:
        return
    frame.alpha_composite(img.crop((bx0, by0, bx1, by1)), (x0 + bx0, y0 + by0))


if __name__ == "__main__":
    targets, words = voice_timeline()
    print("targets:", [round(x, 2) for x in targets], "total", round(sum(targets), 2))
    if "--preview" in sys.argv:
        b = np.cumsum(targets)
        times = [0.05, b[0] * 0.5, b[0] + 0.9, b[1] + 1.2, b[2] + 1.6, b[3] - 0.2, b[3] + 1.6, b[4] - 0.1]
        ims = render(targets, words, None, preview_times=times)
        strip = Image.new("RGB", (216 * len(ims), 384))
        for i, im in enumerate(ims):
            strip.paste(im.resize((216, 384)), (i * 216, 0))
        out = sys.argv[sys.argv.index("--preview") + 1] if len(sys.argv) > sys.argv.index("--preview") + 1 else "preview.png"
        strip.save(out); print("preview ->", out)
    else:
        render(targets, words, os.path.join(HERE, "temp_clips"))
