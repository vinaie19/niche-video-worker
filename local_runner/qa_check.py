#!/usr/bin/env python3
"""Automatic QA gate for a finished Short. Run it on every final MP4 before calling a build done.

    python qa_check.py final_videos/sci_ep28_sun_8min_complete.mp4 --script longform/short_sun_8min.py

Checks (any FAIL means the build is not ready; one bad second is a FAIL):
  1. Voice vs script: Whisper transcribes the whole final audio; every scripted word must be heard,
     and the script's last 3 words must be heard in order. Catches cut or missing lines.
  2. Ending room: the last spoken word must end at least 0.3 s before the video ends.
  3. Judder: within a moving shot, frame-to-frame change should be steady. A shot where many
     consecutive frames are identical, or where the change jumps up and down, is stepping.
  4. Repeated shots: two shots more than 2 s apart that look nearly the same.
  5. Audio every 0.1 s: dropouts, clipping, loudness, audio shorter than video.
  6. Picture every frame: dark/empty screens, frozen video.
  7. Per-second verdicts: every second of the video is scored for dark screen, black bands
     (letterboxing), soft/blurry picture, brightness flashes, silence and stalls. One bad second = FAIL.
  8. Captions vs voice: every caption must appear within 0.35 s of its first spoken word and stay up
     until its last word is said.
Sheets: every frame of the first 2 s, every 0.25 s, every 0.1 s, and every frame around each transition.

It can't judge whether the video feels good. The owner's phone watch stays the final gate.
"""
import argparse
import ast
import json
import os
import re
import subprocess
import sys
import tempfile

import numpy as np

