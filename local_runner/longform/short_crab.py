"""
ep30 Short: "Flying Into the Crab Nebula" (9:16, ~20 s, $0 local).

The flight style the owner approved (5 Nov, "preview 1 is too good"): fly into a colour-rich real image with a 3D
star-field streaming past, one continuous move, then a real payoff.

  1-2  Hubble's Crab Nebula mosaic grows from a small cloud in deep space to fill the screen; stars stream past;
       hook text "IN THE YEAR 1054 / A STAR EXPLODED" from frame 1
  3    deeper, through Webb's 10,000-px image of the filaments (sharp at 1:1)
  4-5  Hubble's close-up of the heart: the ripple-like shock waves, and a ring on the real pulsar (NASA's caption:
       "the rightmost of the two bright stars near the center"); dissolves back to frame 1 (loop)

Facts (NASA/CXC Crab pages): supernova recorded in 1054 AD, visible in daylight for weeks; ~6,500 light-years away;
the pulsar is ~20 km across and spins ~30 times a second.
Credits: NASA, ESA, J. Hester and A. Loll (PIA03606); NASA, ESA, CSA, STScI, T. Temim (Webb, weic2326a, CC BY 4.0);
NASA and ESA (Hubble heart close-up).

  python longform/short_crab.py [--preview]  ->  final_videos/sci_ep30_crab_complete.mp4
"""
import math
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
os.environ.setdefault("CHANNEL", "b")

import lf01_render as R  # noqa: E402
import starflight  # noqa: E402
from audio_post import (_probe_duration, generate_ambient_bed, generate_voiceover,  # noqa: E402
                        mux_video_audio_subs)
from short_zoom_v2 import whoosh_track  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
VID = "sci_ep30_crab"
W, H, FPS = 1080, 1920, 30
R.W, R.H = W, H
STILLS = os.path.join(ROOT, "i2v_stills", VID)
WORK = os.path.join(ROOT, "temp_clips", f"{VID}_audio")
OUT = os.path.join(ROOT, "final_videos", f"{VID}_complete.mp4")
STEM = f"{VID}_voice"
VO_DELAY = 0.05
VOICE = "en-US-AndrewMultilingualNeural"

BEATS = [
    # no comma after the year: it left a 0.7 s pause inside the hook line
    dict(text="In the year ten fifty-four a star exploded so brightly, people saw it in daylight.",
         caption_text="In the year 1054 a star exploded so brightly, people saw it in daylight.",
         phrases=["In the year 1054,", "a star exploded so brightly,", "people saw it in daylight."],
         rate="+6%", pause_ms=80),
    dict(text="We're flying into what's left of it, sixty-five hundred light-years away.",
         caption_text="We're flying into what's left of it, 6,500 light-years away.",
         phrases=["We're flying into what's left of it,", "6,500 light-years away."], rate="+6%", pause_ms=80),
    dict(text="Through its glowing wreckage, still racing outward, all the way to its heart.",
         phrases=["Through its glowing wreckage,", "still racing outward,", "all the way to its heart."],
         rate="+5%", pause_ms=100),
    # "...only twenty kilometres wide." lost its last word: end on a strong, plain one
    dict(text="And there it is. A dead star, no bigger than a city.",
         phrases=["And there it is.", "A dead star,", "no bigger than a city."], rate="+3%", pause_ms=100),
    dict(text="Still spinning thirty times every second, a thousand years later.",
         caption_text="Still spinning 30 times every second, a thousand years later.",
         phrases=["Still spinning 30 times every second,", "a thousand years later."], rate="+3%", pause_ms=0),
]
HOOK = ("IN THE YEAR 1054", "A STAR EXPLODED")  # frame-1 text, before the voice starts
# hand-split captions; joined they are exactly the spoken words (beat 1 is covered by the hook text instead)
CAPS = ["IN THE YEAR 1054,", "A STAR EXPLODED", "SO BRIGHTLY,", "PEOPLE SAW IT", "IN DAYLIGHT.",
        "WE'RE FLYING INTO", "WHAT'S LEFT OF IT,", "6,500", "LIGHT-YEARS AWAY.",
        "THROUGH ITS", "GLOWING WRECKAGE,", "STILL RACING", "OUTWARD,", "ALL THE WAY", "TO ITS HEART.",
        "AND THERE IT IS.", "A DEAD STAR,", "NO BIGGER", "THAN A CITY.",
        "STILL SPINNING", "30 TIMES", "EVERY SECOND,", "A THOUSAND", "YEARS LATER."]
HOOK_CAPS = 5           # the first 5 caption chunks are beat 1, shown as the hook text instead
CAP_Y = 700
CAP_SIZE = 112

PUL = (761 / 1200, 560 / 1173)   # NASA: the pulsar is the rightmost of the two bright stars near the centre
WEBB_C = (0.5255, 0.529)         # centre of the ripple rings in Webb's image
PH = {}


