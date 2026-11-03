"""
ep28 v2 Short: "Your Sunlight Is Older Than the Pyramids" (9:16, ~19 s, $0 local).

First Short built on real NASA *video* instead of still photos with code zooms (the owner judged the
still-photo Shorts "not even average"). Every shot is moving footage, cropped to 9:16 from 4K where
possible, with a slow sub-pixel camera move on top:

  1  SDO 4K full-disc Sun (orange)           "If the Sun vanished right now..."   claim on frame 1
  2  ISS 4K: the Sun blazing past Earth's limb  "...keep coming for 8 more minutes"   clock starts
  3  ISS 4K: sunlit Earth (Sahara to ocean)  "...how long it takes to reach you"  clock hits 8:20, Earth goes dark
  4  SDO 4K: M6.7 flare close-up             "But that light is far older..."     the turn
  5  SDO: Phoenix prominence eruption        "...thousands of years trapped inside"  10,000+ YEARS counter
  6  Giza at sunset (LOC, 1930s), warm-toned  "...older than the pyramids."       dissolves back to frame 1

Physics: 1 AU / c = 8 min 19 s. Energy made in the core random-walks out of the radiative zone for
~10,000 to ~170,000 years (estimates vary), so "thousands of years" and "older than the pyramids"
(~4,500 years) are both safe.

Footage lives in local_runner/nasa_video (not in git); see i2v_stills/sci_ep28_sun_v2/SOURCES.md.

  python longform/short_sun_v2.py [--preview]  ->  final_videos/sci_ep28_sun_v2_complete.mp4
"""
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
os.environ.setdefault("CHANNEL", "b")

import lf01_render as R  # noqa: E402
from audio_post import (_probe_duration, create_phrase_subtitles, generate_ambient_bed,  # noqa: E402
                        generate_voiceover, mux_video_audio_subs, shift_srt_file)
from short_zoom_v2 import whoosh_track  # noqa: E402

VID = "sci_ep28_sun_v2"
W, H, FPS = 1080, 1920, 30
R.W, R.H = W, H
OW, OH = 1242, 2208  # each shot is cut 15% larger than the screen, so the camera can move inside it
NASA = os.path.join(ROOT, "nasa_video")
STILLS = os.path.join(ROOT, "i2v_stills", VID)
WORK = os.path.join(ROOT, "temp_clips", f"{VID}_audio")
OUT = os.path.join(ROOT, "final_videos", f"{VID}_complete.mp4")
STEM = f"{VID}_voice"
VO_DELAY = 0.05
VOICE = "en-US-AndrewMultilingualNeural"
XF = 0.3
LIGHT_S = 8 * 60 + 20

BEATS = [
    dict(text="If the Sun vanished right now, you wouldn't even know.",
         phrases=["If the Sun vanished right now,", "you wouldn't even know."], rate="+8%", pause_ms=80),
    dict(text="Its light would keep coming for eight more minutes.",
         caption_text="Its light would keep coming for 8 more minutes.",
         phrases=["Its light would keep coming", "for 8 more minutes."], rate="+6%", pause_ms=80),
    dict(text="That's how long it takes to reach you.",
         phrases=["That's how long", "it takes to reach you."], rate="+4%", pause_ms=250),
    dict(text="But that light is far older than eight minutes.",
         caption_text="But that light is far older than 8 minutes.",
         phrases=["But that light is far older", "than 8 minutes."], rate="+4%", pause_ms=100),
    # "It spent..." was heard as "It's been..." (Whisper, and plausibly viewers): plain words only
    dict(text="It was trapped inside the Sun for thousands of years.",
         phrases=["It was trapped inside the Sun", "for thousands of years."], rate="+4%", pause_ms=120),
    dict(text="So the sunlight on your face right now is older than the pyramids.",
         phrases=["So the sunlight on your face", "right now", "is older than the pyramids."],
         rate="+2%", pause_ms=0),
]

