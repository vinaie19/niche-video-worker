"""
ep28 Short: "You're Seeing the Sun 8 Minutes Late" (9:16, ~19 s, $0 local).

Rules after ep26 (23.7% stayed, 84% AVD): the claim and a full-frame subject on frame 1, no
build-up, real NASA imagery filling the frame the whole time, a whoosh on every cut, the Andrew
voice, the punchline as the last words, and the last frame matching the first (loop).

A big timer counts the 8 min 20 s (accelerated) from the moment the Sun "vanishes" to the moment
the light runs out, so the viewer always has a clock to wait for.

Physics: 1 AU / c = 499 s = 8 min 19 s. Changes in gravity also travel at c (GW170817), so Earth
keeps orbiting the vanished Sun's position for the same 8 minutes.

  python longform/short_sun_8min.py [--preview]  ->  final_videos/sci_ep28_sun_8min_complete.mp4
"""
import math
import os
import subprocess
import sys

from PIL import Image, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
os.environ.setdefault("CHANNEL", "b")

import lf01_render as R  # noqa: E402
from audio_post import (_probe_duration, create_phrase_subtitles, generate_ambient_bed,  # noqa: E402
                        generate_voiceover, mux_video_audio_subs, shift_srt_file)
from short_zoom_v2 import whoosh_track  # noqa: E402

VID = "sci_ep28_sun_8min"
W, H, FPS = 1080, 1920, 30
R.W, R.H = W, H
STILLS = os.path.join(ROOT, "i2v_stills")
WORK = os.path.join(ROOT, "temp_clips", f"{VID}_audio")
OUT = os.path.join(ROOT, "final_videos", f"{VID}_complete.mp4")
STEM = f"{VID}_voice"
VO_DELAY = 0.05
VOICE = "en-US-AndrewMultilingualNeural"
XF = 0.3
LIGHT_S = 8 * 60 + 20  # the on-screen clock runs to 8:20

BEATS = [
    dict(text="If the Sun vanished right now, you wouldn't even know.",
         phrases=["If the Sun vanished right now,", "you wouldn't even know."], rate="+8%", pause_ms=80),
    dict(text="It would keep shining for eight more minutes,", caption_text="It would keep shining for 8 more minutes,",
         phrases=["It would keep shining", "for 8 more minutes,"], rate="+6%", pause_ms=60),
    dict(text="because its light takes that long to reach us.",
         phrases=["because its light takes", "that long to reach us."], rate="+6%", pause_ms=100),
    dict(text="Even its gravity travels at light speed, so Earth would keep circling... nothing.",
         phrases=["Even its gravity", "travels at light speed,", "so Earth would keep circling...", "nothing."],
         rate="+4%", pause_ms=120),
    dict(text="Then, at eight minutes and twenty seconds, the lights go out.",
         caption_text="Then, at 8 minutes and 20 seconds, the lights go out.",
         phrases=["Then, at 8 minutes", "and 20 seconds,", "the lights go out."], rate="+2%", pause_ms=150),
    dict(text="So the Sun you're looking at isn't the Sun now. It's the Sun eight minutes ago.",
         caption_text="So the Sun you're looking at isn't the Sun now. It's the Sun 8 minutes ago.",
         phrases=["So the Sun you're looking at", "isn't the Sun now.", "It's the Sun", "8 minutes ago."],
         rate="+4%", pause_ms=0),
]
TOP = [("IF THE SUN", "VANISHED..."), None, None, None, None, ("THIS SUN IS", "8 MINUTES OLD")]

PH, BLUR = {}, {}


