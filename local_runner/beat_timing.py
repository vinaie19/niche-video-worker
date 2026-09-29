"""
Beat timing & frame calculation: measure VO duration for each beat and calculate
frame counts to match, respecting LTX-2.5 constraints (8n+1 frames).

Usage:
  from beat_timing import calculate_beat_frames, dry_run_beat_timing

  frames_per_beat = calculate_beat_frames(
      script_beats=beats,
      fps=24,
      voice="christopher",
      safety_margin_ms=200,
  )
  # Returns [121, 169, 145, ...] for each beat

  # Or dry-run to print durations without affecting jobs:
  dry_run_beat_timing(episode_name, beats, fps=24)
"""

import os
import re
import asyncio
import tempfile
import subprocess
from typing import Optional, Any


def _valid_ltx_frames(max_frames=961):
    """LTX-2.5 frame counts: 8k+1 for k >= 2."""
    return {8 * k + 1 for k in range(2, (max_frames - 1) // 8 + 1)}


VALID_FRAMES = _valid_ltx_frames()


def nearest_valid_frames(n: int) -> int:
    """Round n to nearest valid LTX frame count."""
    n = max(17, int(n))
    if n in VALID_FRAMES:
        return n
    return min(VALID_FRAMES, key=lambda v: abs(v - n))


def _collapse_whitespace(text: str) -> str:
    """Strip line breaks and collapse whitespace for TTS."""
    return re.sub(r'\s+', ' ', text).strip()


async def _tts_beat_duration(
    beat_text: str,
    voice_id: str,
    rate: str = "+0%",
    pitch: str = "+0Hz",
) -> float:
    """Synthesize one beat via Edge-TTS (without file I/O) and return duration in seconds."""
    try:
        import edge_tts
    except ImportError:
        raise ImportError("edge-tts required; install with: pip install edge-tts")

    clean_text = _collapse_whitespace(beat_text)
    if not clean_text:
        return 0.0

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        temp_mp3 = f.name

    try:
        communicate = edge_tts.Communicate(clean_text, voice_id, rate=rate, pitch=pitch)
        await communicate.save(temp_mp3)

        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1:nokey=1",
                temp_mp3,
            ],
            capture_output=True,
            text=True,
        )
        try:
            return float(result.stdout.strip())
        except (ValueError, AttributeError):
            return 0.0
    finally:
        if os.path.exists(temp_mp3):
            os.unlink(temp_mp3)


def _resolve_voice(voice: Optional[str]) -> str:
    """Resolve voice preset key or full Edge-TTS ID."""
    from audio_post import resolve_voice
    return resolve_voice(voice)


def calculate_beat_frames(
    script_beats: list[dict[str, Any]],
    fps: int = 24,
    voice: Optional[str] = None,
    rate: Optional[str] = None,
    pitch: Optional[str] = None,
    safety_margin_ms: int = 200,
    dry_run: bool = False,
) -> list[int]:
    """
    Measure TTS duration for each beat and calculate frame counts.

    Args:
        script_beats: list of {text, rate?, pitch?, pause_ms?, ...}
        fps: frames per second (default 24)
        voice: voice preset or full ID
        rate: default rate (e.g., "+0%")
        pitch: default pitch (e.g., "+0Hz")
        safety_margin_ms: extra ms to add to VO duration (default 200)
        dry_run: if True, don't modify beats; just calculate

    Returns:
        List of frame counts (8n+1 form) for each beat, one per beat.
    """
    from audio_post import resolve_voice, _normalize_rate, _normalize_pitch

    if not script_beats:
        return []

    voice_id = resolve_voice(voice)
    rate_default = _normalize_rate(rate)
    pitch_default = _normalize_pitch(pitch)

    durations = asyncio.run(
        _measure_all_beats(
            script_beats,
            voice_id,
            rate_default,
            pitch_default,
        )
    )

    frame_counts = []
    for dur_s, pause_ms, beat_dict in zip(durations,
                                          [b.get("pause_ms", 0) for b in script_beats],
                                          script_beats):
        total_ms = int(dur_s * 1000) + int(pause_ms or 0) + safety_margin_ms
        total_s = total_ms / 1000.0
        requested_frames = int(total_s * fps)
        final_frames = nearest_valid_frames(requested_frames)
        frame_counts.append(final_frames)

        if not dry_run and "num_frames" not in beat_dict:
            beat_dict["num_frames"] = final_frames

    return frame_counts