# NASA's ISS 4K reel is 24p padded to 29.97 with a repeated frame every 5 (a visible hitch), and the
# Phoenix clip is 30p doubled to 59.94 with blended in-betweens. Strip both back to unique frames and
# play each once at 30 fps (ISS: 1.25x real time).
ISS_24P = "mpdecimate,setpts=N/(30*TB)"  # (decimate sometimes drops the wrong frame)
PHOENIX_30P = "framestep=2,setpts=N/(30*TB)"

# Shots: source, start (s), playback speed, scale (canvas px per source px), source point at the
# canvas centre (fractions), camera zoom at the start and end of the beat (1 = canvas px = screen px).
SHOTS = [
    dict(src="sdo_flare_4k.mp4", t0=10.8, speed=1.0, k=1.03, cx=0.49, cy=0.48, z=(1.00, 1.06)),
    dict(src="iss4k_sunburst.mp4", t0=2.0, speed=1.25, pre=ISS_24P, k=0.80, cx=0.53, cy=0.52, z=(0.98, 1.12)),
    dict(src="iss4k_day.mp4", t0=7.0, speed=1.25, pre=ISS_24P, k=0.80, cx=0.50, cy=0.50, z=(1.00, 1.10)),
    dict(src="sdo_flare_4k.mp4", t0=26.0, speed=1.0, k=1.04, cx=0.70, cy=0.55, z=(1.00, 1.14)),
    dict(src="sdo_phoenix.mp4", t0=54.0, speed=1.0, pre=PHOENIX_30P, k=3.08, cx=0.60, cy=0.50, z=(1.00, 1.06)),
    dict(still="giza_warm.jpg", k=0.76, cx=0.645, cy=0.47, z=(1.08, 0.99)),
]
TOP = [("IF THE SUN", "VANISHED..."), None, None, ("BUT THAT LIGHT", "IS OLDER"), None,
       ("OLDER THAN", "THE PYRAMIDS")]


def probe_size(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                          "-of", "json", path], capture_output=True, text=True, check=True).stdout
    s = json.loads(out)["streams"][0]
    return s["width"], s["height"]


class Shot:
    """Streams one shot's canvas frames (OW x OH, 30 fps) from ffmpeg in time order."""

    def __init__(self, spec, dur):
        self.spec, self.k, self.last = spec, -1, None
        if "still" in spec:
            im = Image.open(os.path.join(STILLS, spec["still"])).convert("RGB")
            self.still = self._place(im)
            return
        path = os.path.join(NASA, spec["src"])
        iw, ih = probe_size(path)
        sw, sh = int(round(iw * spec["k"] / 2)) * 2, int(round(ih * spec["k"] / 2)) * 2
        x, y = int(round(spec["cx"] * sw)), int(round(spec["cy"] * sh))
        retime = spec.get("pre") or f"setpts=(PTS-STARTPTS)/{spec['speed']}"
        vf = (f"{retime}{'' if spec.get('pre') else f',fps={FPS}'},scale={sw}:{sh}:flags=lanczos,"
              f"pad={sw + OW}:{sh + OH}:{OW // 2}:{OH // 2},crop={OW}:{OH}:{x}:{y}")
        need = (dur + XF + 0.6) * spec["speed"]
        self.p = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-threads", "4", "-ss", f"{spec['t0']:.3f}", "-i", path, "-t", f"{need:.3f}",
                                   "-vf", vf, "-filter_threads", "2", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, stdin=subprocess.DEVNULL)

    def _place(self, im):
        s = self.spec
        sw, sh = im.width * s["k"], im.height * s["k"]
        coeffs = (1 / s["k"], 0, s["cx"] * im.width - OW / 2 / s["k"], 0, 1 / s["k"], s["cy"] * im.height - OH / 2 / s["k"])
        return im.transform((OW, OH), Image.AFFINE, coeffs, resample=Image.BICUBIC)

    def get(self, k):
        if "still" in self.spec:
            return self.still
        while self.k < k:
            buf = self.p.stdout.read(OW * OH * 3)
            if len(buf) < OW * OH * 3:  # source ran out: hold the last frame (should not happen; the QA stall check would flag it)
                break
            self.last = Image.frombuffer("RGB", (OW, OH), buf, "raw", "RGB", 0, 1).copy()
            self.k += 1
        return self.last

    def close(self):
        if "still" not in self.spec:
            self.p.stdout.close(); self.p.wait()


