"""
ep24 Short cut from LF01: "This marble is Earth... the Sun is a football pitch away" (9:16, $0).

A feeder Short for the long-form "How Big Is the Universe? (If Earth Were 1 cm)": same scale,
same real NASA imagery, vertical layout, picture kept clear of the mid-frame captions
(clean_heavy_safe, ~62% down) and the bottom 25% Shorts UI. Set LF01 as its Related video.

  python longform/short_lf01_sun.py   ->  final_videos/sci_ep24_sun_117m_complete.mp4
"""
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
os.environ.setdefault("CHANNEL", "b")

import lf01_render as R  # noqa: E402  (reuses the LF01 drawing primitives + assets)
from audio_post import (_probe_duration, create_phrase_subtitles, generate_ambient_bed,  # noqa: E402
                        generate_voiceover, mux_video_audio_subs, shift_srt_file)

VID = "sci_ep24_sun_117m"
W, H, FPS = 1080, 1920, 30
R.W, R.H = W, H  # the primitives read these module globals
WORK = os.path.join(ROOT, "temp_clips", f"{VID}_audio")
OUT = os.path.join(ROOT, "final_videos", f"{VID}_complete.mp4")
STEM = f"{VID}_complete_voice"
VO_DELAY = 0.1

BEATS = [
    dict(text="This marble is Earth, shrunk to one centimetre.", caption_text="This marble is Earth, shrunk to 1 cm.",
         phrases=["This marble is Earth,", "shrunk to 1 cm."], rate="+6%", pause_ms=150),
    dict(text="At the same scale, the Sun is a glowing ball, over a metre wide.",
         phrases=["At the same scale,", "the Sun is a glowing ball,", "over a metre wide."], rate="+4%", pause_ms=150),
    dict(text="And it's not next to us.", phrases=["And it's not next to us."], rate="+4%", pause_ms=100),
    dict(text="It's a hundred and seventeen metres away, a whole football pitch.",
         caption_text="It's 117 metres away, a whole football pitch.",
         phrases=["It's 117 metres away,", "a whole football pitch."], rate="+2%", pause_ms=150),
    dict(text="Even light needs eight minutes to cross it.", caption_text="Even light needs 8 minutes to cross it.",
         phrases=["Even light needs", "8 minutes to cross it."], rate="+2%", pause_ms=150),
    dict(text="And that's the closest star.", phrases=["And that's", "the closest star."], rate="-2%", pause_ms=0),
]


def timeline():
    os.makedirs(WORK, exist_ok=True)
    generate_voiceover(script_beats=BEATS, output_mp3=os.path.join(WORK, f"{STEM}.mp3"), voice="guy",
                       pitch="-1Hz", work_dir=WORK)
    t, starts = VO_DELAY, []
    for i, b in enumerate(BEATS, start=1):
        d = _probe_duration(os.path.join(WORK, f"{STEM}_beat{i}.wav"))
        starts.append((t, t + d))
        t += d + b["pause_ms"] / 1000.0
    return starts, t + 0.05  # end on the last word


