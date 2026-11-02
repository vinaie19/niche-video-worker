"""
ep27 Short: "Jupiter's Great Red Spot Is Shrinking" (9:16, ~20 s, $0 local).

Same rules as ep26: full-frame real imagery the whole time (Juno, Voyager 1 and Trouvelot's 1880
drawing, all public domain), a big subject from frame one, constant motion, a whoosh on every
cut, the Andrew voice, and the punchline as the last word.

Numbers: the Great Red Spot is ~16,000 km wide today (~1.3 Earths, Earth = 12,742 km). In the
late 1800s it was ~40,000 km across (~3 Earths). It has been watched continuously since 1831,
and its edge winds reach ~430 km/h. Earths drawn over Trouvelot's plate are scaled to his disk
(Jupiter = 11.2 Earths wide).

  python longform/short_great_red_spot.py   ->  final_videos/sci_ep27_great_red_spot_complete.mp4
"""
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
os.environ.setdefault("CHANNEL", "b")

import lf01_render as R  # noqa: E402
from audio_post import (_probe_duration, create_phrase_subtitles, generate_ambient_bed,  # noqa: E402
                        generate_voiceover, mux_video_audio_subs, shift_srt_file)
from short_zoom_v2 import whoosh_track  # noqa: E402

VID = "sci_ep27_great_red_spot"
W, H, FPS = 1080, 1920, 30
R.W, R.H = W, H
ASSETS = os.path.join(ROOT, "i2v_stills", VID)
WORK = os.path.join(ROOT, "temp_clips", f"{VID}_audio")
OUT = os.path.join(ROOT, "final_videos", f"{VID}_complete.mp4")
STEM = f"{VID}_voice"
VO_DELAY = 0.1
VOICE = "en-US-AndrewMultilingualNeural"
XF = 0.35
SUBJ_Y = 1150  # subject centre on screen: below the mid-frame captions, above the Shorts UI

BEATS = [
    dict(text="There's a storm on Jupiter bigger than the entire Earth.",
         phrases=["There's a storm on Jupiter", "bigger than the entire Earth."], rate="+6%", pause_ms=120),
    dict(text="It's been raging for almost two hundred years.", caption_text="It's been raging for almost 200 years.",
         phrases=["It's been raging", "for almost 200 years."], rate="+6%", pause_ms=120),
    dict(text="Its winds hit over four hundred kilometres an hour.",
         caption_text="Its winds hit over 400 km an hour.",
         phrases=["Its winds hit", "over 400 km an hour."], rate="+6%", pause_ms=120),
    dict(text="In the eighteen-eighties, it was wide enough to swallow three Earths.",
         caption_text="In the 1880s, it was wide enough to swallow 3 Earths.",
         phrases=["In the 1880s,", "it was wide enough", "to swallow 3 Earths."], rate="+4%", pause_ms=150),
    dict(text="Today? It barely fits one.", phrases=["Today?", "It barely fits one."], rate="+0%", pause_ms=150),
    dict(text="The biggest storm in the solar system is shrinking, and nobody knows if it will survive.",
         phrases=["The biggest storm", "in the solar system", "is shrinking,", "and nobody knows",
                  "if it will survive."], rate="+4%", pause_ms=0),
]
TOP = ["BIGGER THAN EARTH", "~200 YEARS OLD", "400+ km/h WINDS", "1880s: 3 EARTHS", "TODAY: 1.3 EARTHS", ""]

# Spot geometry measured on each image (photo fractions): centre and width.
JUNO_SPOT = (0.545, 0.45, 0.79, 0.35)    # cx, cy, w, h of the oval
VOY_SPOT = (0.51, 0.27)
TROU_SPOT = ((0.55 - 0.07) / 0.91, (0.40 - 0.14) / 0.74)  # in the cropped plate
TROU_DISK = 0.522 / 0.91                  # Jupiter's disk diameter / cropped plate width
JUNO_EARTH = JUNO_SPOT[2] / 1.3           # Earth width in Juno-image widths (spot = 1.3 Earths)

PH, BLUR = {}, {}