def camera(canvas, z):
    """Sub-pixel zoom about the canvas centre onto the 1080x1920 screen."""
    c = 1 / z
    return canvas.transform((W, H), Image.AFFINE, (c, 0, OW / 2 - W / 2 * c, 0, c, OH / 2 - H / 2 * c),
                            resample=Image.BICUBIC)


def timer_value(t, st):
    t0, t1 = st[1][0], st[2][0] + 0.75 * (st[2][1] - st[2][0])
    if t < t0:
        return None
    return int(round(LIGHT_S * min(1.0, (t - t0) / (t1 - t0)) ** 1.15)), t1


class Film:
    def __init__(self, st, total):
        self.st, self.total = st, total
        self.bounds = [0.0] + [s for s, _ in st[1:]] + [total]
        self.shots = {}
        self.first = None

    def shot(self, i):
        if i not in self.shots:
            self.shots[i] = Shot(SHOTS[i], self.bounds[i + 1] - self.bounds[i])
            for j in [j for j in self.shots if j < i - 1]:
                self.shots.pop(j).close()
        return self.shots[i]

    def picture(self, i, t):
        s0, s1 = self.bounds[i], self.bounds[i + 1]
        u = min(1.0, max(0.0, (t - s0) / (s1 - s0)))
        z0, z1 = SHOTS[i]["z"]
        im = camera(self.shot(i).get(max(0, int(round((t - s0) * FPS)))), R.lerp(z0, z1, R.sm(u) * 0.5 + u * 0.5))
        if i == 2:  # the moment the clock hits 8:20 the last sunlight arrives: sunlit Earth fades to night
            _, t_out = timer_value(t, self.st)
            e = R.ramp(t, t_out, 0.6)
            if e > 0.001:
                im = ImageEnhance.Brightness(im).enhance(1.0 - 0.72 * e)  # dimmed to night, still visible
                im = Image.blend(im, Image.new("RGB", (W, H), (10, 20, 50)), 0.3 * e)
        return im

    def overlays(self, F, i, t, k):
        """Beat i's text, drawn at opacity k (the clock ignores k across the 1 -> 2 cut: it never blinks)."""
        st = self.st
        clock_k = 1.0 if (i == 2 and t < st[2][0] + XF) else k
        if k <= 0.01 and clock_k <= 0.01:
            return
        if TOP[i] and k > 0.01:
            a = k
            if i == len(TOP) - 1:  # clear the last label before the loop dissolve, so two labels never overlap
                a *= 1.0 - R.ramp(t, self.total - 0.5, 0.2)
            F.label(TOP[i][0], W / 2, 210, 96, (255, 255, 255), a)
            # on the warm Giza photo amber vanishes into the sky, so the last label's second line is pale gold
            F.label(TOP[i][1], W / 2, 330, 92, (255, 236, 160) if i == 5 else R.AMBER, a)
        tv = timer_value(t, st)
        if tv and (i == 2 or (i == 1 and t < st[2][0])):  # one clock, running straight across the 1 -> 2 cut
            v, _ = tv
            done = v >= LIGHT_S
            F.label(f"{v // 60}:{v % 60:02d}", W / 2, 300, 170, (255, 90, 70) if done else (255, 255, 255), clock_k)
            F.label("LIGHT RUNS OUT" if done else "SINCE THE SUN VANISHED", W / 2, 430, 46, R.AMBER, clock_k)
        if i == 4 and k > 0.01:  # how long the energy was stuck inside: counts up to 10,000+
            s0, s1 = self.bounds[4], self.bounds[5]
            x = R.ramp(t, s0 + 0.2, (s1 - s0) * 0.6)
            n = int(round(10000 * x ** 0.6 / 100.0)) * 100
            F.label(f"{n:,}" + ("+" if x >= 0.999 else ""), W / 2, 280, 170, (255, 255, 255), k)
            F.label("YEARS INSIDE THE SUN", W / 2, 415, 62, R.AMBER, k)

    def frame(self, t):
        st = self.st
        i = max(k for k in range(len(st)) if st[k][0] <= t or k == 0)
        s0 = st[i][0]
        F = R.Frame()
        F.im = self.picture(i, t)
        if i > 0 and t < s0 + XF:  # crossfade: the previous shot keeps playing underneath
            F.im = Image.blend(self.picture(i - 1, t), F.im, R.sm((t - s0) / XF))
        # On-screen text: at each cut the old text fades out over the first half of the crossfade and the
        # new text fades in over the second half, so text never pops off in one frame or overlaps
        if i > 0 and t < s0 + XF:
            self.overlays(F, i - 1, t, 1.0 - R.ramp(t, s0, XF / 2))
        self.overlays(F, i, t, 1.0 if i == 0 else R.ramp(t, s0 + XF / 2, XF / 2))
        im = F.rgb()
        if t == 0.0:
            self.first = im
        if self.first is not None and t > self.total - 0.25:  # quick dissolve into frame 1: seamless loop, not a soft blur
            im = Image.blend(im, self.first, R.sm((t - (self.total - 0.25)) / 0.25))
        return im