def load():
    PH["mosaic"] = Image.open(os.path.join(STILLS, "PIA03606.jpg")).convert("RGB")
    from PIL import ImageEnhance
    webb = Image.open(os.path.join(STILLS, "weic2326a.jpg")).convert("RGB")
    # Webb's inner nebula is pale next to the Hubble mosaic: a modest grade keeps the colour consistent
    PH["webb"] = ImageEnhance.Color(ImageEnhance.Contrast(webb).enhance(1.18)).enhance(1.25)
    PH["heart"] = Image.open(os.path.join(STILLS, "GSFC_20171208_Archive_e000273.jpg")).convert("RGB")


def still(name, k, cx, cy):
    p = PH[name]; c = 1 / k
    x, y = cx * p.width, cy * p.height
    return np.asarray(p.transform((W, H), Image.AFFINE, (c, 0, x - W / 2 * c, 0, c, y - H / 2 * c),
                                  resample=Image.BICUBIC)).astype(np.float32)


def fit(text, size):
    from PIL import ImageFont
    while size > 40 and ImageFont.truetype(R.BOLD, size).getlength(text) > W - 120:
        size -= 2
    return size


class Film:
    def __init__(self, st, total):
        self.st, self.total = st, total
        self.sf = starflight.StarFlight(seed=11)
        self.t_webb = st[2][0]            # into Webb's image as "through its glowing wreckage" starts
        self.t_heart = st[3][0]           # the heart close-up on "and there it is"
        self.first = None

    def picture(self, t):
        # 1) approach: the whole nebula grows from a small cloud to filling the screen (preview 1, approved)
        if t < self.t_webb + 0.35:
            u = min(1.0, t / self.t_webb)
            kk = 0.12 * math.exp(math.log(1.7 / 0.12) * u)
            sp = 0.6 * (1 - 0.45 * u)
            dist = 0.6 * FPS * self.t_webb * (u - 0.225 * u * u)
            img = still("mosaic", kk, 0.5, 0.5) + self.sf.layer(dist, sp).astype(np.float32) * 0.85
            if t >= self.t_webb:  # crossfade into Webb's sharper image of the same region
                x = R.sm((t - self.t_webb) / 0.35)
                img = img * (1 - x) + self.webb(t) * x
            return img
        if t < self.t_heart:
            return self.webb(t)
        # 3) the heart: Hubble close-up, pushing in on the pulsar
        u = min(1.0, (t - self.t_heart) / (self.total - self.t_heart))
        img = still("heart", (H / PH["heart"].height) * math.exp(math.log(1.45) * u), *PUL)
        if t < self.t_heart + 0.3:
            x = R.sm((t - self.t_heart) / 0.3)
            img = self.webb(self.t_heart) * (1 - x) + img * x
        return img

    def webb(self, t):
        # 2) deeper through the filaments: Webb from the inner nebula down to 1:1 pixels; streaks fade as we arrive
        u = min(1.0, max(0.0, (t - self.t_webb) / (self.t_heart - self.t_webb)))
        # starts at the same apparent scale as the mosaic's last frame (~16% of the nebula across the screen;
        # owner: starting wider made the cut lurch backwards and read as too fast), then a gentle 1.7x push
        kk = 0.64 * math.exp(math.log(1.1 / 0.64) * u)
        a = max(0.0, 0.6 - u * 1.2)
        # start on the colourful filaments and drift onto the heart as we push in
        e = R.sm(u)
        img = still("webb", kk, R.lerp(0.50, WEBB_C[0], e), R.lerp(0.47, WEBB_C[1], e))
        if a > 0.01:
            img = img + self.sf.layer(self.dist_webb(t), 0.3 * a).astype(np.float32) * 0.85 * a
        return img

    def dist_webb(self, t):
        return 0.6 * FPS * self.t_webb * 0.775 + (t - self.t_webb) * FPS * 0.25

    def frame(self, t, caps):
        F = R.Frame()
        F.im = Image.fromarray(np.clip(self.picture(t), 0, 255).astype(np.uint8))
        st = self.st
        if t < st[1][0]:  # hook text from frame 1, through beat 1
            a = 1.0 - R.ramp(t, st[1][0] - 0.25, 0.25)
            F.label(HOOK[0], W / 2, 300, fit(HOOK[0], 104), (255, 255, 255), a)
            F.label(HOOK[1], W / 2, 430, fit(HOOK[1], 112), R.AMBER, a)
        if t >= self.t_heart + 0.3:  # ring on the real pulsar
            r = 52 + 5 * math.sin(t * 6)
            al = R.ramp(t, self.t_heart + 0.3, 0.3) * (1.0 - R.ramp(t, self.total - 0.5, 0.2))
            F.draw().ellipse((W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r), outline=R.AMBER + (int(235 * al),), width=7)
        cap = next((c for c, a, b in caps if a <= t < b), None)
        if cap and t < self.total - 0.3:
            F.label(cap, W / 2, CAP_Y, fit(cap, CAP_SIZE), (255, 255, 255), 1.0)
        im = F.rgb()
        if t == 0.0:
            self.first = im
        if self.first is not None and t > self.total - 0.25:
            im = Image.blend(im, self.first, R.sm((t - (self.total - 0.25)) / 0.25))
        return im


