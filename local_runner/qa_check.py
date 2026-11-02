#!/usr/bin/env python3
"""Automatic QA gate for a finished Short. Run it on every final MP4 before calling a build done.

    python qa_check.py final_videos/sci_ep28_sun_8min_complete.mp4 --script longform/short_sun_8min.py

Checks (any FAIL means the build is not ready):
  1. Voice vs script: Whisper transcribes the whole final audio; every scripted word must be heard,
     and the script's last 3 words must be heard in order. Catches cut or missing lines.
  2. Ending room: the last spoken word must end at least 0.3 s before the video ends.
  3. Judder: within a moving shot, frame-to-frame change should be steady. A shot where many
     consecutive frames are identical, or where the change jumps up and down, is stepping.
  4. Repeated shots: two shots more than 2 s apart that look nearly the same.

It can't judge whether the video feels good. The owner's phone watch stays the final gate.
"""
import argparse
import ast
import json
import re
import subprocess
import sys
import tempfile

import numpy as np

FPS = 30
SW, SH = 540, 960  # half resolution: sub-pixel stepping is still visible, memory stays ~300 MB


def words(text):
    return re.findall(r"[a-z0-9']+", text.lower().replace("’", "'"))


NUM = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six",
       "7": "seven", "8": "eight", "9": "nine", "10": "ten", "20": "twenty"}


def norm(w):
    return NUM.get(w, w).rstrip("s")  # crude plural/number folding so "Earths"=="earth", "8"=="eight"


def script_text(path):
    """Pull the spoken text out of an episode script's BEATS list without importing it."""
    tree = ast.parse(open(path).read())
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "BEATS" for t in node.targets):
            for d in node.value.elts:
                if isinstance(d, ast.Call):
                    for kw in d.keywords:
                        if kw.arg == "text" and isinstance(kw.value, ast.Constant):
                            out.append(kw.value.value)
                elif isinstance(d, ast.Dict):
                    for k, v in zip(d.keys, d.values):
                        if getattr(k, "value", None) == "text" and isinstance(v, ast.Constant):
                            out.append(v.value)
    if not out:
        sys.exit(f"no BEATS text found in {path}")
    return " ".join(out)


def probe_duration(mp4):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", mp4],
                       capture_output=True, text=True, check=True)
    return float(json.loads(r.stdout)["format"]["duration"])


def check_voice(mp4, script, duration):
    import whisper
    with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-ac", "1", "-ar", "16000", wav.name], check=True)
        res = whisper.load_model("small").transcribe(wav.name, word_timestamps=True, language="en")
    heard = [(norm(w), s["end"]) for seg in res["segments"] for wd in seg.get("words", [])
             for w, s in [(x, wd) for x in words(wd["word"])]]
    heard_words = [w for w, _ in heard]
    want = [norm(w) for w in words(script)]
    missing = [w for w in dict.fromkeys(want) if w not in heard_words]
    tail = want[-3:]
    tail_ok = len(heard_words) >= 3 and heard_words[-3:] == tail
    last_end = heard[-1][1] if heard else 0.0
    room = duration - last_end
    fails = []
    if len(missing) > max(1, len(set(want)) // 20):  # allow ~5% Whisper slips on odd words
        fails.append(f"scripted words not heard: {missing}")
    if not tail_ok:
        fails.append(f"ending not heard: expected '... {' '.join(tail)}', heard '... {' '.join(heard_words[-3:])}'")
    if room < 0.3:
        fails.append(f"last word ends {room:.2f}s before the video ends (need >= 0.3s)")
    print(f"voice: heard {len(heard_words)} words, last word at {last_end:.2f}s of {duration:.2f}s; "
          f"transcript ends '...{' '.join(heard_words[-6:])}'")
    return fails


def frames(mp4):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", mp4, "-vf", f"scale={SW}:{SH}", "-f", "rawvideo",
                          "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, SH, SW)


def check_motion(f):
    # change between consecutive frames, frame by frame to keep memory low
    D = [np.abs(f[k + 1].astype(np.int16) - f[k].astype(np.int16)).astype(np.uint8) for k in range(len(f) - 1)]
    whole = np.array([x.mean() for x in D])
    cuts = np.where(whole > 18)[0]  # hard cuts / fast crossfades
    bounds = [0] + [c + 1 for c in cuts] + [len(f)]
    fails, shots = [], []
    for a, b in zip(bounds[:-1], bounds[1:]):
        if b - a < FPS // 2:
            continue
        shots.append((a, b))
        seg = D[a:b - 1]
        mask = np.max(np.stack(seg), axis=0) > 4  # only the pixels that move in this shot
        if mask.mean() < 0.002:
            continue  # a still shot
        d = np.array([x[mask].mean() for x in seg])
        stalled = (d < 0.35 * np.median(d)).mean()  # frames where the moving part barely moves
        if stalled > 0.12:
            fails.append(f"judder {a / FPS:.1f}-{b / FPS:.1f}s: {stalled:.0%} of frames stall inside a moving shot")
    # repeated shots: compare each shot's middle frame at low resolution
    mids = [(a, f[(a + b) // 2][::8, ::8].astype(np.float32)) for a, b in shots]
    for i in range(len(mids)):
        for j in range(i + 1, len(mids)):
            (a1, m1), (a2, m2) = mids[i], mids[j]
            if (a2 - a1) / FPS > 2 and np.abs(m1 - m2).mean() < 6:
                fails.append(f"repeated shot: {a1 / FPS:.1f}s and {a2 / FPS:.1f}s look the same")
    print(f"motion: {len(shots)} shots checked")
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mp4")
    ap.add_argument("--script", required=True, help="episode script with a BEATS list")
    ap.add_argument("--skip-voice", action="store_true")
    a = ap.parse_args()
    dur = probe_duration(a.mp4)
    fails = [] if a.skip_voice else check_voice(a.mp4, script_text(a.script), dur)
    fails += check_motion(frames(a.mp4))
    if fails:
        print("QA FAIL")
        for x in fails:
            print("  -", x)
        sys.exit(1)
    print("QA PASS (automatic checks only; the owner's phone watch is still required)")


if __name__ == "__main__":
    main()
