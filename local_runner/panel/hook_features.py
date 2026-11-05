#!/usr/bin/env python3
"""Gate 2 data: measure the first 2 s of every published Short and compare with its real 'stayed to watch' %.

    venv/bin/python panel/hook_features.py            -> panel/hook_features.csv + correlations
"""
import csv
import os
import subprocess

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FV = os.path.join(os.path.dirname(HERE), "final_videos")
# title (as in ledger_14h.csv) -> published file (hook versions where those were the uploads)
FILES = {
    "Zoom Out From Earth to the Edge of the Universe": "sci_ep25_zoom_out_complete.mp4",
    "Jupiter Is a Star That Never Lit Up (80x Too Light)": "sci_ep20_jupiter_star_complete.mp4",
    "The Black Hole That Weighs 66 Billion Suns (TON 618)": "sci_ep19_ton618_complete.mp4",
    "The Exact Speed Needed to Escape the Sun (617.5 km/s)": "ready/sci_ep09_solar_escape_hook.mp4",
    "The Exact Size a Collapsed Star Crushes Down To (20 km)": "sci_ep08_neutron_star_complete.mp4",
    "The Fastest Anything Has Ever Spun (716 Hz)": "ready/sci_ep14_pulsar_716hz_hook.mp4",
    "The Exact Mass That Causes a White Dwarf Collapse (1.44 M☉)": "sci_ep07_chandrasekhar_complete.mp4",
    "Saturn Would Float in Water (Here's Why)": "sci_ep21_saturn_float_complete.mp4",
    "How Fast Is Earth Moving Through Space? (30 km/s)": "sci_ep18_earth_speed_complete.mp4",
    "The Exact Point Where Gravity Stretches Matter Into Spaghetti": "sci_ep05_spaghettification_complete.mp4",
    "The Exact Distance Where Gravity Shatters a Moon": "sci_ep02_roche_limit_complete.mp4",
    "The Exact Size Earth Must Shrink to Become a Black Hole (8.87 mm)": "ready/sci_ep13_earth_black_hole_hook.mp4",
    "The Mass Where a Neutron Star Becomes a Black Hole (About 2.5 Suns)": "sci_ep16_neutron_mass_limit_complete_v5.mp4",
    "The Exact Mass Limit No Star Can Pass (300 Suns)": "ready/sci_ep10_eddington_hook.mp4",
    "What If the Sun Turned Into a Black Hole? (6 km Wide)": "sci_ep17_sun_black_hole_still_complete.mp4",
    "Every Planet Fits Between Earth and the Moon": "sci_ep23_planets_moon_gap_complete.mp4",
    "Your Sunlight Is Older Than the Pyramids": "sci_ep28_sun_v2_nocaps.mp4",
    "The Star That Can Wipe Your Card From Space": "ready/sci_ep15_magnetar_hook.mp4",
    "Saturn's Rings Are Thinner Than a House": "sci_ep26_saturn_rings_complete.mp4",
    "Dropping an Object 1 Meter at 200 Million Gs": "sci_ep03_neutron_impact_complete.mp4",
    "The Exact Temperature Where Atomic Motion Stops (0 K)": "sci_ep04_absolute_zero_complete.mp4",
    "The Exact Point Where Sound Destroys Matter (194 dB)": "sci_ep01_sound_194db_complete.mp4",
}
W, H, FPS = 180, 320, 15


def frames(path, secs=3.0):
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-t", str(secs), "-i", path, "-vf",
                          f"fps={FPS},scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3).astype(np.float32)


def colorfulness(im):
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    rg, yb = r - g, 0.5 * (r + g) - b
    return float(np.hypot(rg.std(), yb.std()) + 0.3 * np.hypot(rg.mean(), yb.mean()))


def features(path):
    f = frames(path)
    g = f.mean(axis=3)
    n2 = 2 * FPS
    d = np.abs(np.diff(g[:n2 + 1], axis=0)).mean(axis=(1, 2))
    drift = [np.abs(g[k] - g[0]).mean() for k in range(min(len(g), 3 * FPS))]
    first_change = next((k / FPS for k, x in enumerate(drift) if x > 20), 3.0)
    cuts3 = int((np.abs(np.diff(g[:3 * FPS], axis=0)).mean(axis=(1, 2)) > 25).sum())
    f0 = f[0]
    top = g[0][: H // 3]
    edges = np.abs(np.diff(top, axis=1)).mean()  # sharp edges in the top third ~ on-screen text
    return dict(motion_2s=float(d.mean()), change_by_2s=float(np.abs(g[min(n2, len(g) - 1)] - g[0]).mean()),
                first_big_change_s=first_change, cuts_first_3s=cuts3, brightness_f0=float(g[0].mean()),
                dark_frac_f0=float((g[0] < 25).mean()), colorful_f0=colorfulness(f0), top_edge_f0=float(edges))


def main():
    rows = {r["title"]: r for r in csv.DictReader(open(os.path.join(HERE, "ledger_14h.csv")))}
    out = []
    for title, rel in FILES.items():
        p = os.path.join(FV, rel)
        if not os.path.exists(p):
            print("missing file:", rel); continue
        r = rows[title]
        out.append(dict(title=title, views=int(r["views_14h"]), stayed=float(r["stayed_pct"]), **features(p)))
    keys = list(out[0].keys())
    with open(os.path.join(HERE, "hook_features.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, keys); w.writeheader(); w.writerows(out)
    use = [o for o in out if o["views"] >= 50]  # tiny samples (2-27 views) make stayed% noise
    st = np.array([o["stayed"] for o in use])
    vw = np.log10([o["views"] for o in use])

    def rank(x):
        return np.argsort(np.argsort(x)).astype(float)

    print(f"\n{len(use)} Shorts with >= 50 views. Spearman correlation with stayed % and with log(views):")
    for k in keys[3:]:
        x = np.array([o[k] for o in use])
        rs = np.corrcoef(rank(x), rank(st))[0, 1]
        rv = np.corrcoef(rank(x), rank(vw))[0, 1]
        print(f"  {k:20s} stayed r={rs:+.2f}   views r={rv:+.2f}")
    print("\nper Short (sorted by stayed):")
    for o in sorted(out, key=lambda o: -o["stayed"]):
        print(f"  {o['stayed']:5.1f}% {o['views']:5d}v  motion {o['motion_2s']:5.1f}  change {o['change_by_2s']:5.1f}  "
              f"1st-change {o['first_big_change_s']:.1f}s  cuts {o['cuts_first_3s']}  bright {o['brightness_f0']:5.1f}  "
              f"dark {o['dark_frac_f0']:.2f}  color {o['colorful_f0']:5.1f}  text {o['top_edge_f0']:4.1f}  {o['title'][:45]}")


if __name__ == "__main__":
    main()
