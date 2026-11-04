"""
ep29 Short: "Flying to the Biggest Black Hole in Our Galaxy" (9:16, ~18 s, $0 local).

Built on the framework (local_runner/panel/MARKET_STUDY.md): a journey/zoom (2.6x breakout in the
market study) to an extreme object (our best-staying topic), real imagery only, one text layer.

  1  ESO/VISTA galactic-centre star field fills the screen; target circled; "26,000 LIGHT-YEARS"
  2  deep zoom into the core while the distance counts down
  3  ESO/VLT NACO time-lapse: ~20 years of real observations, stars whipping around an empty point
  4  same footage: "4,000,000 SUNS" you can't see
  5  Event Horizon Telescope's first image of Sagittarius A* (2022); dissolves back to frame 1 (loop)

Facts: distance 8.18 kpc = ~26,700 ly (GRAVITY 2019); mass ~4.3 million Suns; event horizon ~25 million km
across, inside Mercury's orbit (116 million km across); EHT image released 12 May 2022.
Credits: ESO/VVV Survey/D. Minniti (eso1242a), ESO/S. Gillessen et al. (eso1825e), EHT Collaboration (eso2208).
All CC BY 4.0.

  python longform/short_sgra.py [--preview]  ->  final_videos/sci_ep29_sgra_complete.mp4
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
os.environ.setdefault("CHANNEL", "b")

import lf01_render as R  # noqa: E402
import short_sun_v2 as SV  # noqa: E402  (video-shot streaming + camera)
from audio_post import (_probe_duration, create_phrase_subtitles, generate_ambient_bed,  # noqa: E402
                        generate_voiceover, mux_video_audio_subs, shift_srt_file)
from short_zoom_v2 import whoosh_track  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
VID = "sci_ep29_sgra"
W, H, FPS = 1080, 1920, 30
R.W, R.H = W, H
STILLS = os.path.join(ROOT, "i2v_stills", VID)
WORK = os.path.join(ROOT, "temp_clips", f"{VID}_audio")
OUT = os.path.join(ROOT, "final_videos", f"{VID}_complete.mp4")
STEM = f"{VID}_voice"
VO_DELAY = 0.05
VOICE = "en-US-AndrewMultilingualNeural"
XF = 0.3
LY = 26000

BEATS = [
    dict(text="This is a trip to the black hole at the center of our galaxy.",
         phrases=["This is a trip to the black hole", "at the center of our galaxy."], rate="+8%", pause_ms=60),
    # plain words only: "past" can be heard as "passed"
    # "right into the core" was heard as "...the cold" (weak final consonant): clearer words
    dict(text="Twenty-six thousand light-years, through billions of stars, all the way to the center.",
         caption_text="26,000 light-years, through billions of stars, all the way to the center.",
         phrases=["26,000 light-years,", "through billions of stars,", "all the way to the center."], rate="+6%",
         pause_ms=80),
    # "around nothing." came out as "around now/us": the clipped last word; say it plainly
    dict(text="This is real telescope footage. Stars racing around an empty point in space.",
         phrases=["This is real telescope footage.", "Stars racing around", "an empty point in space."],
         rate="+4%", pause_ms=80),
    dict(text="Something four million times heavier than the Sun, and completely invisible.",
         caption_text="Something 4 million times heavier than the Sun, and completely invisible.",
         phrases=["Something 4 million times", "heavier than the Sun,", "and completely invisible."],
         rate="+4%", pause_ms=120),
    dict(text="Until twenty twenty-two, when we took its first real photo.",
         caption_text="Until 2022, when we took its first real photo.",
         phrases=["Until 2022,", "when we took its first real photo."], rate="+2%", pause_ms=0),
]
TOP = [("A TRIP TO OUR", "GALAXY'S BLACK HOLE"), None, ("20 YEARS OF", "REAL FOOTAGE"),
       ("4,000,000 SUNS", "YOU CAN'T SEE"), ("ITS FIRST", "REAL PHOTO")]

VISTA_CORE = (0.5125, 0.332)  # Sgr A* in eso1242a (fractions)
# speed is set in Film so the 20 s clip exactly covers its beats (it ran out once and froze for 2.7 s);
# framerate= blends neighbouring frames, so a non-integer speed still moves evenly
# eso1825e repeats one ~2.4 s pass of the real time-lapse (frames 42-102, sharp) spliced with a blurrier
# 1.6 s version; using the whole clip made the stars jump every ~1.2 s. Use the single clean pass only.
ORBIT = dict(src="eso1825e_uhd.mp4", t0=42 / 25.0, speed=0.55, k=1.03, cx=0.505, cy=0.455, z=(0.90, 1.30))  # centred on S2's hairpin around Sgr A*
ORBIT_PASS = (42, 102)
PH = {}


def fit(text, size):
    """Largest size <= size at which the bold label fits inside the frame with a 60 px margin."""
    from PIL import ImageFont
    while size > 40 and ImageFont.truetype(R.BOLD, size).getlength(text) > W - 120:
        size -= 2
    return size


def load():
    for n, f in (("vista", "eso1242a.jpg"), ("eht", "eso2208-eht-mwa.jpg")):
        PH[n] = Image.open(os.path.join(STILLS, f)).convert("RGB")


def still(name, k, cx, cy):
    """Screen = source scaled by k (screen px per source px), source point (cx, cy) at screen centre.
    The centre is clamped so the image always covers the whole screen (no black bands)."""
    p = PH[name]
    hw, hh = W / 2 / k, H / 2 / k
    x = min(max(cx * p.width, hw), p.width - hw) if 2 * hw < p.width else p.width / 2  # smaller than the
    y = min(max(cy * p.height, hh), p.height - hh) if 2 * hh < p.height else p.height / 2  # screen: centre it
    c = 1 / k
    im = p.transform((W, H), Image.AFFINE, (c, 0, x - W / 2 * c, 0, c, y - H / 2 * c), resample=Image.BICUBIC)
    return im, (W / 2 + (cx * p.width - x) * k, H / 2 + (cy * p.height - y) * k)


def ring_composite(im, bg, kk):
    """EHT photo over a real star field, with no background stars inside the ring or its shadow."""
    yy, xx = np.mgrid[0:H, 0:W]
    rr = np.hypot(xx - W / 2, yy - H / 2) / (0.34 * PH["eht"].width * kk)  # 1.0 ~ just outside the ring
    keep = np.clip((rr - 0.9) / 0.2, 0, 1)[..., None]
    return np.maximum(np.asarray(im).astype(np.float32), bg * keep).astype(np.uint8)


def vista_k(e):
    k0 = max(W / PH["vista"].width, H / PH["vista"].height)  # cover
    return k0 * 1.7 * math.exp(math.log(2.4) * e)  # opens on the core (1.7x), dives to 4x across beats 1-2


class Film:
    def __init__(self, st, total):
        self.st, self.total = st, total
        self.bounds = [0.0] + [s for s, _ in st[1:]] + [total]
        self.orbit = None
        self.first = None
        self.under = None
        self.bg = None
        self.trail, self.trail_k = None, -1
        self.open_bg = None

    def zoom_e(self, t):  # 0..1 across beat 2: slow start, accelerating dive
        a, b = self.bounds[1], self.bounds[2]
        u = min(1.0, max(0.0, (t - a) / (b - a)))
        return 0.06 * min(1.0, u / 0.25) + 0.94 * R.sm(max(0.0, (u - 0.15) / 0.85)) ** 1.3

    def picture(self, i, t):
        if i == 0:  # frame 1: the destination itself, big and recognisable (Gate 2), slowly pulling back
            k0 = max(W / PH["eht"].width, H / PH["eht"].height)
            u = min(1.0, t / self.bounds[1])
            kk = k0 * R.lerp(1.10, 1.02, u)
            im, _ = still("eht", kk, 0.5, 0.5)
            if self.open_bg is None:  # the real galactic-centre star field behind it (its sky, no black bands)
                v, _ = still("vista", vista_k(1.0), *VISTA_CORE)
                self.open_bg = np.asarray(v).astype(np.float32) * 0.6
            return Image.fromarray(ring_composite(im, self.open_bg, kk)), (W / 2, H / 2)
        if i == 1:
            im, ring = still("vista", vista_k(self.zoom_e(t)), *VISTA_CORE)
            return im, ring
        if i in (2, 3):
            if self.orbit is None:
                # the one clean pass plays slowly across beats 3-4 (no hold, no loop); -ss lands on its first
                # frame and trim stops it before the splice (the -t limit is on input time, so trim does the cut)
                span = self.bounds[4] - self.bounds[2] + XF + 0.1
                a, b = ORBIT_PASS
                ORBIT["speed"] = round((b - a) / 25.0 / span, 4)
                ORBIT["pre"] = (f"trim=end_frame={b - a},setpts=(PTS-STARTPTS)/{ORBIT['speed']},"
                                f"framerate=fps={FPS}")
                self.orbit = SV.Shot(ORBIT, span)
                if self.under is None:  # the same sky region from VISTA, deep zoom + soft: real light behind the stars
                    u, _ = still("vista", vista_k(1.0), *VISTA_CORE)
                    self.under = np.asarray(u.filter(ImageFilter.GaussianBlur(3))).astype(np.float32) * 0.32
            s0, s1 = self.bounds[2], self.bounds[4]
            z = R.lerp(*ORBIT["z"], min(1.0, max(0.0, (t - s0) / (s1 - s0))))  # steady push, no easing to a stop
            k_src = max(0, int(round((t - s0) * FPS)))
            raw = np.asarray(self.orbit.get(k_src)).astype(np.float32)
            # star trails: each star leaves a fading trail of the positions it actually passed through, so
            # the orbits around the empty point show as arcs (real positions, nothing drawn by hand)
            if self.trail is None or k_src < self.trail_k:
                self.trail = raw.copy()
            elif k_src != self.trail_k:
                self.trail = np.maximum(self.trail * 0.997, raw)  # long memory: the whole pass builds up
            self.trail_k = k_src
            mix = np.maximum(raw, self.trail * np.array([0.65, 0.85, 1.0], np.float32))  # trails a cooler blue
            frame = SV.camera(Image.fromarray(np.clip(mix, 0, 255).astype(np.uint8)), z)
            a = np.asarray(frame).astype(np.float32)
            a = np.minimum(255, a * 1.35 + 6)  # lift the star field a touch
            return Image.fromarray(np.maximum(a, self.under).astype(np.uint8)), (W / 2, H / 2)
        # the EHT photo sits in the real star field it came from (the orbit footage's last frame), so its
        # black sky never shows as bands; the ring grows steadily
        s0 = self.bounds[4]
        u = min(1.0, max(0.0, (t - s0) / (self.total - s0)))
        if self.bg is None:
            last = SV.camera(self.orbit.get(10 ** 6), ORBIT["z"][1])
            a = np.minimum(255, np.asarray(last).astype(np.float32) * 1.35 + 6)
            self.bg = np.maximum(a, self.under) * 0.8
        k0 = max(W / PH["eht"].width, H / PH["eht"].height)
        kk = k0 * R.lerp(0.80, 1.0, u)
        im, _ = still("eht", kk, 0.5, 0.5)
        return Image.fromarray(ring_composite(im, self.bg, kk)), (W / 2, H / 2)

    def overlays(self, F, i, t, k, ring):
        if k <= 0.01:
            return
        if TOP[i]:
            a = k
            if i == len(TOP) - 1:
                a *= 1.0 - R.ramp(t, self.total - 0.5, 0.2)
            F.label(TOP[i][0], W / 2, 210, fit(TOP[i][0], 92), (255, 255, 255), a)
            F.label(TOP[i][1], W / 2, 325, fit(TOP[i][1], 88), R.AMBER, a)
        if i == 3:  # the empty point the stars orbit
            r = 95
            F.draw().ellipse((W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r), outline=R.AMBER + (int(230 * k),), width=7)
        if i == 0:
            F.label("26,000 LIGHT-YEARS AWAY", W / 2, 1420, fit("26,000 LIGHT-YEARS AWAY", 64), (255, 255, 255), k)
        if i == 1:  # target ring on Sgr A* and the distance left
            e = self.zoom_e(t)
            r = 70 + 40 * e
            x, y = ring
            F.draw().ellipse((x - r, y - r, x + r, y + r), outline=R.AMBER + (int(230 * k),), width=7)
            ly = int(round(LY * (1.0 - e) ** 2.2 / 10.0)) * 10
            F.label(f"{ly:,}", W / 2, 300, 150, (255, 255, 255), k)
            F.label("LIGHT-YEARS TO GO", W / 2, 420, 52, R.AMBER, k)

    def frame(self, t):
        st = self.st
        i = max(j for j in range(len(st)) if st[j][0] <= t or j == 0)
        s0 = st[i][0] if i else 0.0
        F = R.Frame()
        im, ring = self.picture(i, t)
        F.im = im
        cross = i > 0 and t < s0 + XF and i != 3  # 2->3 is the same shot
        if cross:
            prev, pring = self.picture(i - 1, t)
            F.im = Image.blend(prev, F.im, R.sm((t - s0) / XF))
        if i > 0 and t < s0 + XF:
            self.overlays(F, i - 1, t, 1.0 - R.ramp(t, s0, XF / 2), ring)
        self.overlays(F, i, t, 1.0 if i == 0 else R.ramp(t, s0 + XF / 2, XF / 2), ring)
        out = F.rgb()
        if t == 0.0:
            self.first = out
        if self.first is not None and t > self.total - 0.25:
            out = Image.blend(out, self.first, R.sm((t - (self.total - 0.25)) / 0.25))
        return out


def main():
    load()
    os.makedirs(WORK, exist_ok=True)
    generate_voiceover(script_beats=BEATS, output_mp3=os.path.join(WORK, f"{STEM}.mp3"), voice=VOICE,
                       pitch="+0Hz", work_dir=WORK)
    t, st = VO_DELAY, []
    for i, b in enumerate(BEATS, start=1):
        d = _probe_duration(os.path.join(WORK, f"{STEM}_beat{i}.wav"))
        st.append((t, t + d)); t += d + b["pause_ms"] / 1000.0
    total = t + 0.7
    n = int(round(total * FPS))
    film = Film(st, total)
    if "--preview" in sys.argv:
        ts = sorted({0.0, 1.0, 2.0} | {round(s + 0.6, 3) for s, _ in st[1:]} | {round(st[1][1] - 0.2, 3),
                                                                           round(st[3][1] - 0.2, 3), round(total - 0.6, 3)})
        ks = {int(round(x * FPS)) for x in ts}
        ims = []
        for k in range(max(ks) + 1):
            im = film.frame(k / FPS)
            if k in ks:
                ims.append(im.resize((216, 384)))
        sheet = Image.new("RGB", (216 * len(ims), 384))
        for k, im in enumerate(ims):
            sheet.paste(im, (216 * k, 0))
        p = os.path.join(os.environ.get("PREVIEW_DIR", "/tmp"), "sgra_preview.png"); sheet.save(p)
        print("preview ->", p, round(total, 2), [round(s, 2) for s, _ in st]); return
    silent = os.path.join(WORK, f"{VID}_silent.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                            "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    for k in range(n):
        enc.stdin.write(np.asarray(film.frame(k / FPS)).tobytes())
    enc.stdin.close(); enc.wait()
    srt = os.path.join(WORK, f"{VID}_captions.srt")  # kept for the optional YouTube subtitle upload
    create_phrase_subtitles(BEATS, work_dir=WORK, stem=STEM, srt_path=srt, max_words=5)
    shift_srt_file(srt, int(VO_DELAY * 1000))
    bed = os.path.join(WORK, "ambient.wav"); generate_ambient_bed(total + 1.0, bed, preset="space", volume=0.2)
    # whoosh_track starts each whoosh 0.35 s before its time: keep it clear of the previous line's last
    # word (it masked "core" into "cold")
    wh = os.path.join(WORK, "whoosh.wav"); whoosh_track([st[1][1] + 0.45, st[3][1] + 0.45], total, wh)
    mix = os.path.join(WORK, "mix.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, f"{STEM}.mp3"), "-i", bed, "-i", wh,
                    "-filter_complex",
                    f"[0:a]adelay={int(VO_DELAY*1000)}:all=1,apad[v];"
                    f"[1:a]atrim=start=0.4,asetpts=PTS-STARTPTS[b];[v][b][2:a]amix=inputs=3:duration=shortest:normalize=0,"
                    f"atrim=0:{total:.3f},loudnorm=I=-14:TP=-1.5:LRA=11[o]", "-map", "[o]", "-ar", "48000", mix], check=True)
    mux_video_audio_subs(silent, mix, srt, OUT, burn_captions=False)  # one text layer: the labels
    align_srt(OUT, srt)
    print(f"✅ {OUT} ({_probe_duration(OUT):.1f}s)")


def align_srt(mp4, srt):
    """Rewrite the (optional, upload-only) subtitle file from Whisper's word times, so each phrase starts
    on its first spoken word instead of an estimate."""
    import re
    import whisper
    def norm(w):
        return re.sub(r"[^a-z0-9]", "", w.lower())
    res = whisper.load_model("small").transcribe(mp4, word_timestamps=True, language="en")
    heard = []
    for sgm in res["segments"]:
        for w in sgm["words"]:
            if heard and re.fullmatch(r"\s*,\d+[.,]?\s*", w["word"]):  # Whisper splits "26,000" into "26" ",000"
                heard[-1] = (heard[-1][0] + norm(w["word"]), heard[-1][1], w["end"])
            else:
                heard.append((norm(w["word"]), w["start"], w["end"]))
    phrases = [p for b in BEATS for p in b["phrases"]]
    starts, k = [], 0
    for ph in phrases:
        first = norm(ph.split()[0])
        j = next((j for j in range(k, min(k + 16, len(heard))) if heard[j][0] == first), None)
        starts.append(heard[j][1] if j is not None else None)
        if j is not None:
            k = j + 1
    total = _probe_duration(mp4)

    def ts(x):
        return f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{int(x % 60):02d},{int(round(x * 1000)) % 1000:03d}"
    blocks, n = [], 0
    for i, ph in enumerate(phrases):
        a = starts[i]
        if a is None:
            continue
        b = next((s for s in starts[i + 1:] if s is not None), total)
        n += 1
        blocks.append(f"{n}\n{ts(max(0.0, a - 0.05))} --> {ts(b - 0.02)}\n{ph}")
    with open(srt, "w") as f:
        f.write("\n\n".join(blocks) + "\n")
    out = os.path.join(ROOT, "final_videos", f"{VID}_captions.srt")
    with open(out, "w") as f:
        f.write("\n\n".join(blocks) + "\n")


if __name__ == "__main__":
    main()
