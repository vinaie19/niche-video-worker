"""
ep29 version B: the same picture and audio as short_sgra.py (version A), but one text system: big
word-synced captions instead of the top labels (owner asked whether captions should come back; muted
viewers otherwise miss the story). The countdown and the target ring stay as graphics.

Caption timing comes from Whisper word times on the clean voice track, so each chunk appears as it is said.

  python longform/short_sgra_captions.py   (after short_sgra.py)  ->  final_videos/sci_ep29_sgra_captions_complete.mp4
"""
import os
import re
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)

import lf01_render as R  # noqa: E402
import short_sgra as G  # noqa: E402
from audio_post import _probe_duration, mux_video_audio_subs  # noqa: E402

OUT = os.path.join(G.ROOT, "final_videos", f"{G.VID}_captions_complete.mp4")
CAP_Y = 700           # usual Shorts caption height, above the target ring; the countdown stays at 1400
CAP_SIZE = 112


def word_times():
    """(text, start, end) for every spoken word, on the final timeline; Whisper's split numbers re-joined."""
    import whisper
    res = whisper.load_model("small").transcribe(os.path.join(G.WORK, f"{G.STEM}.mp3"), word_timestamps=True,
                                                 language="en")
    out = []
    for sg in res["segments"]:
        for w in sg["words"]:
            txt = w["word"].strip()
            if out and re.fullmatch(r",\d+[.,]?", txt):  # "26" ",000" -> "26,000"
                out[-1] = (out[-1][0] + txt, out[-1][1], w["end"]); continue
            out.append((txt, w["start"] + G.VO_DELAY, w["end"] + G.VO_DELAY))
    return out


# hand-split captions (readable 1-3 word units); joined they are exactly the script's words, in order
CAPS = ["THIS IS A TRIP", "TO THE BLACK HOLE", "AT THE CENTER", "OF OUR GALAXY.", "26,000", "LIGHT-YEARS,",
        "THROUGH BILLIONS", "OF STARS,", "ALL THE WAY", "TO THE CENTER.", "HIDING THERE", "IS SOMETHING",
        "4 MILLION TIMES", "HEAVIER", "THAN THE SUN.", "IT SWALLOWS", "ALL LIGHT,", "SO FOR DECADES",
        "IT STAYED", "INVISIBLE.", "UNTIL 2022,", "WHEN WE TOOK", "ITS FIRST", "REAL PHOTO."]


def chunks(words):
    """Time each caption by the spoken words it covers (counted as Whisper splits them: 'light-years' = 2)."""
    n_script = sum(len(c.replace("-", " ").split()) for c in CAPS)
    if n_script != len(words):
        sys.exit(f"captions cover {n_script} words but {len(words)} were heard: fix CAPS or the voice")
    res, j = [], 0
    for c in CAPS:
        res.append([re.sub(r"[.,!?]+$", "", c), words[j][1] - 0.04])
        j += len(c.replace("-", " ").split())
    for k in range(len(res)):
        res[k].append(res[k + 1][1] if k + 1 < len(res) else words[-1][2] + 0.6)
    return [tuple(r) for r in res]


def main():
    G.load()
    st, t = [], G.VO_DELAY
    for i, b in enumerate(G.BEATS, start=1):
        d = _probe_duration(os.path.join(G.WORK, f"{G.STEM}_beat{i}.wav"))
        st.append((t, t + d)); t += d + b["pause_ms"] / 1000.0
    total = t + 0.7
    caps = chunks(word_times())
    # the countdown starts once "26,000 light-years" has been said, so two different numbers never share the screen
    G.COUNTER_START = next(a for c, a, b in caps if c.startswith("THROUGH"))
    print("captions:", [(c, round(a, 2)) for c, a, _ in caps])
    G.TOP = [None] * len(G.BEATS)  # one text system: captions only (countdown + ring remain as graphics)
    film = G.Film(st, total)
    base_frame = film.frame

    def frame(tt):
        im = base_frame(tt)
        cap = next((c for c, a, b in caps if a <= tt < b), None)
        if cap and tt < total - 0.3:  # clear before the loop dissolve
            F = R.Frame(); F.im = im
            F.label(cap, G.W / 2, CAP_Y, G.fit(cap, CAP_SIZE), (255, 255, 255), 1.0)
            im = F.rgb()
        return im

    n = int(round(total * G.FPS))
    silent = os.path.join(G.WORK, f"{G.VID}_captions_silent.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{G.W}x{G.H}",
                            "-r", str(G.FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                            "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    for k in range(n):
        enc.stdin.write(np.asarray(frame(k / G.FPS)).tobytes())
    enc.stdin.close(); enc.wait()
    srt = os.path.join(G.WORK, f"{G.VID}_captions.srt")
    mux_video_audio_subs(silent, os.path.join(G.WORK, "mix.wav"), srt, OUT, burn_captions=False)
    print(f"✅ {OUT} ({_probe_duration(OUT):.1f}s)")


if __name__ == "__main__":
    main()
