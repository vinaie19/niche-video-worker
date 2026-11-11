"""
ep32 Short: "Mumbai to Delhi in 6 Seconds" — the fastest thing humans ever built (9:16, ~16 s, $0 local).

New format (owner, 11 Nov): a real-world race on a real map, readable in one second even muted. NASA's satellite
image of India at night; a white-hot streak runs Mumbai -> Delhi in exactly 6.0 real seconds with a live clock.

Facts: Parker Solar Probe reached ~692,000 km/h (192 km/s) at perihelion on 24 Dec 2024 (Guinness World Records,
from NASA). Mumbai-Delhi great-circle distance 1,148 km -> 1,148 / 192 = 6.0 s.
Image: India at night, NASA Earth Observatory / Suomi NPP VIIRS (2012), public domain.
The streak is an illustration of the speed, not the probe's real path (it flies near the Sun).

  python longform/short_parker.py  ->  final_videos/sci_ep32_parker_complete.mp4
"""
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
os.environ.setdefault("CHANNEL", "b")

import lf01_render as R  # noqa: E402
from audio_post import _probe_duration, generate_ambient_bed, generate_voiceover, mux_video_audio_subs  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
VID = "sci_ep32_parker"
W, H, FPS = 1080, 1920, 30
R.W, R.H = W, H
STILLS = os.path.join(ROOT, "i2v_stills", VID)
WORK = os.path.join(ROOT, "temp_clips", f"{VID}_audio")
OUT = os.path.join(ROOT, "final_videos", f"{VID}_complete.mp4")
STEM = f"{VID}_voice"
VOICE = "en-US-AndrewMultilingualNeural"

T0, TRIP = 0.6, 6.0          # the run starts at 0.6 s and takes exactly 6.0 s
BEATS = [
    dict(text="This is the fastest thing humans have ever built.",
         phrases=["This is the fastest thing", "humans have ever built."], rate="+6%", pause_ms=0),
    dict(text="Mumbai to Delhi.", phrases=["Mumbai to Delhi."], rate="+0%", pause_ms=0),
    dict(text="Done. Six seconds.", caption_text="Done. 6 seconds.", phrases=["Done.", "6 seconds."],
         rate="+0%", pause_ms=0),
    dict(text="That's NASA's Parker Solar Probe, diving past the Sun at nearly seven hundred thousand kilometres an hour.",
         caption_text="That's NASA's Parker Solar Probe, diving past the Sun at nearly 700,000 kilometers an hour.",
         phrases=["That's NASA's Parker Solar Probe,", "diving past the Sun", "at nearly 700,000 kilometers an hour."],
         rate="+6%", pause_ms=0),
    dict(text="Where would you go in six seconds?", caption_text="Where would you go in 6 seconds?",
         phrases=["Where would you go", "in 6 seconds?"], rate="+2%", pause_ms=0),
]
# when each line starts: line 3 ("Done.") lands just after the streak reaches Delhi
STARTS = [0.05, 3.0, T0 + TRIP + 0.12, None, None]
GAP = -0.15   # TTS lines carry their own trailing silence
CAPS = ["THIS IS THE", "FASTEST THING", "HUMANS HAVE", "EVER BUILT.", "MUMBAI TO DELHI.", "DONE.", "6 SECONDS.",
        "THAT'S NASA'S", "PARKER SOLAR PROBE,", "DIVING PAST", "THE SUN", "AT NEARLY", "700,000", "KILOMETERS", "AN HOUR.",
        "WHERE WOULD", "YOU GO", "IN 6 SECONDS?"]
HOOK_CAPS = 4                # line 1 is shown as the frame-1 hook text instead of captions
HOOK = ("MUMBAI TO DELHI", "IN 6 SECONDS")
CAP_Y = 315

GRID = 600                   # the image was measured on a 600-px-wide grid
MUM_G, DEL_G = (212, 437), (292, 198)


def fit(text, size):
    while size > 40 and ImageFont.truetype(R.BOLD, size).getlength(text) > W - 120:
        size -= 2
    return size


