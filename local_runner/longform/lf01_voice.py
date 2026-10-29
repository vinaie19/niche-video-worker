"""LF01 step 1: Edge-TTS voice-over per sentence -> timeline.json (sentence start/end times)."""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
from audio_post import generate_voiceover, _probe_duration  # noqa: E402
import lf01_script as sc  # noqa: E402

WORK = os.path.join(ROOT, "temp_clips", "lf01_universe_scale_audio")
STEM = "lf01_voice"
LEAD_S = 0.35  # silence before the first word
VOICE = "en-US-AndrewMultilingualNeural"


def main():
    os.makedirs(WORK, exist_ok=True)
    beats = [{"text": b["text"], "rate": b.get("rate", sc.VOICE_RATE), "pause_ms": b.get("pause_ms", 200)}
             for b in sc.BEATS]
    mp3 = os.path.join(WORK, f"{STEM}.mp3")
    # Long-form narrator: Andrew (Edge "warm, confident, authentic") reads more naturally over
    # 5 minutes than the punchier Shorts voice (Guy).
    generate_voiceover(script_beats=beats, output_mp3=mp3, voice=VOICE, pitch="+0Hz", work_dir=WORK)
    t, rows = LEAD_S, []
    for i, (b, raw) in enumerate(zip(beats, sc.BEATS), start=1):
        d = _probe_duration(os.path.join(WORK, f"{STEM}_beat{i}.wav"))
        rows.append({"i": i, "start": round(t, 3), "end": round(t + d, 3), "text": b["text"], "ch": raw.get("ch")})
        t += d + b["pause_ms"] / 1000.0
    total = t + 0.2
    with open(os.path.join(WORK, "timeline.json"), "w") as f:
        json.dump({"lead": LEAD_S, "total": round(total, 3), "beats": rows}, f, indent=1)
    # Voice track with the lead-in silence, for the final mix.
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-af", f"adelay={int(LEAD_S*1000)}:all=1",
                    os.path.join(WORK, f"{STEM}_lead.wav")], check=True)
    print(f"total {total:.1f}s, {len(rows)} sentences")


if __name__ == "__main__":
    main()