def frame(t, st, total):
    sm, ramp, eo, lerp, lerp_log = R.sm, R.ramp, R.eo, R.lerp, R.lerp_log
    (b1, _), (b2, _), (b3, _), (b4, _), (b5, e5), (b6, _) = st
    F = R.Frame()
    F.stars(0.8, drift=(t * 0.004, t * 0.002))
    cx = W / 2
    # Layout: labels at the top (~170), captions in the middle third (clean_heavy_safe sits
    # ~37% down), subject in 820-1400, Shorts UI below ~1440.
    top, bot = 830, 1400
    SY = 1110  # subject centre for the big Earth / Sun
    ppm = (bot - top) / 117.4
    pw = 68 * ppm
    kp = ramp(t, b3 + 0.2, 0.9)  # pitch reveal
    zo = ramp(t, b6 + 0.1, 1.2)  # final zoom-out
    zs = lerp(1.0, 0.28, eo(zo))
    yc = (top + bot) / 2

    def Z(x, y):
        return cx + (x - cx) * zs, yc + (y - yc) * zs

    if kp > 0:
        dr = F.draw()
        fx0, fx1 = cx - pw / 2, cx + pw / 2
        fy0, fy1 = top + 6.2 * ppm, bot - 6.2 * ppm
        a = int(200 * kp)
        p0, p1 = Z(fx0, fy0), Z(fx1, fy1)
        dr.rectangle((*p0, *p1), fill=(30, 110, 45, int(140 * kp)), outline=(235, 255, 235, a), width=3)
        m0, m1 = Z(fx0, yc), Z(fx1, yc)
        dr.line((*m0, *m1), fill=(235, 255, 235, a), width=3)
        r = 9.15 * ppm * zs
        c = Z(cx, yc)
        dr.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), outline=(235, 255, 235, a), width=3)
        for gy, sgn in ((fy0, 1), (fy1, -1)):
            q0 = Z(cx - 20.2 * ppm, gy); q1 = Z(cx + 20.2 * ppm, gy + sgn * 16.5 * ppm)
            dr.rectangle((min(q0[0], q1[0]), min(q0[1], q1[1]), max(q0[0], q1[0]), max(q0[1], q1[1])),
                         outline=(235, 255, 235, a), width=3)
    # Earth: big -> marble (beat 1), then down to the bottom goal (beat 3)
    u1 = eo((t - b1) / 1.4)
    ed = lerp_log(560, 60, u1)
    ey = lerp(SY, bot, sm((t - b3) / 1.0))
    ed = lerp(ed, 10, sm((t - b3) / 1.0))
    ex, ey2 = Z(cx, ey)
    F.planet("earth", ex, ey2, max(9, ed * (zs if zo > 0 else 1)), halo=1.2 * kp, halo_col=(120, 170, 255))
    if t < b3 + 0.4:  # "EARTH = 1 cm" from frame 0 (scroll-stop), ruler once it's a marble
        k = ramp(t, b1 + 1.0) * (1 - ramp(t, b3, 0.4))
        F.ruler(cx - 30, cx + 30, SY + 75, 60, 1, step_lbl=1, alpha=k)
        F.label("EARTH = 1 cm", cx, 170, 64, R.AMBER, (1 - ramp(t, b2 - 0.2, 0.3)))
    # Sun: grows beside the marble (beat 2), then moves to the top goal (beat 3)
    ks = ramp(t, b2 + 0.1, 0.8)
    if ks > 0:
        sd_big = 560
        ug = eo((t - b2 - 0.1) / 1.2)
        mv = sm((t - b3) / 1.0)
        sd = lerp(lerp(30, sd_big, ug), 1.09 * ppm, mv)
        sy = lerp(SY, top, mv)
        sx, sy2 = Z(cx, sy)
        F.planet("sun", sx, sy2, max(16, sd * (zs if zo > 0 else 1)), ks, halo=0.5 + 1.0 * mv, halo_col=(255, 160, 60))
        F.label("SUN = 1.09 m", cx, 170, 64, R.AMBER, ramp(t, b2 + 0.2, 0.4) * (1 - ramp(t, b3, 0.4)))
    # 117 m
    k4 = ramp(t, b4 + 0.2) * (1 - ramp(t, b5, 0.3))
    if k4 > 0:
        F.dashed(cx + pw / 2 + 40, top, cx + pw / 2 + 40, bot, (255, 220, 150), 4, alpha=k4)
    if ramp(t, b4 + 0.2) > 0 and zo < 1:
        F.label("117 m", cx + pw / 2 + 110, (top + bot) / 2, 44, R.AMBER, ramp(t, b4 + 0.4) * (1 - zo))
        F.label("117 m", cx, 170, 96, R.AMBER, k4)
    # light pulse Sun -> Earth with a running timer (accelerated)
    if b5 + 0.2 <= t < b6 + 0.2:
        x = min(1.0, (t - b5 - 0.2) / max(1.2, e5 - b5 - 0.2))
        F.pulse(cx, lerp(top, bot, x), 1.0, r=12)
        secs = int(499 * x)
        F.label(f"light: {secs // 60} min {secs % 60:02d} s", cx, 170, 64, (255, 245, 210))
    # twist: zoom out, it's the CLOSEST star
    if zo > 0:
        F.label("THE CLOSEST STAR", cx, 170, 84, R.WHITE, zo)
    img = F.rgb()
    return img


def main():
    st, total = timeline()
    n = int(round(total * FPS))
    silent = os.path.join(WORK, f"{VID}_silent.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                            "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    for f in range(n):
        enc.stdin.write(frame(f / FPS, st, total).tobytes())
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
