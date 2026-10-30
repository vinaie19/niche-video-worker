"""
ep25 Short: "Zoom Out From Earth to the Edge of the Universe" (9:16, ~22 s, $0 local).

Format modelled on the most-viewed space Shorts (one continuous, satisfying camera move, e.g.
"The most satisfying zoom", 13M views): a single true-scale zoom from Earth to a field of
galaxies, with each step named and its distance given as light-travel time.

Every object sits at its real size and position (km) in one 2D world: Earth at the origin,
the Moon, the Sun and planets on their orbits, nearby stars, the Milky Way (Sun ~26,000 ly
from the centre), Andromeda 2.5 Mly away, and the Hubble Ultra Deep Field as the far
background. The camera's view width V (km across the frame) is interpolated in log space
between beat keyframes, so the motion never stops. All imagery is public domain.

  python longform/short_zoom_out.py   ->  final_videos/sci_ep25_zoom_out_complete.mp4
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
os.environ.setdefault("CHANNEL", "b")

import lf01_render as R  # noqa: E402  (drawing primitives + the lf01 asset set)
from audio_post import (_probe_duration, create_phrase_subtitles, generate_ambient_bed,  # noqa: E402
                        generate_voiceover, mux_video_audio_subs, shift_srt_file)

VID = "sci_ep25_zoom_out"
W, H, FPS = 1080, 1920, 30
R.W, R.H = W, H
WORK = os.path.join(ROOT, "temp_clips", f"{VID}_audio")
OUT = os.path.join(ROOT, "final_videos", f"{VID}_complete.mp4")
STEM = f"{VID}_complete_voice"
VO_DELAY = 0.1
FX, FY = W / 2, 1090  # zoom focus on screen: below the mid-frame captions, above the Shorts UI

LY = 9.4607e12
AU = 1.496e8
BEATS = [
    dict(text="This is how small we really are.", phrases=["This is how small", "we really are."], rate="+4%", pause_ms=150),
    # Commas, not full stops: Edge-TTS leaves ~1 s of dead air after a full stop.
    dict(text="The Moon, light gets there in about a second.", caption_text="The Moon, light gets there in about 1 second.",
         phrases=["The Moon,", "light gets there in about 1 second."], rate="+4%", pause_ms=150),
    dict(text="The Sun, eight minutes for light.", caption_text="The Sun, 8 minutes for light.",
         phrases=["The Sun,", "8 minutes for light."], rate="+4%", pause_ms=150),
    dict(text="Every planet, four hours.", caption_text="Every planet, 4 hours.",
         phrases=["Every planet,", "4 hours."], rate="+4%", pause_ms=150),
    dict(text="The nearest star, four years.", caption_text="The nearest star, 4 years.",
         phrases=["The nearest star,", "4 years."], rate="+4%", pause_ms=150),
    dict(text="Our galaxy, a hundred thousand years.", caption_text="Our galaxy, 100,000 years.",
         phrases=["Our galaxy,", "100,000 years."], rate="+4%", pause_ms=150),
    dict(text="Andromeda, two and a half million years.", caption_text="Andromeda, 2.5 million years.",
         phrases=["Andromeda,", "2.5 million years."], rate="+4%", pause_ms=150),
    dict(text="And almost every dot here is a galaxy.", phrases=["And almost every dot", "here is a galaxy."],
         rate="+2%", pause_ms=150),
    dict(text="One of them is home.", phrases=["One of them", "is home."], rate="+0%", pause_ms=0),
]
# On-screen light-time label per beat (index-aligned), shown at the top.
LIGHT = [None, "light: 1.3 seconds", "light: 8 minutes", "light: 4 hours", "light: 4.2 years",
         "light: 100,000 years", "light: 2.5 million years", None, None]
# View width (km across the 1080 px frame) at the start of each beat, then at the end.
V_KEYS = [2.3e4, 1.3e6, 4.5e8, 1.4e10, 1.6e14, 6.0e17, 3.0e19, 2.0e20, 5.0e20, 1.1e21]

# ---- the world (km, y up) ---------------------------------------------------------------
def pol(r, deg, origin=(0.0, 0.0)):
    return (origin[0] + r * math.cos(math.radians(deg)), origin[1] + r * math.sin(math.radians(deg)))


EARTH = (0.0, 0.0)
MOON = pol(384400, 35)
SUN = pol(AU, 200)
PLANETS = [("mercury", 0.387, 4879, 40), ("venus", 0.723, 12104, 130), ("mars", 1.524, 6779, 300),
           ("jupiter", 5.204, 139820, 75), ("saturn", 9.58, 116460, 160), ("uranus", 19.2, 50724, 250),
           ("neptune", 30.07, 49244, 340)]
GC = pol(26000 * LY, 75, SUN)       # galactic centre
MW_D = 100000 * LY                  # disc diameter
ANDRO = pol(2.537e6 * LY, 20, GC)
ANDRO_D = 220000 * LY
LG = ((GC[0] + ANDRO[0]) / 2, (GC[1] + ANDRO[1]) / 2)
rng = np.random.default_rng(12)
# ~0.004 stars per cubic light-year near the Sun -> ~3,600 within 60 ly (projected onto the
# plane), plus a sparser halo out to 600 ly so the field doesn't end abruptly.
NEAR = [("Proxima Centauri", 4.24, 60), ("Sirius", 8.6, 150), ("Barnard's Star", 5.96, 300)]


def focus(V):
    """World point at the screen focus, blended by zoom level (log V)."""
    lv = math.log10(V)
    def b(a, z0, z1):
        return R.sm((lv - z0) / (z1 - z0))
    x, y = EARTH
    k = b(0, 6.6, 9.3); x, y = x + (SUN[0] - x) * k, y + (SUN[1] - y) * k
    k = b(0, 17.3, 18.1); x, y = x + (GC[0] - x) * k, y + (GC[1] - y) * k
    k = b(0, 19.0, 19.9); x, y = x + (LG[0] - x) * k, y + (LG[1] - y) * k
    return x, y


def view(t, st, total):
    starts = [a for a, _ in st] + [total]
    for i in range(len(starts) - 1):
        if t <= starts[i + 1] or i == len(starts) - 2:
            u = min(1.0, max(0.0, (t - starts[i]) / max(1e-6, starts[i + 1] - starts[i])))
            u = 0.55 * u + 0.45 * R.sm(u)  # keep moving: mostly linear, a little ease
            return R.lerp_log(V_KEYS[i], V_KEYS[i + 1], u), i
    return V_KEYS[-1], len(starts) - 2


def place_photo(F, name, wx, wy, w_km, V, f, alpha=1.0, rot=0.0):
    """Draw a photo centred at world (wx, wy) with real width w_km."""
    p = R.assets().photo[name]
    s = (w_km / V * W) / p.width  # screen px per photo px
    if s * p.width < 6 or alpha <= 0.01:
        return
    X = FX + (wx - f[0]) / V * W
    Y = FY - (wy - f[1]) / V * W
    c, sn = math.cos(math.radians(rot)) / s, math.sin(math.radians(rot)) / s
    coeffs = (c, sn, p.width / 2 - c * X - sn * Y, -sn, c, p.height / 2 + sn * X - c * Y)
    layer = p.transform((W, H), Image.AFFINE, coeffs, resample=Image.BICUBIC, fillcolor=(0, 0, 0))
    # key out the black surround so overlapping galaxies blend
    a = np.asarray(layer).astype(np.float32)
    m = np.clip((a.max(axis=2) - 10) * 5, 0, 255) * alpha
    F.im.paste(layer, (0, 0), Image.fromarray(m.astype(np.uint8), "L"))


MAX_D = 3000  # px: never build a sprite bigger than this (a true-scale Sun near Earth is ~65,000 px)


def visible(x, y, d):
    r = d / 2
    return x + r > -50 and x - r < W + 50 and y + r > -50 and y - r < H + 50


def planet(F, name, x, y, d, alpha=1.0, **kw):
    """F.planet with an off-screen skip and a size cap (prevents multi-GB resizes)."""
    if not visible(x, y, d):
        return
    F.planet(name, x, y, min(d, MAX_D), alpha, **kw)


def frame(t, st, total):
    V, bi = view(t, st, total)
    f = focus(V)
    lv = math.log10(V)
    F = R.Frame()
    F.stars(0.75 * (1 - R.sm((lv - 15.5) / 1.5)) + 0.0, drift=(t * 0.003, t * 0.0015))

    def S(wx, wy):
        return FX + (wx - f[0]) / V * W, FY - (wy - f[1]) / V * W

    def px(km):
        return km / V * W

    # far background: the Hubble Ultra Deep Field, zooming out with the camera
    kudf = R.sm((lv - 20.05) / 0.4)
    if kudf > 0:
        F.photo("udf", zoom=R.lerp_log(2.6, 1.0, R.sm((lv - 20.05) / 1.0)), cx=0.5, cy=0.5, alpha=kudf)
    # Andromeda and the Milky Way at true size; a soft glow behind each while it is small on
    # screen, so a true-scale 40-90 px galaxy still reads on a phone.
    for (gx, gy), gd, z0, col in ((ANDRO, ANDRO_D, 18.6, (170, 190, 255)), (GC, MW_D, 17.45, (200, 205, 255))):
        sz = gd / V * W
        kg = R.sm((lv - z0) / 0.4) * (1 - R.sm((sz - 160) / 120)) * (1 - kudf)
        if kg > 0 and sz > 4:
            X, Y = FX + (gx - f[0]) / V * W, FY - (gy - f[1]) / V * W
            F.paste(R.halo_img(int(min(400, sz * 1.6)), col), X, Y, 0.9 * kg)
            if bi == 6:  # Andromeda beat: ring both galaxies so the pair reads at true scale
                rr = max(34, sz * 0.75)
                F.draw().ellipse((X - rr, Y - rr, X + rr, Y + rr), outline=col + (int(220 * kg),), width=3)
    place_photo(F, "andromeda", ANDRO[0], ANDRO[1], ANDRO_D / 0.75, V, f, alpha=R.sm((lv - 18.6) / 0.6) * (1 - 0.6 * kudf), rot=-35)
    place_photo(F, "milkyway", GC[0], GC[1], MW_D / 0.86, V, f, alpha=R.sm((lv - 17.45) / 0.3) * (1 - 0.6 * kudf), rot=10)
    # nearby stars (true distances from the Sun)
    kn = R.sm((lv - 13.2) / 0.6) * (1 - R.sm((lv - 16.4) / 0.5))
    if kn > 0:
        dr = F.draw()
        for name, ly, ang in NEAR:
            x, y = S(*pol(ly * LY, ang, SUN))
            if 0 <= x < W and 0 <= y < H:
                if name:
                    F.paste(R.halo_img(34 if name.startswith("Proxima") else 22, (255, 180, 150)), x, y, kn)
                    dr.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(255, 225, 205, int(255 * kn)))
                else:
                    dr.ellipse((x - 1.2, y - 1.2, x + 1.2, y + 1.2), fill=(230, 235, 255, int(220 * kn)))
    # orbits + planets
    ko = R.sm((lv - 8.2) / 0.6) * (1 - R.sm((lv - 13.6) / 0.8))
    if ko > 0:
        dr = F.draw()
        sx, sy = S(*SUN)
        for name, au, dkm, ang in PLANETS + [("earth", 1.0, 12742, 20)]:
            r = px(au * AU)
            if 2 < r < 6000:
                dr.ellipse((sx - r, sy - r, sx + r, sy + r), outline=(150, 175, 220, int(150 * ko)), width=2)
            if name == "earth":
                continue
            x, y = S(*pol(au * AU, ang, SUN))
            d = max(5, px(dkm))
            if name == "saturn":
                dr.ellipse((x - d / 2, y - d / 2, x + d / 2, y + d / 2), fill=(230, 210, 160, int(255 * ko)))
            else:
                planet(F, name, x, y, d, ko)
    # Sun
    sx, sy = S(*SUN)
    sd = px(1.3927e6)
    ksun = 1 - R.sm((lv - 16.0) / 1.0)
    if ksun > 0:
        planet(F, "sun", sx, sy, max(7, sd), ksun, halo=0.9 * ksun, halo_col=(255, 170, 70))
    # Moon orbit + Moon
    km_ = 1 - R.sm((lv - 8.4) / 0.6)
    if km_ > 0:
        ex, ey = S(*EARTH)
        r = px(384400)
        if r > 3:
            F.draw().ellipse((ex - r, ey - r, ex + r, ey + r), outline=(170, 190, 230, int(140 * km_)), width=2)
        mx, my = S(*MOON)
        planet(F, "moon", mx, my, max(5, px(3474)), km_, halo=0.6 * km_, halo_col=(230, 230, 255))
    # Earth: a photo while big, then a glowing "you are here" dot until the galaxy swallows it
    ex, ey = S(*EARTH)
    ed = px(12742)
    if ed > 6:
        planet(F, "earth", ex, ey, ed)
    else:
        kd = 1 - R.sm((lv - 16.6) / 0.6)
        if kd > 0:
            F.paste(R.halo_img(18, (120, 180, 255)), ex, ey, kd)
            F.draw().ellipse((ex - 3, ey - 3, ex + 3, ey + 3), fill=(170, 210, 255, int(255 * kd)))
    # names (next to their object) and the light-time readout (top)
    names = {1: ("MOON", MOON), 2: ("SUN", SUN), 3: ("NEPTUNE", pol(30.07 * AU, 340, SUN)), 4: ("PROXIMA CENTAURI", pol(4.24 * LY, 60, SUN)),
             5: ("MILKY WAY", GC), 6: ("ANDROMEDA", ANDRO)}
    t0 = st[bi][0]
    if bi in names:
        nm, pos = names[bi]
        x, y = S(*pos)
        k = R.ramp(t, t0 + 0.15, 0.35)
        if -200 < x < W + 200 and 0 < y < H:
            F.label(nm, min(max(x, 190), W - 190), min(max(y - 70, 1300), 1420) if bi >= 5 else y + 70, 40, R.WHITE, k)
    if LIGHT[bi]:
        F.label(LIGHT[bi], W / 2, 170, 66, R.AMBER, R.ramp(t, t0 + 0.2, 0.3))
    if bi == 0:
        F.label("EARTH", W / 2, 170, 66, R.AMBER, R.ramp(t, 0.15, 0.3))
    return F.rgb()


def timeline():
    os.makedirs(WORK, exist_ok=True)
    generate_voiceover(script_beats=BEATS, output_mp3=os.path.join(WORK, f"{STEM}.mp3"), voice="guy",
                       pitch="-1Hz", work_dir=WORK)
    t, st = VO_DELAY, []
    for i, b in enumerate(BEATS, start=1):
        d = _probe_duration(os.path.join(WORK, f"{STEM}_beat{i}.wav"))
        st.append((t, t + d))
        t += d + b["pause_ms"] / 1000.0
    return st, t + 0.05


def main():
    st, total = timeline()
    if "--preview" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--preview") + 1:]] or \
             [s + 0.6 for s, _ in st] + [total - 0.05]
        ims = [frame(x, st, total).resize((216, 384)) for x in ts]
        sheet = Image.new("RGB", (216 * len(ims), 384))
        for i, im in enumerate(ims):
            sheet.paste(im, (216 * i, 0))
        p = os.path.join(os.environ.get("PREVIEW_DIR", "/tmp"), "zoom_preview.png"); sheet.save(p)
        print("preview ->", p, "total", round(total, 2)); return
    n = int(round(total * FPS))
    silent = os.path.join(WORK, f"{VID}_silent.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                            "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    for k in range(n):
        enc.stdin.write(frame(k / FPS, st, total).tobytes())
    enc.stdin.close(); enc.wait()
    srt = os.path.join(WORK, f"{VID}_captions.srt")
    create_phrase_subtitles(BEATS, work_dir=WORK, stem=STEM, srt_path=srt, max_words=5)
    shift_srt_file(srt, int(VO_DELAY * 1000))
    bed = os.path.join(WORK, f"{VID}_ambient.wav")
    generate_ambient_bed(total, bed, preset="space", volume=0.10)
    mix = os.path.join(WORK, f"{VID}_mix.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, f"{STEM}.mp3"), "-i", bed, "-filter_complex",
                    f"[0:a]adelay={int(VO_DELAY*1000)}:all=1,apad[v];[v][1:a]amix=inputs=2:duration=shortest:normalize=0,"
                    f"atrim=0:{total:.3f},loudnorm=I=-14:TP=-1.5:LRA=11[o]", "-map", "[o]", "-ar", "48000", mix], check=True)
    mux_video_audio_subs(silent, mix, srt, OUT, burn_captions=True, caption_style="clean_heavy_safe")
    print(f"✅ {OUT} ({_probe_duration(OUT):.1f}s)")


if __name__ == "__main__":
    main()
