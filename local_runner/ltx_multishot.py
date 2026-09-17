"""
LTX-2.5 native multishot: one T2V pass, continuous AV bed.

join_style:
  cut      — hard visual cuts; ambient/score continues across cuts (Threshold Physics default)
  continue — one seamless take; no hard cuts (linger / camera evolve)

Official guidance: write chronological prose (not a numbered shot list);
name transitions; state audio continuity at every cut.
"""

from __future__ import annotations

from typing import Any, Iterable, List, Optional, Sequence, Union

JOIN_STYLES = ("cut", "continue")
MULTISHOT_MODES = (
    "ltx_multishot",
    "continuous",
    "cut",
    "continue",
    "single_shot",
    "singleshot",
)

_AUDIO_BIBLE = (
    "a continuous deep-space ambient drone with soft low-frequency hum and "
    "subtle cosmic shimmer, no melody, no vocals, no dialogue"
)


def normalize_join_style(raw: Optional[str], shot_mode: Optional[str] = None) -> str:
    """Resolve join_style from explicit field or shot_mode alias."""
    style = (raw or "").strip().lower()
    if style in JOIN_STYLES:
        return style
    mode = (shot_mode or "").strip().lower()
    if mode in ("continue", "continuous", "single_shot", "singleshot"):
        return "continue"
    if mode in ("cut", "ltx_multishot"):
        return "cut"
    return "cut"


def is_multishot_mode(shot_mode: Optional[str]) -> bool:
    return (shot_mode or "").strip().lower() in MULTISHOT_MODES


def _shot_entries(shots: Sequence[Any]) -> List[dict]:
    """Normalize shots to {prompt, num_frames?}."""
    out: List[dict] = []
    for shot in shots:
        if isinstance(shot, dict):
            text = (shot.get("prompt") or shot.get("shot") or "").strip()
            if not text:
                continue
            entry = {"prompt": text}
            if shot.get("num_frames") is not None:
                entry["num_frames"] = int(shot["num_frames"])
            out.append(entry)
        else:
            text = str(shot).strip()
            if text:
                out.append({"prompt": text})
    return out


def _shot_texts(shots: Sequence[Any]) -> List[str]:
    return [e["prompt"] for e in _shot_entries(shots)]


def sum_shot_frames(
    shots: Sequence[Any],
    default_frames: Optional[int] = None,
) -> int:
    """Sum per-shot num_frames (fallback default_frames or 97)."""
    total = 0
    for entry in _shot_entries(shots):
        if entry.get("num_frames") is not None:
            total += int(entry["num_frames"])
        elif default_frames is not None:
            total += int(default_frames)
        else:
            total += 97
    return max(17, total)


def build_multishot_prompt(
    shots: Sequence[Any],
    join_style: str = "cut",
    audio_bed: str = _AUDIO_BIBLE,
    fps: float = 24.0,
) -> str:
    """
    Collapse N shot prompts into one LTX-2.5 chronological multishot paragraph.
    Includes approximate per-shot durations so cuts land closer to VO beats.
    """
    entries = _shot_entries(shots)
    if not entries:
        raise ValueError("build_multishot_prompt requires at least one shot")

    style = normalize_join_style(join_style)
    bed = (audio_bed or _AUDIO_BIBLE).strip()
    fps = float(fps) if fps and fps > 0 else 24.0

    def _with_dur(prompt: str, num_frames: Optional[int]) -> str:
        body = prompt.rstrip(". ")
        if num_frames:
            secs = max(1.0, int(num_frames) / fps)
            return f"{body}. Hold this framing for about {secs:.1f} seconds"
        return body

    if len(entries) == 1:
        e = entries[0]
        return (
            f"{_with_dur(e['prompt'], e.get('num_frames'))}. "
            f"Continuous audio throughout: {bed}."
        )

    if style == "continue":
        first = entries[0]
        chunks = [
            f"One continuous locked vertical take with no hard cuts. "
            f"Initially: {_with_dur(first['prompt'], first.get('num_frames'))}."
        ]
        for i, e in enumerate(entries[1:], start=2):
            bridge = (
                "A moment later the same continuous take evolves into"
                if i == 2
                else "Without cutting, the view gradually becomes"
            )
            chunks.append(
                f"{bridge}: {_with_dur(e['prompt'], e.get('num_frames'))}."
            )
        chunks.append(
            f"The camera never hard-cuts. Audio is one unbroken bed: {bed}."
        )
        return " ".join(chunks)

    # cut — hard picture edits, continuous score; name duration so edits pace with VO
    first = entries[0]
    chunks = [
        f"Initially: {_with_dur(first['prompt'], first.get('num_frames'))}. "
        f"Audio under this opening: {bed}."
    ]
    for e in entries[1:]:
        chunks.append(
            f"A hard cut transitions to: {_with_dur(e['prompt'], e.get('num_frames'))}. "
            f"The ambient score continues unbroken across the cut: {bed}."
        )
    chunks.append(
        "Across every hard cut the picture reframes but the same continuous "
        f"ambient bed never resets: {bed}."
    )
    return " ".join(chunks)
