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


def _shot_texts(shots: Sequence[Any]) -> List[str]:
    out: List[str] = []
    for shot in shots:
        if isinstance(shot, dict):
            text = (shot.get("prompt") or shot.get("shot") or "").strip()
        else:
            text = str(shot).strip()
        if text:
            out.append(text)
    return out


def sum_shot_frames(
    shots: Sequence[Any],
    default_frames: Optional[int] = None,
) -> int:
    """Sum per-shot num_frames (fallback default_frames or 97)."""
    total = 0
    for shot in shots:
        if isinstance(shot, dict) and shot.get("num_frames") is not None:
            total += int(shot["num_frames"])
        elif default_frames is not None:
            total += int(default_frames)
        else:
            total += 97
    return max(17, total)


def build_multishot_prompt(
    shots: Sequence[Any],
    join_style: str = "cut",
    audio_bed: str = _AUDIO_BIBLE,
) -> str:
    """
    Collapse N shot prompts into one LTX-2.5 chronological multishot paragraph.
    """
    parts = _shot_texts(shots)
    if not parts:
        raise ValueError("build_multishot_prompt requires at least one shot")

    style = normalize_join_style(join_style)
    bed = (audio_bed or _AUDIO_BIBLE).strip()

    if len(parts) == 1:
        return (
            f"{parts[0].rstrip('. ')}. "
            f"Continuous audio throughout: {bed}."
        )

    if style == "continue":
        chunks = [
            f"One continuous locked vertical take with no hard cuts. "
            f"Initially: {parts[0].rstrip('. ')}."
        ]
        for i, p in enumerate(parts[1:], start=2):
            bridge = (
                "A moment later the same continuous take evolves into"
                if i == 2
                else "Without cutting, the view gradually becomes"
            )
            chunks.append(f"{bridge}: {p.rstrip('. ')}.")
        chunks.append(
            f"The camera never hard-cuts. Audio is one unbroken bed: {bed}."
        )
        return " ".join(chunks)

    # cut — hard picture edits, continuous score
    chunks = [
        f"Initially: {parts[0].rstrip('. ')}. "
        f"Audio under this opening: {bed}."
    ]
    for p in parts[1:]:
        chunks.append(
            f"A hard cut transitions to: {p.rstrip('. ')}. "
            f"The ambient score continues unbroken across the cut: {bed}."
        )
    chunks.append(
        "Across every hard cut the picture reframes but the same continuous "
        f"ambient bed never resets: {bed}."
    )
    return " ".join(chunks)
