"""Download ep04 R2 shots with retries, concat, then voice + captions. No GPU."""
from __future__ import annotations

import os
import subprocess
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from audio_post import add_voice_and_captions, parse_captions_option
from test_prompts import test_jobs

VID = "ep04_midnight_platform"
BASE = (
    "https://pub-e52cde68d383466d9ebfbc1b7e8eea33.r2.dev"
    f"/renders/{VID}"
)
SHOTS = 7


def _session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=6,
        connect=6,
        read=6,
        backoff_factor=2,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://", HTTPAdapter(max_retries=retry))
    return s


def download_shot(sess: requests.Session, n: int, dest: str) -> None:
    url = f"{BASE}/shot_{n}.mp4"
    if os.path.isfile(dest) and os.path.getsize(dest) > 50_000:
        print(f"   ⏭️  shot_{n} already on disk ({os.path.getsize(dest)} bytes)")
        return

    print(f"   ⬇️  shot_{n} … {url}")
    last_err = None
    for attempt in range(1, 8):
        try:
            r = sess.get(url, stream=True, timeout=(15, 120))
            r.raise_for_status()
            tmp = dest + ".part"
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(chunk_size=256 * 1024):
                    if chunk:
                        f.write(chunk)
            os.replace(tmp, dest)
            print(f"   ✅ shot_{n} ({os.path.getsize(dest)} bytes)")
            return
        except Exception as e:
            last_err = e
            wait = min(30, 2 * attempt)
            print(f"   ⚠️  shot_{n} attempt {attempt}/7 failed: {e}")
            print(f"      retry in {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"Failed to download shot_{n}: {last_err}")


def main() -> None:
    job = next(j for j in test_jobs if j["video_id"] == VID)
    os.makedirs("./temp_clips", exist_ok=True)
    os.makedirs("./final_videos", exist_ok=True)

    sess = _session()
    local_paths = []
    print(f"⬇️ Downloading {SHOTS} R2 clips for {VID}…")
    for n in range(1, SHOTS + 1):
        path = f"./temp_clips/{VID}_shot_{n}.mp4"
        download_shot(sess, n, path)
        local_paths.append(os.path.abspath(path))

    list_file = f"./temp_clips/{VID}_list.txt"
    with open(list_file, "w") as f:
        for p in local_paths:
            f.write(f"file '{p}'\n")

    silent = f"./temp_clips/{VID}_silent.mp4"
    print("🎞️ Concatenating…")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            list_file,
            "-c",
            "copy",
            silent,
        ],
        check=True,
    )
    print(f"⬇️ Stitched silent video: {silent}")

    captions_on, caption_style = parse_captions_option(
        job.get("captions", False), job.get("caption_style")
    )
    output = f"./final_videos/{VID}_complete.mp4"
    add_voice_and_captions(
        silent,
        job["script"],
        output,
        work_dir=f"./temp_clips/{VID}_audio",
        voice=job.get("voice"),
        burn_captions=captions_on,
        caption_style=caption_style,
        ambient=job.get("ambient", "rain_city"),
        vo_delay_ms=int(job.get("vo_delay_ms", 900)),
        ambient_volume=float(job.get("ambient_volume", 0.38)),
    )
    print(f"🎉 Complete: {output}")


if __name__ == "__main__":
    main()
