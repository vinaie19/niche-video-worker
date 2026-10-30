"""
ep25 v2: "Zoom Out From Earth to the Edge of the Universe" as a full-frame zoom-through.

v1 kept every object at true scale, which left ~10 s of tiny dots on black: the same flaw
that sank ep23 (162 views). v2 keeps the numbers true but always shows each step big:
a real NASA image filling the frame, then a fast fly-away into the next one (with a whoosh),
like the most-viewed space Shorts. It ends by diving into one Deep Field galaxy that becomes
Earth again, so the replay loops seamlessly.

  python longform/short_zoom_v2.py  ->  final_videos/sci_ep25_zoom_out_complete.mp4 (v1 kept as _v1)
"""
import math
import os
import subprocess
import sys

from PIL import ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
os.environ.setdefault("CHANNEL", "b")

import lf01_render as R  # noqa: E402
from audio_post import (_probe_duration, create_phrase_subtitles, generate_ambient_bed,  # noqa: E402
                        generate_voiceover, mux_video_audio_subs, shift_srt_file)

VID = "sci_ep25_zoom_out"
W, H, FPS = 1080, 1920, 30
R.W, R.H = W, H
WORK = os.path.join(ROOT, "temp_clips", f"{VID}_v2_audio")
OUT = os.path.join(ROOT, "final_videos", f"{VID}_complete.mp4")
STEM = f"{VID}_v2_voice"
VO_DELAY = 0.1
CY = 1130  # subject centre: below the mid-frame captions (~37% down), above the Shorts UI
VOICE = "en-US-AndrewMultilingualNeural"

BEATS = [
    dict(text="This is how small we really are.", phrases=["This is how small", "we really are."], rate="+6%", pause_ms=120),
    dict(text="The Moon, light gets there in about a second.", caption_text="The Moon, light gets there in about 1 second.",
         phrases=["The Moon,", "light gets there in about 1 second."], rate="+6%", pause_ms=120),
    dict(text="The Sun, eight minutes for light.", caption_text="The Sun, 8 minutes for light.",
         phrases=["The Sun,", "8 minutes for light."], rate="+6%", pause_ms=120),
    dict(text="Every planet, four hours.", caption_text="Every planet, 4 hours.",
         phrases=["Every planet,", "4 hours."], rate="+6%", pause_ms=120),
    dict(text="The nearest star, four years.", caption_text="The nearest star, 4 years.",
         phrases=["The nearest star,", "4 years."], rate="+6%", pause_ms=120),
    dict(text="Our galaxy, a hundred thousand years.", caption_text="Our galaxy, 100,000 years.",
         phrases=["Our galaxy,", "100,000 years."], rate="+6%", pause_ms=120),
    dict(text="Andromeda, two and a half million years.", caption_text="Andromeda, 2.5 million years.",
         phrases=["Andromeda,", "2.5 million years."], rate="+6%", pause_ms=120),
    dict(text="And almost every dot here is a galaxy.", phrases=["And almost every dot", "here is a galaxy."],
         rate="+4%", pause_ms=120),
    dict(text="One of them is home.", phrases=["One of them", "is home."], rate="+0%", pause_ms=0),
]
LIGHT = ["EARTH", "light: 1.3 seconds", "light: 8 minutes", "light: 4 hours", "light: 4.2 years",
         "light: 100,000 years", "light: 2.5 million years", "", ""]
K = 3.2      # scale ratio between neighbouring steps (fly-away depth)
XF = 0.5     # transition length (s), centred on each beat boundary


def depth(t, st):
    """Continuous depth z: holds near the beat index, then flies to the next one at the boundary."""
    for i, (s, e) in enumerate(st):
        nxt = st[i + 1][0] if i + 1 < len(st) else None
        if nxt is None or t < nxt - XF / 2:
            base = i + 0.12 * R.sm((t - s) / max(0.5, e - s))  # slow drift so nothing is ever static
            if nxt is not None and t > nxt - XF / 2 - 0.0:
                pass
            return base
        if t < nxt + XF / 2:
            u = R.sm((t - (nxt - XF / 2)) / XF)
            return (i + 0.12) + (1 - 0.12) * u
    return len(st) - 1 + 0.12


def scale_alpha(z, i):
    d = z - i                      # >0: this layer is receding (getting small)
    s = K ** (-d)
    a = 1.0 - R.sm((abs(d) - 0.15) / 0.75)
    return s, max(0.0, a)


def star_burst(F, cx, cy, size, alpha):
    if alpha <= 0:
        return
    F.paste(R.halo_img(int(size * 0.9), (255, 230, 200)), cx, cy, alpha)
    F.paste(R.halo_img(int(size * 0.35), (255, 250, 240)), cx, cy, alpha)
    dr = F.draw()
    for ang in (0, 90, 45, 135):
        L = size * (1.6 if ang in (0, 90) else 0.8)
        dx, dy = L * math.cos(math.radians(ang)), L * math.sin(math.radians(ang))
        for w, a in ((6, 60), (2, 200)):
            dr.line((cx - dx, cy - dy, cx + dx, cy + dy), fill=(255, 245, 230, int(a * alpha)), width=w)
    dr.ellipse((cx - size * 0.09, cy - size * 0.09, cx + size * 0.09, cy + size * 0.09), fill=(255, 255, 255, int(255 * alpha)))


