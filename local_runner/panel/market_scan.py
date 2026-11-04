#!/usr/bin/env python3
"""Market study: which space/physics Short ideas break out on other channels.

1. Find space/physics channels through YouTube search (many topic queries).
2. Pull each channel's Shorts tab (title + views) and its subscriber count.
3. Score every Short against its own channel: outlier = views / channel's median Short views.
   This controls for channel size, so a high score means the idea worked, not the audience.

    venv/bin/python panel/market_scan.py      -> panel/market_shorts.csv
"""
import csv
import os
import random
import statistics
import sys
import time

import yt_dlp

HERE = os.path.dirname(os.path.abspath(__file__))
QUERIES = [
    "neutron star", "black hole", "magnetar", "pulsar", "white dwarf", "biggest star in the universe",
    "largest black hole", "space facts shorts", "universe scale comparison", "zoom out universe", "jupiter facts",
    "saturn rings facts", "sun facts", "moon facts", "mars facts", "earth from space facts", "speed of light explained",
    "spaghettification", "what if the sun disappeared", "solar system to scale", "scariest thing in space",
    "space size comparison", "physics facts shorts", "quasar", "supernova", "galaxy collision", "space mysteries shorts",
    "astronomy facts shorts", "dark matter explained", "how big is the universe", "planets size comparison",
    "extreme physics facts", "space shorts", "cosmos facts shorts",
]
SPACE = ("star", "sun", "black hole", "galax", "planet", "jupiter", "saturn", "mars", "moon", "earth", "universe",
         "space", "neutron", "pulsar", "magnetar", "nebula", "quasar", "supernova", "cosmic", "orbit", "light year",
         "light-year", "asteroid", "comet", "venus", "mercury", "uranus", "neptune", "pluto", "solar", "astronaut",
         "nasa", "gravity", "dwarf", "telescope", "webb", "hubble", "alien", "spacetime", "wormhole", "big bang")
MAX_CHANNELS = int(os.environ.get("MAX_CHANNELS", "90"))
SHORTS_PER_CHANNEL = int(os.environ.get("SHORTS_PER_CHANNEL", "80"))


def main():
    flat = yt_dlp.YoutubeDL({"quiet": True, "extract_flat": True, "skip_download": True, "ignoreerrors": True,
                             "no_warnings": True})
    chans = {}
    for q in QUERIES:
        for query in (f"ytsearch25:{q}", f"ytsearch25:{q} #shorts"):
            try:
                res = flat.extract_info(query, download=False) or {}
            except Exception:  # noqa: BLE001
                continue
            for e in res.get("entries") or []:
                if e and e.get("channel_id"):
                    chans.setdefault(e["channel_id"], [e.get("channel"), 0])[1] += 1
            time.sleep(0.8)
    ranked = sorted(chans.items(), key=lambda kv: -kv[1][1])[:MAX_CHANNELS]
    print(f"{len(chans)} channels found; scanning the {len(ranked)} most frequent", file=sys.stderr)
    tab = yt_dlp.YoutubeDL({"quiet": True, "extract_flat": True, "skip_download": True, "ignoreerrors": True,
                            "no_warnings": True, "playlistend": SHORTS_PER_CHANNEL})
    out = os.path.join(HERE, "market_shorts.csv")
    keys = ["channel", "channel_id", "subs", "n_shorts", "channel_median", "title", "id", "views", "outlier", "space"]
    rows = 0
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, keys); w.writeheader()
        for k, (cid, (name, hits)) in enumerate(ranked):
            try:
                s = tab.extract_info(f"https://www.youtube.com/channel/{cid}/shorts", download=False)
            except Exception:  # noqa: BLE001
                s = None
            ents = [e for e in ((s or {}).get("entries") or []) if e and e.get("view_count")]
            if len(ents) >= 8:
                med = statistics.median(e["view_count"] for e in ents)
                for e in ents:
                    t = e.get("title") or ""
                    w.writerow(dict(channel=name, channel_id=cid, subs=(s or {}).get("channel_follower_count") or "",
                                    n_shorts=len(ents), channel_median=int(med), title=t, id=e.get("id"),
                                    views=e["view_count"], outlier=round(e["view_count"] / max(1, med), 2),
                                    space=int(any(x in t.lower() for x in SPACE))))
                    rows += 1
                fh.flush()
            if k % 10 == 0:
                print(f"  {k}/{len(ranked)} channels, {rows} Shorts", file=sys.stderr)
            time.sleep(0.8 + random.random())
    print(f"wrote {rows} Shorts to {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
