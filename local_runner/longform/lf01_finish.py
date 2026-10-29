"""LF01 step 3: mix voice + space ambience (loudness-normalized), mux, write CC subtitles + chapters."""
import json
import os
import subprocess
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from audio_post import _probe_duration, generate_ambient_bed  # noqa: E402

WORK = os.path.join(ROOT, "temp_clips", "lf01_universe_scale_audio")
SILENT = os.path.join(ROOT, "temp_clips", "lf01_universe_scale_silent.mp4")
OUT_DIR = os.path.join(ROOT, "final_videos")
OUT = os.path.join(OUT_DIR, "lf01_universe_scale_complete.mp4")


def ts(t, srt=True):
    h, rem = divmod(t, 3600); m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".", ",") if srt else f"{int(m)}:{int(s):02d}"


def main():
    tl = json.load(open(os.path.join(WORK, "timeline.json")))
    dur = _probe_duration(SILENT)
    bed = os.path.join(WORK, "lf01_ambient.wav")
    generate_ambient_bed(dur, bed, preset="space", volume=0.10)
    mix = os.path.join(WORK, "lf01_mix.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, "lf01_voice_lead.wav"), "-i", bed,
                    "-filter_complex",
                    f"[0:a]apad,atrim=0:{dur:.3f}[v];[1:a]atrim=0:{dur:.3f},afade=t=out:st={dur-3:.3f}:d=3[b];"
                    f"[v][b]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[out]",
                    "-map", "[out]", "-ar", "48000", mix], check=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SILENT, "-i", mix, "-map", "0:v:0", "-map", "1:a:0",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT],
                   check=True)
    # CC subtitles for upload (sentence cues, wrapped to 2 lines)
    srt = os.path.join(OUT_DIR, "lf01_universe_scale.en.srt")
    with open(srt, "w") as f:
        for i, b in enumerate(tl["beats"], start=1):
            txt = "\n".join(textwrap.wrap(b["text"], 42))
            f.write(f"{i}\n{ts(b['start'])} --> {ts(b['end'] + 0.15)}\n{txt}\n\n")
    chapters = [(0.0 if i == 0 else b["start"], b["ch"]) for i, b in enumerate(x for x in tl["beats"] if x["ch"])]
    with open(os.path.join(OUT_DIR, "lf01_universe_scale_chapters.txt"), "w") as f:
        f.writelines(f"{ts(t, srt=False)} {name}\n" for t, name in chapters)
    print("✅", OUT, f"{_probe_duration(OUT):.1f}s"); print("✅", srt)
    print(open(os.path.join(OUT_DIR, "lf01_universe_scale_chapters.txt")).read())


if __name__ == "__main__":
    main()