def frame(t, st, total):
    z = depth(t, st)
    F = R.Frame()
    F.stars(0.85, zoom=1.0 + 0.04 * z, drift=(0.002 * t, 0.001 * t))
    from ep23_planet_stack import saturn_sprite  # cached below
    global _SAT
    try:
        _SAT
    except NameError:
        _SAT = saturn_sprite()
    for i in range(len(st)):
        s, a = scale_alpha(z, i)
        if a <= 0.01:
            continue
        if i == 0:   # Earth
            F.planet("earth", W / 2, CY, min(2600, 960 * s), a)
        elif i == 1:  # Moon
            F.planet("moon", W / 2, CY, min(2600, 900 * s), a)
        elif i == 2:  # Sun
            d = min(2600, 1150 * s)
            F.planet("sun", W / 2, CY, d, a, halo=0.6 if d < 1300 else 0.0, halo_col=(255, 150, 60))
        elif i == 3:  # every planet: Jupiter, Saturn, Neptune receding in a line
            sprite, (fx, fy) = _SAT
            for k, (name, dx, dy, d) in enumerate((("jupiter", -170, -260, 620), ("saturn", 200, 120, 520),
                                                    ("neptune", -120, 470, 300))):
                ka = a * R.ramp(t, st[3][0] + 0.18 * k, 0.25)
                x, y, dd = W / 2 + dx * s, CY + dy * s, min(2400, d * s)
                if name == "saturn":
                    img = sprite.resize((max(4, int(sprite.width * dd / 900)), max(4, int(sprite.height * dd / 900))))
                    F.paste(img, x + (0.5 - fx) * img.width, y + (0.5 - fy) * img.height, ka)
                else:
                    F.planet(name, x, y, dd, ka)
        elif i == 4:  # the nearest star
            star_burst(F, W / 2, CY, min(1300, 700 * s), a)
        elif i == 5:
            F.photo("milkyway", zoom=1.05 * s, cx=0.5, cy=0.47, rot=-4 * z, alpha=a)
        elif i == 6:
            F.photo("andromeda", zoom=1.4 * s, cx=0.5, cy=0.5, rot=-30 + 3 * z, alpha=a)
        elif i >= 7:  # the Deep Field twice in a row: zooming out of galaxies into more galaxies
            F.photo("udf", zoom=max(0.3, s), cx=0.52, cy=0.46, alpha=a)
    # loop: the last ~0.7 s dives into one galaxy that becomes Earth again
    tl = total - 0.75
    if t > tl:
        u = R.sm((t - tl) / 0.75)
        F.fade(0.85 * u)
        F.planet("earth", W / 2, CY, R.lerp_log(8, 960, u), u)
    lab = LIGHT[min(len(LIGHT) - 1, int(round(z)))]
    if lab:
        F.label(lab, W / 2, 170, 66, R.AMBER, 1.0 - R.sm((abs(z - round(z)) - 0.25) / 0.2))
    return F.rgb()


def whoosh_track(times, total, path):
    """Synthesised whooshes (pink noise, band-limited, swelling) at each transition."""
    parts, labels = [], []
    for k, tt in enumerate(times):
        parts.append(f"anoisesrc=color=pink:duration=0.7:amplitude=0.6,highpass=f=250,lowpass=f=3500,"
                     f"afade=t=in:st=0:d=0.35,afade=t=out:st=0.35:d=0.35,volume=0.22,"
                     f"adelay={int(max(0, tt - 0.35) * 1000)}:all=1[w{k}]")
        labels.append(f"[w{k}]")
    fc = ";".join(parts) + ";" + "".join(labels) + f"amix=inputs={len(times)}:normalize=0,atrim=0:{total:.3f}[o]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-filter_complex", fc, "-map", "[o]", "-ar", "48000", "-ac", "2", path], check=True)


def main():
    os.makedirs(WORK, exist_ok=True)
    generate_voiceover(script_beats=BEATS, output_mp3=os.path.join(WORK, f"{STEM}.mp3"), voice=VOICE,
                       pitch="+0Hz", work_dir=WORK)
    t, st = VO_DELAY, []
    for i, b in enumerate(BEATS, start=1):
        d = _probe_duration(os.path.join(WORK, f"{STEM}_beat{i}.wav"))
        st.append((t, t + d)); t += d + b["pause_ms"] / 1000.0
    total = t + 0.05
    if "--preview" in sys.argv:
        from PIL import Image
        ts = [0.3] + [s + 0.6 for s, _ in st[1:]] + [st[3][0] + 0.9, total - 0.3]
        ims = [frame(x, st, total).resize((216, 384)) for x in ts]
        sheet = Image.new("RGB", (216 * len(ims), 384))
        for i, im in enumerate(ims):
            sheet.paste(im, (216 * i, 0))
        p = os.path.join(os.environ.get("PREVIEW_DIR", "/tmp"), "zoom_v2_preview.png"); sheet.save(p)
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
    wh = os.path.join(WORK, "whoosh.wav"); whoosh_track([s for s, _ in st[1:]] + [total - 0.6], total, wh)
    mix = os.path.join(WORK, "mix.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, f"{STEM}.mp3"), "-i", bed, "-i", wh,
                    "-filter_complex",
                    f"[0:a]adelay={int(VO_DELAY*1000)}:all=1,apad[v];[v][1:a][2:a]amix=inputs=3:duration=shortest:normalize=0,"
                    f"atrim=0:{total:.3f},loudnorm=I=-14:TP=-1.5:LRA=11[o]", "-map", "[o]", "-ar", "48000", mix], check=True)
    if os.path.isfile(OUT) and not os.path.isfile(OUT.replace(".mp4", "_v1.mp4")):
        os.replace(OUT, OUT.replace(".mp4", "_v1.mp4"))
    mux_video_audio_subs(silent, mix, srt, OUT, burn_captions=True, caption_style="clean_heavy_safe")
    print(f"✅ {OUT} ({_probe_duration(OUT):.1f}s)")


if __name__ == "__main__":
    main()