FPS = 30
WORDS = []   # (word, start, end) from Whisper, filled by check_voice
AUDIO_DB = None  # level of every 0.1 s of audio, filled by check_audio
TRANSITIONS = []  # times (s) of cuts and crossfades, filled by check_motion, for the transition sheets
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
                        # the written form (caption_text, e.g. "26,000") is what Whisper prints, so prefer it
                        kws = {k.arg: k.value for k in d.keywords if isinstance(k.value, ast.Constant)}
                        if kw.arg == "text" and "caption_text" not in kws and isinstance(kw.value, ast.Constant):
                            out.append(kw.value.value)
                        if kw.arg == "caption_text" and isinstance(kw.value, ast.Constant):
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
    global WORDS
    WORDS = [(norm(x), wd["start"], wd["end"]) for seg in res["segments"] for wd in seg.get("words", [])
             for x in words(wd["word"])]
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
    if missing:  # zero tolerance: re-listen by hand if Whisper mishears a rare word, never wave it through
        fails.append(f"scripted words not heard: {missing}")
    starts = [wd["start"] for seg in res["segments"] for wd in seg.get("words", [])]
    ends = [wd["end"] for seg in res["segments"] for wd in seg.get("words", [])]
    for e, st in zip(ends[:-1], starts[1:]):
        if st - e > 0.6:
            fails.append(f"voice gap {e:.1f}-{st:.1f}s ({st - e:.2f}s of silence mid-script)")
    if starts and starts[0] > 0.4:
        fails.append(f"voice starts late at {starts[0]:.2f}s (hook must be heard from frame 1)")
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
    global TRANSITIONS
    roll = np.array([np.median(whole[max(0, k - 15):k + 16]) for k in range(len(whole))])
    peaks = [k for k in range(len(whole)) if whole[k] > max(4.0, 2.2 * roll[k])]
    TRANSITIONS = []
    for k in peaks:  # one entry per transition, at its first frame
        if not TRANSITIONS or k / FPS - TRANSITIONS[-1] > 0.5:
            TRANSITIONS.append(k / FPS)
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
        # motion relative to the frame's own detail: a smooth, blurry image that moves correctly changes few
        # pixels, so raw differences made it look 'stalled' next to a sharp star field (ep29's EHT reveal)
        tex = np.array([np.abs(np.diff(f[k].astype(np.int16), axis=1))[:, :-0 or None].mean() + 1.0
                        for k in range(a, b - 1)])
        d = np.array([x[mask].mean() for x in seg]) / tex * tex.mean()
        # compare each frame with its neighbours (+-0.5 s), not one median for the whole span: crossfades
        # don't register as cuts, so a slow zoom next to busy footage used to read as "stalling"
        roll = np.array([np.median(d[max(0, k - FPS // 2):k + FPS // 2 + 1]) for k in range(len(d))])
        ref = np.maximum(roll, 0.3 * np.median(d))  # a long hold still fails: its neighbours are still too
        stalled = (d < 0.35 * ref).mean()  # frames where the moving part barely moves
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

def check_audio(mp4, duration):
    """Second-by-second audio scan: dropouts, clipping, loudness, audio shorter than video."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", mp4, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32)
    fails = []
    if len(a) / 16000 < duration - 0.1:
        fails.append(f"audio is {len(a) / 16000:.2f}s but video is {duration:.2f}s")
    win = 1600  # 0.1 s windows
    rms = np.array([np.sqrt(np.mean(a[i:i + win] ** 2) + 1e-12) for i in range(0, len(a) - win, win)])
    db = 20 * np.log10(rms)
    global AUDIO_DB
    AUDIO_DB = db
    dead = np.where(db < -50)[0]
    if len(dead):
        fails.append(f"near-silent audio at {', '.join(f'{k / 10:.1f}s' for k in dead[:10])}"
                     + (" ..." if len(dead) > 10 else ""))
    peak = 20 * np.log10(np.abs(a).max() + 1e-12)
    if peak > -0.3:
        fails.append(f"audio clips (peak {peak:.1f} dBFS)")
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", mp4, "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.findall(r"I:\s+(-?[0-9.]+) LUFS", r.stderr)
    if m and not -16.5 <= float(m[-1]) <= -12.5:
        fails.append(f"loudness {m[-1]} LUFS (want -14 +/- 2)")
    print(f"audio: {len(a) / 16000:.2f}s, peak {peak:.1f} dBFS, loudness {m[-1] if m else '?'} LUFS")
    return fails


def check_picture(f):
    """Every frame: mostly-dark/empty screens and frozen video."""
    fails = []
    dark = [k for k in range(len(f)) if (f[k] < 22).mean() > 0.45]  # >45% of the screen near-black
    if dark:
        secs = sorted({round(k / FPS, 1) for k in dark})
        fails.append(f"mostly dark/empty screen at {len(secs)} moments, e.g. {secs[:8]}s (rule: full-frame imagery)")
    same = 0
    for k in range(1, len(f)):
        same = same + 1 if np.array_equal(f[k], f[k - 1]) else 0
        if same == 6:  # 0.2 s of identical frames
            fails.append(f"frozen video around {k / FPS:.1f}s")
    return fails


def check_seconds(f):
    """Score every second on its own. Any flagged second fails the build."""
    n = len(f)
    lum = np.array([x.mean() for x in f])
    sharp = []
    for x in f:
        y = x[::2, ::2].astype(np.float32)
        lap = 4 * y[1:-1, 1:-1] - y[:-2, 1:-1] - y[2:, 1:-1] - y[1:-1, :-2] - y[1:-1, 2:]
        sharp.append(lap.var())
    sharp = np.array(sharp)

    def band(x):  # near-black rows touching the top/bottom edge: letterboxing
        rows = x.mean(axis=1) < 14
        top = np.argmin(rows) if not rows.all() else len(rows)
        bot = np.argmin(rows[::-1]) if not rows.all() else len(rows)
        return (top + bot) / len(rows)

    bands = np.array([band(x) for x in f])
    dark = np.array([(x < 22).mean() for x in f])
    same = np.array([0] + [int(np.array_equal(f[k], f[k - 1])) for k in range(1, n)])
    jump = np.abs(np.diff(lum, prepend=lum[0]))
    lit = sharp[dark < 0.45]
    ref = np.median(lit) if len(lit) else np.median(sharp)
    fails, rows = [], []
    for sec in range(int(np.ceil(n / FPS))):
        a, b = sec * FPS, min(n, (sec + 1) * FPS)
        why = []
        if (dark[a:b] > 0.45).mean() > 0.3:
            why.append(f"dark {np.mean(dark[a:b]):.0%}")
        if np.median(bands[a:b]) > 0.10:
            why.append(f"black bands {np.median(bands[a:b]):.0%} of height")
        if np.median(sharp[a:b]) < 0.3 * ref and np.median(dark[a:b]) < 0.45:
            why.append(f"soft picture ({np.median(sharp[a:b]) / ref:.0%} of the video's sharpness)")
        if jump[a:b].max() > 40:
            why.append(f"brightness flash ({jump[a:b].max():.0f} levels in one frame)")
        if same[a:b].sum() >= 3:
            why.append(f"{same[a:b].sum()} repeated frames")
        if AUDIO_DB is not None:
            w = AUDIO_DB[sec * 10:(sec + 1) * 10]
            if len(w) and (w < -50).any():
                why.append(f"near-silent audio ({(w < -50).sum()} x 0.1 s)")
        rows.append(f"  {sec:2d}s  {'FLAG  ' + '; '.join(why) if why else 'ok'}")
        if why:
            fails.append(f"second {sec}: " + "; ".join(why))
    print("per-second verdicts:")
    print("\n".join(rows))
    return fails


def script_vid(path):
    for node in ast.walk(ast.parse(open(path).read())):
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "VID" for t in node.targets):
            return node.value.value
    return None


def check_captions(script_path):
    """Each caption must appear within 0.35 s of its first spoken word and stay until its last word ends."""
    vid = script_vid(script_path)
    root = os.path.dirname(os.path.dirname(os.path.abspath(script_path)))
    srt = os.path.join(root, "temp_clips", f"{vid}_audio", f"{vid}_captions.srt")
    if not vid or not os.path.exists(srt):
        return [f"caption file not found ({srt}): caption timing could not be verified"]
    if not WORDS:
        return ["no Whisper words (voice check skipped?): caption timing could not be verified"]

    def ts(x):
        h, m, r = x.strip().split(":"); sec, ms = r.split(",")
        return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000

    fails, k = [], 0
    for block in open(srt).read().strip().split("\n\n"):
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        a, b = (ts(x) for x in lines[1].split("-->"))
        ws = [norm(w) for w in words(" ".join(lines[2:]))]
        if not ws:
            continue
        hit = next((j for j in range(k, min(k + 10, len(WORDS))) if WORDS[j][0] == ws[0]), None)
        if hit is None:
            fails.append(f"caption '{' '.join(lines[2:])}' ({a:.2f}s): its first word wasn't found in the voice")
            continue
        last = next((j for j in range(hit + len(ws) - 1, min(hit + len(ws) + 4, len(WORDS)))
                     if WORDS[j][0] == ws[-1]), hit + len(ws) - 1)
        k = last + 1
        if a - WORDS[hit][1] > 0.35:
            fails.append(f"caption '{' '.join(lines[2:])}' appears {a - WORDS[hit][1]:.2f}s after the word is spoken")
        if WORDS[hit][1] - a > 0.5:
            fails.append(f"caption '{' '.join(lines[2:])}' appears {WORDS[hit][1] - a:.2f}s before the word is spoken")
        if last < len(WORDS) and b < WORDS[last][2] - 0.15:
            fails.append(f"caption '{' '.join(lines[2:])}' leaves {WORDS[last][2] - b:.2f}s before its last word ends")
    print(f"captions: checked against {len(WORDS)} spoken words")
    return fails


def contact_sheets(mp4, outdir, duration):
    """Dense frame sheets for the visual review: every frame of the first 2 s, then every 0.25 s."""
    os.makedirs(outdir, exist_ok=True)
    for old in os.listdir(outdir):
        os.remove(os.path.join(outdir, old))
    jobs = [("first2s", "trim=0:2,fps=30", 6, 216), ("every_0.25s", "fps=4", 8, 216),
            ("every_0.1s", "fps=10", 10, 162)]
    for t in TRANSITIONS:  # every frame from 0.3 s before to 0.3 s after each cut or crossfade
        jobs.append((f"transition_{t:05.2f}s", f"trim=start={max(0, t - 0.3):.3f}:end={t + 0.3:.3f},setpts=PTS-STARTPTS,fps=30", 9, 162))
    for name, flt, cols, w in jobs:
        out = os.path.join(outdir, f"{name}_%02d.png")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-vf",
                        f"{flt},scale={w}:{w * 16 // 9},drawtext=text='%{{pts\\:hms}}':x=4:y=4:fontsize=14:"
                        f"fontcolor=yellow:box=1:boxcolor=black@0.6,tile={cols}x2", out], check=True)
    sheets = sorted(os.listdir(outdir))
    print(f"sheets: {len(sheets)} images in {outdir}")
    return sheets


REVIEW_QUESTIONS = """
Answer every question from the sheets (and the script) before sending the video. Any 'no' = fix and rebuild.
 1. Frame 1: does the surprising claim show on screen, with the subject filling the screen?
 2. Within 1 s, would a stranger know what they're looking at?
 3. For every 0.25 s frame: is the screen full and bright (no big black areas, no tiny object on black)?
 4. Does each picture show exactly what the voice says at that moment?
 5. Is any shot used twice, or two shots so alike they read as a repeat?
 6. Is all text fully on screen, readable, and clear of captions and the bottom 20% (Shorts UI)?
 7. Do captions match the spoken words, and change in time with them?
 8. Is something visibly moving in every second (no static holds)?
 9. Does the last frame match the first so the loop is seamless?
10. Is the final line the payoff, said in full, with the last word clearly heard?
11. Is every number and claim correct (checked against a source, not memory)?
12. Would I stop scrolling for frame 1 and stay to the end? If unsure, the answer is no.
13. Transition sheets: is every cut/crossfade clean (no flash, no black frame, no half-drawn text)?
14. 0.1 s sheets: does any single moment look wrong (glitch, jump, text overlapping text, wrong crop)?
15. Is every picture sharp on a phone, or does any shot look upscaled/soft?
16. Does the on-screen label ever contradict or lag the voice?
17. Is the footage real and correctly described (no AI-looking details, credits right in the description)?
18. Is there one clear idea, with a turn, and nothing a viewer would call filler?
19. Is the audio balanced: voice clearly on top, no music/effects drowning a word, no harsh whoosh?
20. Compared with the best Shorts on this topic, is this one clearly better? If not, why post it?
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mp4")
    ap.add_argument("--script", required=True, help="episode script with a BEATS list")
    ap.add_argument("--skip-voice", action="store_true")
    ap.add_argument("--sheets", help="folder for the contact sheets (default: <video>_qa/)")
    ap.add_argument("--accept", action="append", default=[], metavar="FROM-TO:CHECK:REASON",
                    help="documented exception for a per-second check, e.g. '17-19:soft:the EHT image is the "
                         "real data at its native resolution'. Printed in every report; never silent.")
    a = ap.parse_args()
    dur = probe_duration(a.mp4)
    fails = [] if a.skip_voice else check_voice(a.mp4, script_text(a.script), dur)
    fails += check_audio(a.mp4, dur)
    fr = frames(a.mp4)
    fails += check_picture(fr)
    fails += check_motion(fr)
    accepted = []
    for spec in a.accept:
        rng, chk, why = spec.split(":", 2)
        lo, hi = (int(x) for x in rng.split("-"))
        accepted.append((lo, hi, chk, why))
    sec_fails = check_seconds(fr)
    for f in sec_fails:
        sec = int(f.split()[1].rstrip(":"))
        reasons = f.split(": ", 1)[1].split("; ")
        left = [r for r in reasons
                if not any(lo <= sec <= hi and r.startswith(chk) for lo, hi, chk, _ in accepted)]
        if left:
            fails.append(f"second {sec}: " + "; ".join(left))
    for lo, hi, chk, why in accepted:
        print(f"ACCEPTED EXCEPTION seconds {lo}-{hi} '{chk}': {why}")
    if not a.skip_voice:
        fails += check_captions(a.script)
    contact_sheets(a.mp4, a.sheets or os.path.splitext(a.mp4)[0] + "_qa", dur)
    print(REVIEW_QUESTIONS)
    if fails:
        print("QA FAIL")
        for x in fails:
            print("  -", x)
        sys.exit(1)
    print("QA PASS on the automatic checks. Now answer the review questions above from the sheets,\n"
          "then the owner's phone watch is still required.")


if __name__ == "__main__":
    main()