def main():
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
        ts = sorted({0.0, 1.5} | {round(s + 0.7, 3) for s, _ in st[1:]} | {round(st[2][1] - 0.1, 3), round(total - 0.6, 3)})
        ks = {int(round(x * FPS)) for x in ts}
        ims = []
        for k in range(max(ks) + 1):  # frames must be pulled in order from the streams
            im = film.frame(k / FPS)
            if k in ks:
                ims.append(im.resize((216, 384)))
        sheet = Image.new("RGB", (216 * len(ims), 384))
        for k, im in enumerate(ims):
            sheet.paste(im, (216 * k, 0))
        p = os.path.join(os.environ.get("PREVIEW_DIR", "/tmp"), "sun_v2_preview.png"); sheet.save(p)
        print("preview ->", p, round(total, 2), [round(s, 2) for s, _ in st]); return
    silent = os.path.join(WORK, f"{VID}_silent.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                            "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    for k in range(n):
        enc.stdin.write(np.asarray(film.frame(k / FPS)).tobytes())
    enc.stdin.close(); enc.wait()
    srt = os.path.join(WORK, f"{VID}_captions.srt")
    create_phrase_subtitles(BEATS, work_dir=WORK, stem=STEM, srt_path=srt, max_words=5)
    shift_srt_file(srt, int(VO_DELAY * 1000))
    bed = os.path.join(WORK, "ambient.wav"); generate_ambient_bed(total + 1.0, bed, preset="space", volume=0.2)  # no dead air between lines
    wh = os.path.join(WORK, "whoosh.wav"); whoosh_track([s for s, _ in st[1:]], total, wh)
    mix = os.path.join(WORK, "mix.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, f"{STEM}.mp3"), "-i", bed, "-i", wh,
                    "-filter_complex",
                    f"[0:a]adelay={int(VO_DELAY*1000)}:all=1,apad[v];"
                    # skip the bed's 0.35 s fade-in and drop its fade-out: full level from frame 1 to the loop point
                    f"[1:a]atrim=start=0.4,asetpts=PTS-STARTPTS[b];[v][b][2:a]amix=inputs=3:duration=shortest:normalize=0,"
                    f"atrim=0:{total:.3f},loudnorm=I=-14:TP=-1.5:LRA=11[o]", "-map", "[o]", "-ar", "48000", mix], check=True)
    mux_video_audio_subs(silent, mix, srt, OUT, burn_captions=True, caption_style="clean_heavy_safe")
    print(f"✅ {OUT} ({_probe_duration(OUT):.1f}s)")


if __name__ == "__main__":
    main()
