"""
Download the free (public-domain / CC0) images a still-video episode needs from Wikimedia Commons.

Run on the laptop before still_video.py:
  VIDEO_ID=sci_ep17_sun_black_hole python fetch_still_assets.py

Files land in i2v_stills/<video_id>/ (git-ignored) with a SOURCES.md credit log. Anything whose
licence is not public domain or CC0 is refused, so nothing needing attribution slips in.
"""

import json
import os
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://commons.wikimedia.org/w/api.php"
UA = "niche-video-worker/1.0 (Threshold Physics still builder)"
OK_LICENCES = ("public domain", "pd", "cc0")

# {video_id: [(local filename, Commons search query), ...]} — first search hit is used.
ASSETS = {
    "sci_ep17_sun_black_hole": [
        ("sun.jpg", "Sun Atmospheric Imaging Assembly Solar Dynamics Observatory 20100819"),
        ("earth.jpg", "The Earth seen from Apollo 17"),
        ("city.jpg", "Chicago Illinois pictured at night from the International Space Station iss075e0099858"),
    ],
    "sci_ep22_sun_white": [
        ("sun_iss.jpg", "Sun over Earth's horizon International Space Station NASA"),
        ("astronaut.jpg", "Bruce McCandless II during EVA in 1984"),
        ("earth_limb.jpg", "Top of Atmosphere"),
    ],
    "sci_ep23_planets_moon_gap": [
        ("earth.jpg", "The Earth seen from Apollo 17"),
        ("moon.jpg", "Moon nearside LRO 5000"),
        ("mercury.jpg", "Mercury in color - Prockter07 centered"),
        ("venus.jpg", "Venus-real color"),
        ("mars.jpg", "Mars 23 aug 2003 hubble"),
        ("jupiter.jpg", "Jupiter by Cassini-Huygens"),
        ("saturn.jpg", "Saturn from Cassini Orbiter 2004-10-06"),
        ("uranus.jpg", "Uranus2"),
        ("neptune.jpg", "Neptune Full"),
    ],
    "sci_ep21_saturn_float": [
        ("saturn.jpg", "Saturn from Cassini Orbiter 2004-10-06"),
    ],
    "sci_ep20_jupiter_star": [
        ("jupiter.jpg", "Hubble Planetary Portrait Captures New Changes in Jupiter Great Red Spot 22214599072"),
    ],
}


def _get(params):
    url = API + "?" + urllib.parse.urlencode({**params, "format": "json"})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def find(query):
    """Return (title, download_url, licence) for the first image file matching query."""
    hits = _get({"action": "query", "list": "search", "srnamespace": 6, "srlimit": 5, "srsearch": query})
    for hit in hits["query"]["search"]:
        title = hit["title"]
        if not title.lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff")):
            continue
        info = _get({
            "action": "query", "titles": title, "prop": "imageinfo",
            "iiprop": "url|extmetadata", "iiurlwidth": 2400,
        })
        page = next(iter(info["query"]["pages"].values()))
        ii = page["imageinfo"][0]
        meta = ii.get("extmetadata", {})
        licence = meta.get("LicenseShortName", {}).get("value", "unknown")
        return title, ii.get("thumburl") or ii["url"], licence
    raise LookupError(f"no image found for: {query}")


def fetch(video_id):
    if video_id not in ASSETS:
        raise SystemExit(f"No asset list for {video_id}. Add it to ASSETS in fetch_still_assets.py")
    out_dir = os.path.join(HERE, "i2v_stills", video_id)
    os.makedirs(out_dir, exist_ok=True)
    log = [f"# {video_id} stills (Wikimedia Commons, public domain / CC0 only)", ""]
    for name, query in ASSETS[video_id]:
        title, url, licence = find(query)
        if not any(k in licence.lower() for k in OK_LICENCES):
            raise SystemExit(f"Refusing {title}: licence is '{licence}', not public domain/CC0")
        dst = os.path.join(out_dir, name)
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r, open(dst, "wb") as f:
            f.write(r.read())
        print(f"✅ {name} <- {title} ({licence})")
        log.append(f"- {name}: {title} — {licence}. https://commons.wikimedia.org/wiki/"
                   f"{urllib.parse.quote(title.replace(' ', '_'))}")
    with open(os.path.join(out_dir, "SOURCES.md"), "w") as f:
        f.write("\n".join(log) + "\n")
    print(f"Saved to {out_dir} — check each image looks right before building.")


if __name__ == "__main__":
    vid = os.getenv("VIDEO_ID") or (sys.argv[1] if len(sys.argv) > 1 else "")
    if not vid:
        raise SystemExit("Set VIDEO_ID=sci_epNN_slug")
    fetch(vid)