def load():
    for n, f in (("juno", "juno.jpg"), ("voyager", "voyager.jpg"), ("trouvelot", "trouvelot.tif")):
        im = Image.open(os.path.join(ASSETS, f)).convert("RGB")
        if n == "trouvelot":  # drop the ruler and the page edges, keep the plate
            im = im.crop((int(im.width * 0.07), int(im.height * 0.14), int(im.width * 0.98), int(im.height * 0.88)))
        PH[n] = im
        k = max(W / im.width, H / im.height) / 8  # full-frame cover copy, blurred and dimmed
        b = im.resize((math.ceil(im.width * k), math.ceil(im.height * k))).filter(ImageFilter.GaussianBlur(6))
        b = b.resize((math.ceil(b.width * 8), math.ceil(b.height * 8)))
        b = b.crop(((b.width - W) // 2, (b.height - H) // 2, (b.width - W) // 2 + W, (b.height - H) // 2 + H))
        BLUR[n] = Image.eval(b, lambda v: int(v * 0.55))
    BLUR["juno"] = Image.new("RGB", (W, H))  # Juno's top is black space: extend it, no blurred band


def photo(F, name, zoom, cx, cy, rot=0.0, ty=SUBJ_Y):
    """Draw photo point (cx, cy) at screen (W/2, ty). zoom is relative to 'cover'. Anything
    outside the photo shows a dimmed, blurred copy instead of black. Returns the scale used."""
    p = PH[name]
    s = max(W / p.width, H / p.height) * zoom
    F.im.paste(BLUR[name], (0, 0))
    c, sn = math.cos(math.radians(rot)) / s, math.sin(math.radians(rot)) / s
    px, py = cx * p.width, cy * p.height
    tx = W / 2
    coeffs = (c, sn, px - c * tx - sn * ty, -sn, c, py + sn * tx - c * ty)
    layer = p.transform((W, H), Image.AFFINE, coeffs, resample=Image.BICUBIC)
    mask = Image.new("L", p.size, 255).transform((W, H), Image.AFFINE, coeffs, resample=Image.BILINEAR)
    if name == "juno":  # feather the photo's edges into the space around it
        mask = mask.filter(ImageFilter.GaussianBlur(28))
    F.im.paste(layer, (0, 0), mask)
    return s


_EARTH = None


def earth(F, x, y, d, alpha=1.0):
    """Earth disc trimmed 6.5% inside its edge: the stock sprite keeps a dark rim that shows on Jupiter."""
    global _EARTH
    if _EARTH is None:
        src = R.assets().disc["earth"]
        m = int(src.width * 0.065)
        e = src.crop((m, m, src.width - m, src.height - m)).convert("RGB")
        mask = Image.new("L", e.size, 0)
        ImageDraw.Draw(mask).ellipse((1, 1, e.width - 2, e.height - 2), fill=255)
        e = e.convert("RGBA"); e.putalpha(mask.filter(ImageFilter.GaussianBlur(1.5)))
        _EARTH = e
    sp = _EARTH.resize((max(2, int(d)), max(2, int(d))), Image.LANCZOS)
    F.paste(sp, x, y, alpha)


def to_screen(name, s, cx, cy, x, y, ty=SUBJ_Y):
    p = PH[name]
    return W / 2 + (x - cx) * p.width * s, ty + (y - cy) * p.height * s


def scene(F, i, u, t):
    sm = R.sm
    if i == 0:  # the comparison is on frame 1 (ep26 lost 76% in the first 2 s): Earth already
        # inside today's spot, camera pushing in so the storm swells past it
        z = R.lerp(0.56, 0.64, sm(u))
        cx, cy = JUNO_SPOT[0], JUNO_SPOT[1]
        s = photo(F, "juno", z, cx, cy)
        d = JUNO_EARTH * PH["juno"].width * s
        earth(F, W / 2, SUBJ_Y, d, alpha=0.9)
    elif i == 1:  # Voyager 1, 1979: push in on the spot with a slow roll
        photo(F, "voyager", R.lerp(1.5, 1.9, u), VOY_SPOT[0], R.lerp(0.33, 0.29, u), rot=R.lerp(-4, 3, u), ty=H / 2)
    elif i == 2:  # into the vortex, spinning
        photo(F, "voyager", R.lerp_log(2.0, 3.2, sm(u)), *VOY_SPOT, rot=R.lerp(3, 28, u), ty=H / 2)
    elif i == 3:  # Trouvelot's 1880 plate: zoom to the spot, three Earths line up across it
        cx, cy = TROU_SPOT
        z = R.lerp_log(1.15, 2.1, sm(min(1, u / 0.6)))
        s = photo(F, "trouvelot", z, cx, cy)
        d = TROU_DISK * PH["trouvelot"].width * s / 11.2  # Earth at the plate's scale
        for k in range(3):
            a = R.ramp(u, 0.25 + 0.1 * k, 0.1)
            if a > 0:
                earth(F, W / 2 + (k - 1) * d * 1.02, SUBJ_Y, d * 0.98, alpha=a)
    elif i == 4:  # back to Juno: the 1880 outline shrinks onto today's spot, one Earth inside
        cx, cy, sw, sh = JUNO_SPOT
        s = photo(F, "juno", 0.62, cx, cy)
        d = JUNO_EARTH * PH["juno"].width * s
        earth(F, W / 2, SUBJ_Y, d, alpha=0.9)
        k = R.lerp(40 / 16, 1.0, sm(min(1, u / 0.7)))
        ew, eh = sw * PH["juno"].width * s * k, sh * PH["juno"].height * s * k
        F.draw().ellipse((W / 2 - ew / 2, SUBJ_Y - eh / 2, W / 2 + ew / 2, SUBJ_Y + eh / 2),
                         outline=R.AMBER + (230,), width=8)
    else:  # slow drift across the whole storm
        photo(F, "juno", R.lerp(0.80, 0.95, u), R.lerp(0.50, 0.58, u), JUNO_SPOT[1], rot=R.lerp(0, -4, u))


def frame(t, st, total):
    i = max(k for k in range(len(st)) if st[k][0] <= t or k == 0)
    s0 = st[i][0]
    s1 = st[i + 1][0] if i + 1 < len(st) else total
    F = R.Frame()
    scene(F, i, min(1.0, (t - s0) / max(0.5, s1 - s0)), t)
    if i > 0 and t < s0 + XF:  # crossfade from the previous scene
        P = R.Frame()
        scene(P, i - 1, 1.0, t)
        F.im = Image.blend(P.rgb(), F.rgb(), R.sm((t - s0) / XF))
    if TOP[i]:
        if i == 0:  # bold claim visible from the very first frame
            F.label(TOP[0], W / 2, 260, 84, R.AMBER, 1.0)
        else:
            F.label(TOP[i], W / 2, 170, 70 if len(TOP[i]) < 18 else 56, R.AMBER, R.ramp(t, s0 + 0.1, 0.3))
    return F.rgb()


def main():
    load()
    os.makedirs(WORK, exist_ok=True)
    generate_voiceover(script_beats=BEATS, output_mp3=os.path.join(WORK, f"{STEM}.mp3"), voice=VOICE,
                       pitch="+0Hz", work_dir=WORK)
    t, st = VO_DELAY, []
    for i, b in enumerate(BEATS, start=1):
        d = _probe_duration(os.path.join(WORK, f"{STEM}_beat{i}.wav"))
        st.append((t, t + d)); t += d + b["pause_ms"] / 1000.0
    total = t + 0.6  # room after the last word: mp3 encode delay + natural decay (ep26 lost its last word at 0.05)
    if "--preview" in sys.argv:
        ts = [0.3, 1.5] + [s + 0.8 for s, _ in st[1:]] + [st[3][0] + 2.5, st[4][0] + 1.5, total - 0.2]
        ims = [frame(x, st, total).resize((216, 384)) for x in sorted(ts)]
        sheet = Image.new("RGB", (216 * len(ims), 384))
        for k, im in enumerate(ims):
            sheet.paste(im, (216 * k, 0))
        p = os.path.join(os.environ.get("PREVIEW_DIR", "/tmp"), "grs_preview.png"); sheet.save(p)
        print("preview ->", p, round(total, 2)); return
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
    bed = os.path.join(WORK, "ambient.wav"); generate_ambient_bed(total, bed, preset="space", volume=0.08)
    wh = os.path.join(WORK, "whoosh.wav"); whoosh_track([s for s, _ in st[1:]], total, wh)
    mix = os.path.join(WORK, "mix.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, f"{STEM}.mp3"), "-i", bed, "-i", wh,
                    "-filter_complex",
                    f"[0:a]adelay={int(VO_DELAY*1000)}:all=1,apad[v];[v][1:a][2:a]amix=inputs=3:duration=shortest:normalize=0,"
                    f"atrim=0:{total:.3f},loudnorm=I=-14:TP=-1.5:LRA=11[o]", "-map", "[o]", "-ar", "48000", mix], check=True)
    mux_video_audio_subs(silent, mix, srt, OUT, burn_captions=True, caption_style="clean_heavy_safe")
    print(f"✅ {OUT} ({_probe_duration(OUT):.1f}s)")


if __name__ == "__main__":
    main()