def load():
    for n, f in (("sun", "sci_ep17_sun_black_hole/sun.jpg"), ("iss", "sci_ep22_sun_white/sun_iss.jpg"),
                 ("clouds", "sci_ep22_sun_white/earth_limb.jpg"), ("earth", "sci_ep17_sun_black_hole/earth.jpg"),
                 ("city", "sci_ep17_sun_black_hole/city.jpg")):
        im = Image.open(os.path.join(STILLS, f)).convert("RGB")
        PH[n] = im
        k = max(W / im.width, H / im.height) / 8  # full-frame cover copy, blurred and dimmed
        b = im.resize((math.ceil(im.width * k), math.ceil(im.height * k))).filter(ImageFilter.GaussianBlur(6))
        b = b.resize((math.ceil(b.width * 8), math.ceil(b.height * 8)))
        b = b.crop(((b.width - W) // 2, (b.height - H) // 2, (b.width - W) // 2 + W, (b.height - H) // 2 + H))
        BLUR[n] = Image.eval(b, lambda v: int(v * 0.55))


def photo(F, name, zoom, cx, cy, rot=0.0, ty=H / 2):
    """Draw photo point (cx, cy) at screen (W/2, ty); zoom is relative to 'cover'. Anything
    outside the photo shows a dimmed, blurred copy instead of black."""
    p = PH[name]
    s = max(W / p.width, H / p.height) * zoom
    F.im.paste(BLUR[name], (0, 0))
    c, sn = math.cos(math.radians(rot)) / s, math.sin(math.radians(rot)) / s
    px, py = cx * p.width, cy * p.height
    tx = W / 2
    coeffs = (c, sn, px - c * tx - sn * ty, -sn, c, py + sn * tx - c * ty)
    layer = p.transform((W, H), Image.AFFINE, coeffs, resample=Image.BICUBIC)
    mask = Image.new("L", p.size, 255).transform((W, H), Image.AFFINE, coeffs, resample=Image.BILINEAR)
    F.im.paste(layer, (0, 0), mask)
    return s


def sun(F, u, z0, z1, r0, r1):
    photo(F, "sun", R.lerp(z0, z1, u), 0.5, 0.5, rot=R.lerp(r0, r1, u))


def scene(F, i, u, t):
    sm = R.sm
    if i == 0:  # the Sun fills the frame: fire edge to edge, slow push
        sun(F, u, 1.00, 1.10, 0, 4)
    elif i == 1:  # sunrise over Earth from the ISS: push into the star
        photo(F, "iss", R.lerp(1.0, 1.35, sm(u)), R.lerp(0.26, 0.21, u), R.lerp(0.42, 0.36, u))
    elif i == 2:  # sunlit clouds from the edge of space, drifting
        photo(F, "clouds", R.lerp(1.15, 1.3, u), R.lerp(0.40, 0.58, u), 0.5)
    elif i == 3:  # the whole Earth, still turning and drifting along its orbit
        photo(F, "earth", R.lerp(0.80, 0.86, u), R.lerp(0.42, 0.58, u), 0.5, rot=R.lerp(-6, 6, u))
    elif i == 4:  # the light runs out: the clouds go dark, then only city lights are left
        if u < 0.45:
            photo(F, "clouds", 1.3, 0.58, 0.5)
            k = 1.0 - 0.85 * sm(u / 0.45)
            F.im = ImageEnhance.Brightness(F.im).enhance(k)
            F.im = Image.blend(F.im, Image.new("RGB", (W, H), (8, 14, 40)), 0.35 * sm(u / 0.45))
        else:
            v = (u - 0.45) / 0.55
            photo(F, "city", R.lerp(1.25, 1.1, sm(v)), 0.62, 0.62)
            F.im = ImageEnhance.Brightness(F.im).enhance(R.lerp(0.4, 1.0, sm(v * 2)))
    else:  # back to the Sun, pulling out to exactly the opening frame (seamless loop)
        sun(F, u, 1.10, 1.00, 4, 0)


def timer_value(t, st):
    """Clock seconds shown at time t: starts with beat 2, hits 8:20 on 'twenty seconds' (beat 5)."""
    t0 = st[1][0]
    t1 = st[4][0] + 0.55 * (st[4][1] - st[4][0])
    if t < t0:
        return None
    x = min(1.0, (t - t0) / (t1 - t0))
    return int(round(LIGHT_S * x ** 1.15))


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
    if TOP[i]:  # the claim is on screen from frame 0, no fade
        a = 1.0 if i == 0 else R.ramp(t, s0, 0.25)
        F.label(TOP[i][0], W / 2, 210, 96, (255, 255, 255), a)
        F.label(TOP[i][1], W / 2, 330, 92, R.AMBER, a)
    v = timer_value(t, st)
    if v is not None and i in (1, 2, 3, 4):
        done = v >= LIGHT_S
        col = (255, 90, 70) if done else (255, 255, 255)
        a = R.ramp(t, st[1][0], 0.2) * (1.0 - R.ramp(t, st[5][0] - 0.25, 0.25))
        F.label(f"{v // 60}:{v % 60:02d}", W / 2, 300, 170, col, a)
        F.label("SINCE THE SUN VANISHED" if not done else "LIGHT RUNS OUT", W / 2, 430, 46, R.AMBER, a)
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
    total = t + 0.6  # let the punchline caption sit for a beat before the loop restarts
    if "--preview" in sys.argv:
        ts = sorted([0.0, 1.2] + [s + 0.6 for s, _ in st[1:]] + [st[3][0] + 2.5, st[4][0] + 1.6, st[4][0] + 2.6,
                                                                total - 0.05])
        ims = [frame(x, st, total).resize((216, 384)) for x in ts]
        sheet = Image.new("RGB", (216 * len(ims), 384))
        for k, im in enumerate(ims):
            sheet.paste(im, (216 * k, 0))
        p = os.path.join(os.environ.get("PREVIEW_DIR", "/tmp"), "sun8_preview.png"); sheet.save(p)
        print("preview ->", p, round(total, 2), [round(s, 2) for s, _ in st]); return
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
    with open(srt) as f:  # hold the last caption ("8 minutes ago.") to the final frame
        blocks = f.read().strip().split("\n\n")
    a, _ = blocks[-1].split("\n")[1].split(" --> ")
    end = f"{int(total // 3600):02d}:{int(total % 3600 // 60):02d}:{int(total % 60):02d},{int(total * 1000 % 1000):03d}"
    lines = blocks[-1].split("\n"); lines[1] = f"{a} --> {end}"; blocks[-1] = "\n".join(lines)
    with open(srt, "w") as f:
        f.write("\n\n".join(blocks) + "\n")
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
