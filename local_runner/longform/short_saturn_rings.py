"""
ep26 Short: "Saturn's Rings Are Thinner Than a House" (9:16, ~20 s, $0 local).

Built to the post-LF01 rules: full-frame real imagery at every moment (Cassini and Hubble, all
public domain), a contradiction hook in the first 2 s, constant camera motion, a whoosh on every
cut, the Andrew voice, and the punchline as the last word.

Numbers: the A ring's outer edge is at 136,775 km radius, so the main rings are ~273,500 km
across = 21.5 Earth diameters. The main rings are typically ~10 m thick (up to ~1 km). Scaled
to a 7 cm phone width, 10 m becomes ~2.6 nanometres; a sheet of paper is ~0.1 mm, so the
rings would be ~38,000 times thinner than paper.

  python longform/short_saturn_rings.py   ->  final_videos/sci_ep26_saturn_rings_complete.mp4
"""
import math
import os
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
os.environ.setdefault("CHANNEL", "b")

import lf01_render as R  # noqa: E402
from audio_post import (_probe_duration, create_phrase_subtitles, generate_ambient_bed,  # noqa: E402
                        generate_voiceover, mux_video_audio_subs, shift_srt_file)
from short_zoom_v2 import whoosh_track  # noqa: E402

VID = "sci_ep26_saturn_rings"
W, H, FPS = 1080, 1920, 30
R.W, R.H = W, H
ASSETS = os.path.join(ROOT, "i2v_stills", VID)
WORK = os.path.join(ROOT, "temp_clips", f"{VID}_audio")
OUT = os.path.join(ROOT, "final_videos", f"{VID}_complete.mp4")
STEM = f"{VID}_voice"
VO_DELAY = 0.1
VOICE = "en-US-AndrewMultilingualNeural"
XF = 0.35

BEATS = [
    dict(text="Saturn's rings are wider than twenty Earths.", caption_text="Saturn's rings are wider than 20 Earths.",
         phrases=["Saturn's rings are", "wider than 20 Earths."], rate="+6%", pause_ms=120),
    dict(text="Two hundred and seventy thousand kilometres, edge to edge.", caption_text="270,000 km, edge to edge.",
         phrases=["270,000 km,", "edge to edge."], rate="+6%", pause_ms=120),
    dict(text="But in most places, they're only about ten metres thick.",
         caption_text="But in most places, they're only about 10 metres thick.",
         phrases=["But in most places,", "they're only", "about 10 metres thick."], rate="+4%", pause_ms=120),
    dict(text="Thinner than a house is tall.", phrases=["Thinner than", "a house is tall."], rate="+4%", pause_ms=120),
    dict(text="Shrink them to the width of your phone, and they'd be thousands of times thinner than paper.",
         phrases=["Shrink them to", "the width of your phone,", "and they'd be thousands of times", "thinner than paper."],
         rate="+6%", pause_ms=120),
    dict(text="So when we see them from the side, Saturn's rings almost vanish.",
         phrases=["So when we see them", "from the side,", "Saturn's rings", "almost vanish."], rate="+0%", pause_ms=0),
]
TOP = ["20 EARTHS WIDE", "273,000 km", "~10 m THICK", "THINNER THAN A HOUSE", "38,000× THINNER THAN PAPER", ""]


class Photos:
    def __init__(self):
        self.p = {}
        for n in ("saturn", "equinox", "backlit", "ringclose"):
            self.p[n] = Image.open(os.path.join(ASSETS, f"{n}.jpg")).convert("RGB")
        e = Image.open(os.path.join(ASSETS, "edgeon.jpg")).convert("RGB")
        self.p["edgeon"] = e.crop((0, 0, e.width, int(e.height * 0.80)))  # drop the HST caption strip


PH = None


SUBJ_Y = 1150  # subject centre on screen: below the mid-frame captions, above the Shorts UI


def photo(F, name, zoom, cx, cy, rot=0.0, alpha=1.0, fit="cover", drop=True):
    """Like R.Frame.photo, but for this episode's images. drop=True shifts the photo so its
    (cx, cy) point lands at SUBJ_Y instead of the frame centre (landscape photos only)."""
    R.assets().photo[name] = PH.p[name]
    if drop:
        cy -= (SUBJ_Y - H / 2) / (H * zoom)  # cover scale is H/photo_h * zoom for these images
    F.photo(name, zoom=zoom, cx=cx, cy=cy, rot=rot, alpha=alpha, fit=fit)