async def _measure_all_beats(
    script_beats: list[dict[str, Any]],
    voice_id: str,
    rate_default: str,
    pitch_default: str,
) -> list[float]:
    """Measure TTS duration for each beat concurrently."""
    tasks = []
    for beat in script_beats:
        text = (beat.get("text") or "").strip()
        if not text:
            tasks.append(asyncio.sleep(0))
            continue

        rate = beat.get("rate", rate_default)
        pitch = beat.get("pitch", pitch_default)
        task = _tts_beat_duration(text, voice_id, rate, pitch)
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    return [r if isinstance(r, float) else 0.0 for r in results]


def dry_run_beat_timing(
    episode_name: str,
    script_beats: list[dict[str, Any]],
    fps: int = 24,
    voice: Optional[str] = None,
    rate: Optional[str] = None,
    pitch: Optional[str] = None,
    safety_margin_ms: int = 200,
) -> None:
    """
    Dry-run: measure all beats and print timing info without modifying.

    Prints:
      - Per-beat VO duration (after silence trim)
      - Per-beat pause
      - Per-beat total (VO + pause + margin)
      - Chosen frame count (8n+1)
    """
    from audio_post import resolve_voice, _normalize_rate, _normalize_pitch

    if not script_beats:
        print(f"⏱️  {episode_name}: no beats to measure")
        return

    voice_id = resolve_voice(voice)
    rate_default = _normalize_rate(rate)
    pitch_default = _normalize_pitch(pitch)

    print(f"\n⏱️  Beat timing dry-run: {episode_name} ({len(script_beats)} beats @{fps}fps)")
    print("=" * 80)

    durations = asyncio.run(
        _measure_all_beats(
            script_beats,
            voice_id,
            rate_default,
            pitch_default,
        )
    )

    total_ms_all = 0
    for i, (beat, dur_s) in enumerate(zip(script_beats, durations), start=1):
        text_preview = (beat.get("text") or "")[:48].replace("\n", " ")
        pause_ms = int(beat.get("pause_ms", 0) or 0)
        total_ms = int(dur_s * 1000) + pause_ms + safety_margin_ms
        total_s = total_ms / 1000.0
        requested_frames = int(total_s * fps)
        final_frames = nearest_valid_frames(requested_frames)
        final_s = final_frames / fps

        total_ms_all += total_ms

        print(
            f"  Beat {i:2d} | VO: {dur_s:6.2f}s | pause: {pause_ms:3d}ms | "
            f"total: {total_s:6.3f}s | frames: {final_frames:3d} "
            f"({final_s:.2f}s @{fps}fps) | {text_preview}…"
        )

    print("=" * 80)
    print(f"📊 Total duration (all beats + pauses + margin): {total_ms_all/1000.0:.2f}s")
    print()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python beat_timing.py <episode_name> [fps]")
        sys.exit(1)

    ep_name = sys.argv[1]
    fps_arg = int(sys.argv[2]) if len(sys.argv) > 2 else 24

    from science_prompts import build_science_jobs
    jobs = build_science_jobs(num_frames=129, steps=8)

    for job in jobs:
        if job.get("video_id") == ep_name:
            beats = job.get("script_beats") or []
            dry_run_beat_timing(
                ep_name,
                beats,
                fps=fps_arg,
                voice=job.get("voice"),
                rate=job.get("voice_rate"),
                pitch=job.get("voice_pitch"),
            )
            sys.exit(0)

    print(f"❌ Episode '{ep_name}' not found")
    sys.exit(1)
