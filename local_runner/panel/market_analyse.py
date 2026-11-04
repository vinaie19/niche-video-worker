#!/usr/bin/env python3
"""Analyse panel/market_shorts.csv: which topics and title patterns break out (views vs own channel median)."""
import csv
import os
import re
import statistics as S

HERE = os.path.dirname(os.path.abspath(__file__))
TOPICS = {
    "extreme objects": r"neutron|pulsar|magnetar|black hole|quasar|white dwarf|supernova|kilonova|hypernova",
    "giant stars": r"biggest star|largest star|uy scuti|stephenson|betelgeuse|red giant|hypergiant|r136",
    "scale / size": r"size|scale|compar|zoom|how big|how small|bigger than|smaller than|fit inside|vs\b",
    "solar system": r"\bsun\b|moon|earth|mars|jupiter|saturn|venus|mercury|uranus|neptune|pluto|asteroid|comet",
    "galaxy / universe": r"galax|universe|big bang|dark matter|dark energy|cosmic|observable",
    "astronauts / NASA": r"astronaut|\biss\b|space station|nasa|spacex|rocket|apollo",
    "alien / mystery": r"alien|mysterious|mystery|unexplained|signal|wow signal|ufo",
    "what if / danger": r"what if|what would happen|deadliest|scariest|dangerous|kill|destroy|die\b",
}
FORMATS = {
    "journey / zoom / flight": r"zoom|flight|fly |flying|journey|travel to|to the edge|from earth to",
    "size comparison": r"size comparison|compared to|scale|how big|how small|bigger than|vs\b",
    "visualized / simulation / 3D": r"visuali[sz]|simulation|3d|animation|model",
    "real footage / caught on camera": r"footage|caught on camera|real |captured|camera|filmed|nasa video|view from",
    "news / event": r"launch|starship|artemis|eclipse 202|flight \d|just |new |discovered|found",
    "explainer (why/how/what is)": r"^why|^how |^what is|explained|^what are",
}
PATTERNS = {
    "has a number": r"\d",
    "question (?)": r"\?",
    "what if / would": r"what if|would happen|what would",
    "superlative": r"biggest|largest|fastest|smallest|heaviest|hottest|coldest|scariest|deadliest|most |strongest|oldest",
    "talks to 'you'": r"\byou\b|\byour\b",
    "comparison": r"\bvs\b|compared|than |versus",
    "emoji": r"[\U0001F300-\U0001FAFF☀-➿]",
    "hashtags in title": r"#\w",
    "ALL-CAPS word": r"\b[A-Z]{4,}\b",
}


def main():
    rows = [r for r in csv.DictReader(open(os.path.join(HERE, "market_shorts.csv")))]
    for r in rows:
        r["views"] = int(r["views"]); r["outlier"] = float(r["outlier"]); r["med"] = int(r["channel_median"])
    off = ("bajaj", "techtravel", "aumsum")  # off-topic channels the search pulled in (a motorbike called Pulsar...)
    space = [r for r in rows if r["space"] == "1" and r["med"] >= 500
             and not any(o in r["channel"].lower() for o in off)]  # tiny channels: medians are noise
    chans = {r["channel_id"] for r in space}
    print(f"{len(rows)} Shorts from {len({r['channel_id'] for r in rows})} channels; {len(space)} space Shorts from "
          f"{len(chans)} channels (median >= 500 views) analysed")
    top_cut = sorted(r["outlier"] for r in space)[int(len(space) * 0.9)]
    print(f"breakout = top 10% = >= {top_cut:.1f}x the channel's median\n")

    def block(name, table):
        print(f"{name:22s} {'Shorts':>6s} {'median x':>8s} {'breakout rate':>13s}")
        base = sum(r["outlier"] >= top_cut for r in space) / len(space)
        out = []
        for k, rx in table.items():
            sel = [r for r in space if re.search(rx, r["title"], re.I if k != "ALL-CAPS word" else 0)]
            if len(sel) < 15:
                continue
            br = sum(r["outlier"] >= top_cut for r in sel) / len(sel)
            out.append((br, k, len(sel), S.median(r["outlier"] for r in sel)))
        for br, k, n, m in sorted(out, reverse=True):
            print(f"  {k:20s} {n:6d} {m:8.2f} {br:12.0%}  ({br / base:.1f}x the average)")
        print()

    block("TOPIC", TOPICS)
    block("TITLE PATTERN", PATTERNS)
    block("FORMAT (from title)", FORMATS)
    durs = None
    print("TOP 40 BREAKOUT SPACE SHORTS (views vs that channel's median):")
    for r in sorted(space, key=lambda r: -r["outlier"])[:40]:
        print(f"  {r['outlier']:6.1f}x  {r['views']:>11,}  {r['title'][:80]}  [{r['channel'][:22]}]")


if __name__ == "__main__":
    main()