def word_times():
    import whisper
    # alignment, not recognition: prime with the known script so no words are dropped between runs
    script = " ".join(b.get("caption_text", b["text"]) for b in BEATS)
    res = whisper.load_model("small").transcribe(os.path.join(WORK, f"{STEM}.mp3"), word_timestamps=True, language="en",
                                                 temperature=0.0, condition_on_previous_text=False,
                                                 initial_prompt=script)
    out = []
    for sg in res["segments"]:
        for w in sg["words"]:
            txt = w["word"].strip()
            if out and re.fullmatch(r",\d+[.,]?", txt):
                out[-1] = (out[-1][0] + txt, out[-1][1], w["end"]); continue
            # after a comma/full stop Whisper can stretch the next word's start back across the pause
            start = w["start"]
            if out and re.search(r"[.,!?]$", out[-1][0]):
                start = max(start, w["end"] - 0.4)
            out.append((txt, start + VO_DELAY, w["end"] + VO_DELAY))
    return out


def chunks(words):
    n_script = sum(len(c.replace("-", " ").split()) for c in CAPS)
    if n_script != len(words):
        sys.exit(f"captions cover {n_script} words but {len(words)} were heard: {[w[0] for w in words]}")
    res, j = [], 0
    for c in CAPS:
        res.append([re.sub(r"[.,!?]+$", "", c), words[j][1] - 0.04])
        j += len(c.replace("-", " ").split())
    for k in range(len(res)):
        res[k].append(res[k + 1][1] if k + 1 < len(res) else words[-1][2] + 0.6)
    return [tuple(r) for r in res]


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
    all_caps = chunks(word_times())    # every line, for the upload subtitle file
    caps = all_caps[HOOK_CAPS:]         # burned in: beat 1 is shown as the frame-1 hook text instead
    film = Film(st, total)
    if "--preview" in sys.argv:
        ts = [0.0, 1.5, st[1][0] + 0.5, st[2][0] + 0.2, st[2][0] + 1.5, st[3][0] + 0.1, st[3][0] + 1.0,
              st[4][0] + 0.8, total - 0.6]
        ims = [film.frame(x, caps).resize((216, 384)) for x in ts]
        sheet = Image.new("RGB", (216 * len(ims), 384))
        for k, im in enumerate(ims):
            sheet.paste(im, (216 * k, 0))
        p = os.path.join(os.environ.get("PREVIEW_DIR", "/tmp"), "crab_preview.png"); sheet.save(p)
        print("preview ->", p, round(total, 2), [round(s, 2) for s, _ in st]); return
    n = int(round(total * FPS))
    silent = os.path.join(WORK, f"{VID}_silent.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                            "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    for k in range(n):
        enc.stdin.write(np.asarray(film.frame(k / FPS, caps)).tobytes())
    enc.stdin.close(); enc.wait()
    srt = os.path.join(WORK, f"{VID}_captions.srt")
    with open(srt, "w") as f:  # upload-only subtitle file from the same word times
        def ts(x):
            return f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{int(x % 60):02d},{int(round(x * 1000)) % 1000:03d}"
        f.write("\n\n".join(f"{k + 1}\n{ts(a)} --> {ts(b)}\n{c}" for k, (c, a, b) in enumerate(all_caps)) + "\n")
    bed = os.path.join(WORK, "ambient.wav"); generate_ambient_bed(total + 1.0, bed, preset="space", volume=0.2)
    wh = os.path.join(WORK, "whoosh.wav"); whoosh_track([st[2][1] + 0.45], total, wh)
    mix = os.path.join(WORK, "mix.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, f"{STEM}.mp3"), "-i", bed, "-i", wh,
                    "-filter_complex",
                    f"[0:a]adelay={int(VO_DELAY*1000)}:all=1,apad[v];"
                    f"[1:a]atrim=start=0.4,asetpts=PTS-STARTPTS[b];[v][b][2:a]amix=inputs=3:duration=shortest:normalize=0,"
                    f"atrim=0:{total:.3f},loudnorm=I=-14:TP=-1.5:LRA=11[o]", "-map", "[o]", "-ar", "48000", mix], check=True)
    mux_video_audio_subs(silent, mix, srt, OUT, burn_captions=False)
    print(f"✅ {OUT} ({_probe_duration(OUT):.1f}s)")


if __name__ == "__main__":
    main()