class Film:
    def __init__(self, total, caps):
        self.src = Image.open(os.path.join(STILLS, "india_viirs.jpg")).convert("RGB")
        g = self.src.width / GRID
        self.mum, self.dl = np.array(MUM_G) * g, np.array(DEL_G) * g
        self.mid = (self.mum + self.dl) / 2 + np.array([25 * g, 8 * g])
        self.L = np.hypot(*(self.dl - self.mum))
        self.total, self.caps = total, caps
        self.yy, self.xx = np.mgrid[0:H, 0:W].astype(np.float32)
        self.first = None

    def to_screen(self, p, k):
        return (W / 2 + (p[0] - self.mid[0]) * k, H / 2 + (p[1] - self.mid[1]) * k)

    def frame(self, t):
        k = (700 / self.L) * (1 + 0.28 * t / self.total)   # the route spans ~700 px; a steady push all the way
        c = 1 / k
        cx, cy = self.mid
        fr = np.asarray(self.src.transform((W, H), Image.AFFINE, (c, 0, cx - W / 2 * c, 0, c, cy - H / 2 * c),
                                           resample=Image.BICUBIC)).astype(np.float32) * 1.25
        m, d = self.to_screen(self.mum, k), self.to_screen(self.dl, k)
        u = min(1.0, max(0.0, (t - T0) / TRIP))
        p = (m[0] + (d[0] - m[0]) * u, m[1] + (d[1] - m[1]) * u)
        light = np.zeros((H, W), np.float32)
        if u > 0:
            Lm = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(Lm)
            steps = 40
            for s in range(steps):
                a, b = u * s / steps, u * (s + 1) / steps
                dr.line((m[0] + (d[0] - m[0]) * a, m[1] + (d[1] - m[1]) * a,
                         m[0] + (d[0] - m[0]) * b, m[1] + (d[1] - m[1]) * b), fill=int(40 + 215 * (s + 1) / steps), width=9)
            light = np.asarray(Lm.filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255 * 0.9
        rr = np.hypot(self.xx - p[0], self.yy - p[1])
        light = light + np.exp(-(rr / 16) ** 2) + 0.55 * np.exp(-(rr / 70) ** 2)
        fr = fr + np.clip(light, 0, 1.6)[..., None] * np.array([255, 240, 215], np.float32)
        if u >= 1:  # arrival flash on Delhi
            fl = R.ramp(t, T0 + TRIP, 0.05) * (1 - R.ramp(t, T0 + TRIP + 0.1, 0.6))
            fr = fr + (np.exp(-(np.hypot(self.xx - d[0], self.yy - d[1]) / 140) ** 2) * fl)[..., None] \
                * np.array([255, 230, 190], np.float32)
        F = R.Frame(); F.im = Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8))
        F.label("MUMBAI", m[0] - 150, m[1], 46, (255, 255, 255), 1.0)
        F.label("DELHI", d[0] - 130, d[1], 46, (255, 255, 255), 1.0)
        cap = next((cc for cc, a, b in self.caps if a <= t < b), None)
        if cap is None and t < self.caps[0][1] + 0.01 or t < 2.9:   # hook text from frame 1 through line 1
            a = 1.0 - R.ramp(t, 2.7, 0.2)
            F.label(HOOK[0], W / 2, 250, fit(HOOK[0], 104), (255, 255, 255), a)
            F.label(HOOK[1], W / 2, 375, fit(HOOK[1], 120), R.AMBER, a)
        elif cap and t < self.total - 0.3:
            F.label(cap, W / 2, CAP_Y, fit(cap, 112), (255, 255, 255), 1.0)
        # the clock, then the speed once the voice says it
        # the exact speed shows once "nearly 700,000 ... an hour" has been said: never two numbers at once
        t_speed = next(a for cc, a, b in self.caps if cc == "AN HOUR")
        if t < t_speed:
            F.label(f"{TRIP * u:.1f} s", W / 2, 1480, 150, (255, 90, 70) if u >= 1 else (255, 255, 255), 1.0)
        else:
            a = R.ramp(t, t_speed, 0.2)
            F.label("692,000 KM/H", W / 2, 1480, fit("692,000 KM/H", 130), R.AMBER, a)
        im = F.rgb()
        if t == 0.0:
            self.first = im
        if self.first is not None and t > self.total - 0.25:
            im = Image.blend(im, self.first, R.sm((t - (self.total - 0.25)) / 0.25))
        return im


def word_times(voice_wav):
    import whisper
    script = " ".join(b.get("caption_text", b["text"]) for b in BEATS)
    res = whisper.load_model("small").transcribe(voice_wav, word_timestamps=True, language="en", temperature=0.0,
                                                 condition_on_previous_text=False, initial_prompt=script)
    out = []
    for sg in res["segments"]:
        for w in sg["words"]:
            txt = w["word"].strip()
            if out and re.fullmatch(r",\d+[.,]?", txt):
                out[-1] = (out[-1][0] + txt, out[-1][1], w["end"]); continue
            start = w["start"]
            if out and re.search(r"[.,!?]$", out[-1][0]):
                start = max(start, w["end"] - 0.4)
            out.append((txt, start, w["end"]))
    return out


