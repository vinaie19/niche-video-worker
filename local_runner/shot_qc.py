#!/usr/bin/env python3
"""
Pre-stitch shot QC: catch the two failure modes that have cost real posts.

1. BRIGHTNESS CLIFFS. ep13 (53% AVD) dropped -64% at the 6s cut and -81% at 14s;
   its AVD landed at 17s, right after the second cliff. ep09 (107% AVD) declined
   smoothly — its first cut moved 87.5 -> 85.2. A hard luminance crash at a cut
   reads as "the good part is over". Both videos END equally dark, so it is the
   PATH that matters, not the destination.
2. FROZEN SHOTS. LTX renders restraint language ("drifting imperceptibly",
   "quiet and still") as a literal still image. ep13 shot 4 came back with 0.4%
   of pixels changed across the whole clip, twice.

Usage:  ./venv/bin/python shot_qc.py <video_id> [--max-drop 40] [--min-motion 3]
"""
import argparse, glob, os, subprocess, sys, tempfile

MAX_DROP_PCT = 45.0   # calibrated on real outcomes, not guessed: ep09 (107% AVD)
                      # survives one -43% cut; ep13 (53% AVD) had -54% and -65%.
MIN_MOTION_PCT = 3.0  # pixels changed first->last; below this the shot is frozen


def _luma(path):
    """Return (mean, head, tail) luminance.

    A cut is judged on the brightness the viewer actually sees ACROSS it — the
    TAIL of one shot against the HEAD of the next — not on shot means. Validation
    caught this: ep09 (107% AVD) has shot means of 78.7 -> 32.6 (-59%), which a
    mean-based check flags as a cliff, yet it is the best performer on the channel.
    Its shot 2 simply starts bright and ends dark, so its mean misrepresents both
    edges. Measured tail-to-head, ep09's real transition is far gentler.
    """
    out = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vf",
         "signalstats,metadata=print:key=lavfi.signalstats.YAVG", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    vals = [float(l.split("=")[-1]) for l in out.splitlines() if "YAVG=" in l]
    if not vals:
        return 0.0, 0.0, 0.0
    n = max(1, len(vals) // 8)          # first/last eighth of the clip
    return (sum(vals) / len(vals),
            sum(vals[:n]) / n,
            sum(vals[-n:]) / n)


def _motion(path):
    from PIL import Image, ImageChops
    d = tempfile.mkdtemp()
    dur = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
         "-of","csv=p=0",path], capture_output=True, text=True).stdout.strip() or 1)
    for i, t in enumerate((0.2, max(0.4, dur - 0.3))):
        subprocess.run(["ffmpeg","-v","error","-ss",str(t),"-i",path,"-frames:v","1",
                        "-vf","scale=200:-1", f"{d}/{i}.png","-y"], check=False)
    fs = sorted(glob.glob(f"{d}/*.png"))
    if len(fs) < 2:
        return 0.0
    a = Image.open(fs[0]).convert("L"); b = Image.open(fs[1]).convert("L")
    px = list(ImageChops.difference(a, b).get_flattened_data())
    return sum(1 for p in px if p > 12) / len(px) * 100


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--max-drop", type=float, default=MAX_DROP_PCT)
    ap.add_argument("--min-motion", type=float, default=MIN_MOTION_PCT)
    a = ap.parse_args()

    shots = sorted(glob.glob(f"./temp_clips/{a.video_id}_shot_[0-9].mp4"))
    if not shots:
        sys.exit(f"no shots found for {a.video_id}")

    print(f"\n{a.video_id} — {len(shots)} shots\n")
    print(f"{'shot':<6}{'brightness':>11}{'motion':>9}   verdict")
    rows = []
    for p in shots:
        mean, head, tail = _luma(p)
        m = _motion(p)
        rows.append((os.path.basename(p), mean, head, tail, m))
        flag = "FROZEN" if m < a.min_motion else "ok"
        print(f"{os.path.basename(p)[-6:-4]:<6}{mean:>11.1f}{m:>8.1f}%   {flag}"
              f"   (head {head:.0f} -> tail {tail:.0f})")

    print(f"\n{'cut':<10}{'tail':>8}{'head':>8}{'change':>10}   verdict")
    fails = 0
    for i in range(len(rows) - 1):
        b0, b1 = rows[i][3], rows[i + 1][2]     # tail of N vs head of N+1
        drop = (b0 - b1) / b0 * 100 if b0 else 0.0
        bad = drop > a.max_drop
        fails += bad
        print(f"{i+1}->{i+2:<7}{b0:>8.1f}{b1:>8.1f}{-drop:>9.0f}%   {'CLIFF' if bad else 'ok'}")
    frozen = sum(1 for r in rows if r[4] < a.min_motion)
    print()
    if fails or frozen:
        print(f"FAIL: {fails} brightness cliff(s), {frozen} frozen shot(s)")
        sys.exit(1)
    print("PASS: smooth luminance arc, all shots moving")


if __name__ == "__main__":
    main()