def scene(F, i, u, t):
    """Draw beat i at local progress u (0..1). Zooms are relative to 'cover' (photo height fills
    1920 px for these landscape images), so ~0.4 shows the whole ring system across the frame."""
    sm = R.sm
    if i == 0:  # full Saturn, rings filling the width, push in + slight roll
        photo(F, "saturn", zoom=R.lerp(0.40, 0.50, u), cx=0.49, cy=0.555, rot=R.lerp(-6, 0, u))
    elif i == 1:  # a row of 21 Earths across the rings (true scale), sweeping in
        z = 0.50
        photo(F, "saturn", zoom=z, cx=0.49, cy=0.555, rot=0)
        span = 0.81 * 3840 * (H / 1963) * z  # A-ring outer diameter on screen (px)
        d = span / 21.5
        n = int(min(21, 1 + 21 * sm(u / 0.7)))
        y = SUBJ_Y - 10
        for k in range(n):
            F.planet("earth", W / 2 - span / 2 + d * (k + 0.5), y, d * 0.95)
    elif i == 2:  # equinox: the same rings, almost edge-on, push in
        photo(F, "equinox", zoom=R.lerp(0.42, 0.62, u), cx=0.5, cy=0.5, rot=R.lerp(8, 2, sm(u)))
    elif i == 3:  # zoom hard into the ring line near its tip
        photo(F, "equinox", zoom=R.lerp_log(0.62, 3.2, sm(u)), cx=R.lerp(0.5, 0.86, sm(u)), cy=0.503, rot=2)
    elif i == 4:  # inside the rings: ringlet texture streaming past
        photo(F, "ringclose", zoom=R.lerp(1.55, 1.75, u), cx=R.lerp(0.44, 0.56, u), cy=0.5, rot=-20, drop=False)
    else:  # from the side: Hubble's edge-on view, then the backlit Cassini portrait
        # Saturn at equinox, rings almost edge-on: a hair-thin line through the planet
        photo(F, "equinox", zoom=R.lerp(0.48, 0.40, u), cx=0.5, cy=0.5, rot=R.lerp(0, -3, u))


def frame(t, st, total):
    i = max(k for k in range(len(st)) if st[k][0] <= t or k == 0)
    s0 = st[i][0]
    s1 = st[i + 1][0] if i + 1 < len(st) else total
    F = R.Frame()
    scene(F, i, min(1.0, (t - s0) / max(0.5, s1 - s0)), t)
    if i > 0 and t < s0 + XF:  # crossfade from the previous scene
        P = R.Frame()
        p0, p1 = st[i - 1][0], s0
        scene(P, i - 1, 1.0, t)
        img = Image.blend(P.rgb(), F.rgb(), R.sm((t - s0) / XF))
        F.im = img
    if TOP[i]:
        F.label(TOP[i], W / 2, 170, 70 if len(TOP[i]) < 18 else 56, R.AMBER, R.ramp(t, s0 + 0.1, 0.3))
    return F.rgb()


def main():
    global PH
    PH = Photos()
    os.makedirs(WORK, exist_ok=True)
    generate_voiceover(script_beats=BEATS, output_mp3=os.path.join(WORK, f"{STEM}.mp3"), voice=VOICE,
                       pitch="+0Hz", work_dir=WORK)
    t, st = VO_DELAY, []
    for i, b in enumerate(BEATS, start=1):
        d = _probe_duration(os.path.join(WORK, f"{STEM}_beat{i}.wav"))
        st.append((t, t + d)); t += d + b["pause_ms"] / 1000.0
    total = t + 0.05
    if "--preview" in sys.argv:
        ts = [0.3, 1.5] + [s + 0.8 for s, _ in st[1:]] + [st[-1][0] + 2.5, total - 0.2]
        ims = [frame(x, st, total).resize((216, 384)) for x in ts]
        sheet = Image.new("RGB", (216 * len(ims), 384))
        for k, im in enumerate(ims):
            sheet.paste(im, (216 * k, 0))
        p = os.path.join(os.environ.get("PREVIEW_DIR", "/tmp"), "rings_preview.png"); sheet.save(p)
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