def chunks(words):
    n_script = sum(len(c.replace("-", " ").split()) for c in CAPS)
    if n_script != len(words):
        sys.exit(f"captions cover {n_script} words but {len(words)} were heard: {[w[0] for w in words]}")
    res, j = [], 0
    for c in CAPS:
        nw = len(c.replace("-", " ").split())
        res.append([re.sub(r"[.,!?]+$", "", c), words[j][1] - 0.04, words[j + nw - 1][2]])
        j += nw
    out = []
    for k, (c, a, last_end) in enumerate(res):
        b = res[k + 1][1] if k + 1 < len(res) else words[-1][2] + 0.6
        b = max(b, last_end + 0.1)                  # never clear before the caption's last word is finished
        if k + 1 < len(res):
            res[k + 1][1] = max(res[k + 1][1], b)   # the next caption waits for it
        out.append((c, a, b))
    return out


def main():
    os.makedirs(WORK, exist_ok=True)
    generate_voiceover(script_beats=BEATS, output_mp3=os.path.join(WORK, f"{STEM}_seq.mp3"), voice=VOICE,
                       pitch="+0Hz", work_dir=WORK)
    # place every line at its own time (line 3 must land on the arrival)
    starts, t = [], 0.0
    for i, s in enumerate(STARTS):
        d = _probe_duration(os.path.join(WORK, f"{STEM}_seq_beat{i + 1}.wav"))
        st = s if s is not None else t + GAP
        st = max(st, t - 0.3 if i else 0.0)   # may start inside the previous line's trailing silence
        starts.append(st); t = st + d
    total = t + 0.7
    voice = os.path.join(WORK, f"{STEM}.wav")
    ins, flt = [], []
    for i, st in enumerate(starts):
        ins += ["-i", os.path.join(WORK, f"{STEM}_seq_beat{i + 1}.wav")]
        flt.append(f"[{i}:a]adelay={int(st * 1000)}:all=1[a{i}]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex",
                    ";".join(flt) + ";" + "".join(f"[a{i}]" for i in range(len(starts)))
                    + f"amix=inputs={len(starts)}:normalize=0:duration=longest,apad=whole_dur={total:.3f},"
                      f"atrim=0:{total:.3f}[o]", "-map", "[o]", "-ar", "48000", "-ac", "2", voice], check=True)
    all_caps = chunks(word_times(voice))
    film = Film(total, all_caps[HOOK_CAPS:])
    print("line starts:", [round(s, 2) for s in starts], "total", round(total, 2))
    n = int(round(total * FPS))
    silent = os.path.join(WORK, f"{VID}_silent.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                            "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    for k in range(n):
        enc.stdin.write(np.asarray(film.frame(k / FPS)).tobytes())
    enc.stdin.close(); enc.wait()
    srt = os.path.join(WORK, f"{VID}_captions.srt")

    def ts(x):
        return f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{int(x % 60):02d},{int(round(x * 1000)) % 1000:03d}"
    with open(srt, "w") as f:
        f.write("\n\n".join(f"{k + 1}\n{ts(a)} --> {ts(b)}\n{c}" for k, (c, a, b) in enumerate(all_caps)) + "\n")
    bed = os.path.join(WORK, "ambient.wav"); generate_ambient_bed(total + 1.0, bed, preset="space", volume=0.2)
    # the race has no voice for ~2.5 s: a whoosh builds with the streak and hits on arrival
    race = os.path.join(WORK, "race.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-filter_complex",
                    f"anoisesrc=color=pink:duration={TRIP:.2f}:amplitude=0.9,highpass=f=300,lowpass=f=4000,"
                    f"afade=t=in:st=0:d={TRIP - 0.2:.2f}:curve=exp,afade=t=out:st={TRIP - 0.15:.2f}:d=0.15,volume=0.32,"
                    f"adelay={int(T0 * 1000)}:all=1[r];"
                    f"sine=f=70:duration=0.7,afade=t=out:st=0:d=0.7:curve=exp,volume=0.45,"
                    f"adelay={int((T0 + TRIP) * 1000)}:all=1[h];"
                    f"anullsrc=r=48000:cl=stereo:d={total:.3f}[z];[z][r][h]amix=inputs=3:duration=first:normalize=0[o]",
                    "-map", "[o]", "-ar", "48000", "-ac", "2", race], check=True)
    mix = os.path.join(WORK, "mix.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", voice, "-i", bed, "-i", race, "-filter_complex",
                    "[1:a]atrim=start=0.4,asetpts=PTS-STARTPTS[b];[0:a][b][2:a]amix=inputs=3:duration=first:normalize=0,"
                    f"atrim=0:{total:.3f},loudnorm=I=-14:TP=-2:LRA=11,alimiter=limit=0.7:level=false[o]", "-map", "[o]",
                    "-ar", "48000", mix], check=True)
    mux_video_audio_subs(silent, mix, srt, OUT, burn_captions=False)
    print(f"✅ {OUT} ({_probe_duration(OUT):.1f}s)")


if __name__ == "__main__":
    main()
