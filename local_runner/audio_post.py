"""
Local post-production: Edge-TTS voiceover + Whisper captions + FFmpeg mux.

Runs on the laptop (CPU). GPU worker stays video-only.

Job fields (test_prompts.py):
  script          — narration text (omit for silent)
  voice           — preset key or full Edge-TTS id (see VOICE_PRESETS)
  captions        — False | True | caption style key (see CAPTION_STYLES)
  caption_style   — style key when captions=True (default: minimal)
"""

from __future__ import annotations

import asyncio
import os
import subprocess
from typing import Optional, Union

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

# Short keys → Edge-TTS neural voice IDs
VOICE_PRESETS = {
    "christopher": "en-US-ChristopherNeural",  # calm male (default)
    "guy": "en-US-GuyNeural",  # deeper male
    "davis": "en-US-DavisNeural",  # narrative male
    "jenny": "en-US-JennyNeural",  # clear female
    "aria": "en-US-AriaNeural",  # expressive female
    "sara": "en-US-SaraNeural",  # soft female
    "michelle": "en-US-MichelleNeural",  # warm female
    "andrew": "en-US-AndrewNeural",  # conversational male
    "emma": "en-GB-EmmaNeural",  # British female
    "ryan": "en-GB-RyanNeural",  # British male
    "sonia": "en-IN-NeerjaNeural",  # Indian English female
    "prabhat": "en-IN-PrabhatNeural",  # Indian English male
}

DEFAULT_VOICE_KEY = os.getenv("EDGE_TTS_VOICE", "christopher")

# Caption look presets (FFmpeg ASS force_style — colours are &HAABBGGRR)
CAPTION_STYLES = {
    "minimal": (
        "FontName=Arial,FontSize=11,PrimaryColour=&H00FFFFFF&,"
        "OutlineColour=&H80000000&,BorderStyle=1,Outline=1,Shadow=0,"
        "Alignment=2,MarginV=48"
    ),
    "clean": (
        "FontName=Arial,FontSize=13,PrimaryColour=&H00FFFFFF&,"
        "OutlineColour=&H00000000&,BorderStyle=1,Outline=2,Shadow=0,"
        "Alignment=2,MarginV=52"
    ),
    "boxed": (
        "FontName=Arial,FontSize=12,PrimaryColour=&H00FFFFFF&,"
        "OutlineColour=&H00000000&,BackColour=&H80000000&,BorderStyle=3,"
        "Outline=1,Shadow=0,Alignment=2,MarginV=52"
    ),
    "yellow": (
        "FontName=Arial,FontSize=14,PrimaryColour=&H0000FFFF&,"
        "OutlineColour=&H00000000&,BorderStyle=1,Outline=2,Shadow=0,"
        "Alignment=2,MarginV=56"
    ),
    "tiny": (
        "FontName=Arial,FontSize=9,PrimaryColour=&H00FFFFFF&,"
        "OutlineColour=&H80000000&,BorderStyle=1,Outline=1,Shadow=0,"
        "Alignment=2,MarginV=40"
    ),
}

DEFAULT_CAPTION_STYLE = "minimal"

_whisper_model = None


def list_voices() -> dict:
    return dict(VOICE_PRESETS)


def list_caption_styles() -> list:
    return list(CAPTION_STYLES.keys())


def resolve_voice(voice: Optional[str] = None) -> str:
    """Accept preset key, full Edge-TTS id, or env default."""
    raw = (voice or DEFAULT_VOICE_KEY or "christopher").strip()
    key = raw.lower().replace(" ", "_").replace("-", "_")
    # Allow keys like en_us_jennyneural via fuzzy: if exact preset miss, try short name
    if raw in VOICE_PRESETS:
        return VOICE_PRESETS[raw]
    if key in VOICE_PRESETS:
        return VOICE_PRESETS[key]
    # Full Edge-TTS id e.g. en-US-JennyNeural
    if "Neural" in raw or raw.count("-") >= 2:
        return raw
    # Unknown short name — fall back with warning
    print(f"⚠️ Unknown voice '{raw}'; using christopher. Presets: {', '.join(VOICE_PRESETS)}")
    return VOICE_PRESETS["christopher"]


def resolve_caption_style(style: Optional[str] = None) -> str:
    """Return ASS force_style string for a preset name."""
    if not style:
        style = DEFAULT_CAPTION_STYLE
    key = str(style).strip().lower()
    if key in CAPTION_STYLES:
        return CAPTION_STYLES[key]
    print(f"⚠️ Unknown caption_style '{style}'; using minimal. Options: {', '.join(CAPTION_STYLES)}")
    return CAPTION_STYLES[DEFAULT_CAPTION_STYLE]


def parse_captions_option(
    captions: Union[bool, str, None] = False,
    caption_style: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """
    Normalize job captions field.

    Returns (enabled, style_key).
      captions: False / "off" / "false" → off
      captions: True / "on" → on with caption_style or minimal
      captions: "minimal" | "clean" | ... → on with that style
    """
    if captions is None or captions is False:
        return False, None
    if isinstance(captions, str):
        key = captions.strip().lower()
        if key in ("", "false", "0", "no", "off", "none"):
            return False, None
        if key in ("true", "1", "yes", "on"):
            return True, (caption_style or DEFAULT_CAPTION_STYLE)
        if key in CAPTION_STYLES:
            return True, key
        print(f"⚠️ Unknown captions value '{captions}'; treating as style 'minimal'")
        return True, DEFAULT_CAPTION_STYLE
    if captions is True:
        return True, (caption_style or DEFAULT_CAPTION_STYLE)
    return False, None


def _ensure_deps():
    missing = []
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        missing.append("edge-tts")
    try:
        import whisper  # noqa: F401
    except ImportError:
        missing.append("openai-whisper")
    if missing:
        raise ImportError(
            "Missing audio deps: "
            + ", ".join(missing)
            + ". Install with: pip install edge-tts openai-whisper"
        )


async def _synthesize_voice(text: str, output_mp3: str, voice: str) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_mp3)


def generate_voiceover(
    script: str,
    output_mp3: str,
    voice: Optional[str] = None,
) -> str:
    """Generate narration MP3 via Edge-TTS (free, CPU / network)."""
    _ensure_deps()
    voice_id = resolve_voice(voice)
    os.makedirs(os.path.dirname(os.path.abspath(output_mp3)) or ".", exist_ok=True)
    print(f"🎙️ Edge-TTS → {output_mp3} (voice={voice_id})")
    asyncio.run(_synthesize_voice(script.strip(), output_mp3, voice_id))
    if not os.path.isfile(output_mp3) or os.path.getsize(output_mp3) < 100:
        raise RuntimeError(f"Edge-TTS produced empty audio: {output_mp3}")
    return output_mp3


def _srt_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    millis = int(round(seconds * 1000))
    hours, rem = divmod(millis, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def create_subtitles(audio_path: str, srt_path: str) -> str:
    """Transcribe narration with Whisper and write an SRT file."""
    global _whisper_model
    _ensure_deps()
    import whisper

    print(f"📝 Whisper ({WHISPER_MODEL}) → {srt_path}")
    if _whisper_model is None:
        _whisper_model = whisper.load_model(WHISPER_MODEL)
    result = _whisper_model.transcribe(audio_path)

    os.makedirs(os.path.dirname(os.path.abspath(srt_path)) or ".", exist_ok=True)
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(result.get("segments") or [], start=1):
            start = _srt_timestamp(float(seg["start"]))
            end = _srt_timestamp(float(seg["end"]))
            text = (seg.get("text") or "").strip()
            if not text:
                continue
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
    return srt_path


def _ffmpeg_subtitles_path(path: str) -> str:
    """Escape path for ffmpeg subtitles= filter (colons, backslashes)."""
    p = os.path.abspath(path).replace("\\", "/")
    return p.replace(":", "\\:").replace("'", "\\'")


def mux_video_audio_subs(
    video_path: str,
    audio_path: str,
    srt_path: str,
    output_path: str,
    burn_captions: bool = False,
    caption_style: Optional[str] = None,
) -> str:
    """
    Mux silent Wan MP4 + TTS audio (+ optional burned-in captions).
    Uses -shortest so output ends with the shorter of video/audio.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-i",
        audio_path,
    ]
    if burn_captions and srt_path and os.path.isfile(srt_path):
        style = resolve_caption_style(caption_style)
        sub = _ffmpeg_subtitles_path(srt_path)
        print(f"📝 Caption style: {caption_style or DEFAULT_CAPTION_STYLE}")
        cmd += [
            "-vf",
            f"subtitles={sub}:force_style='{style}'",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "18",
        ]
    else:
        cmd += ["-c:v", "copy"]

    cmd += [
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-movflags",
        "+faststart",
        output_path,
    ]
    print(f"🎬 FFmpeg mux → {output_path}")
    subprocess.run(cmd, check=True)
    return output_path


def add_voice_and_captions(
    silent_video_path: str,
    script: str,
    output_path: str,
    work_dir: Optional[str] = None,
    voice: Optional[str] = None,
    burn_captions: bool = False,
    caption_style: Optional[str] = None,
) -> str:
    """Full post pipeline: TTS → optional Whisper SRT → mux into final MP4."""
    if not script or not script.strip():
        raise ValueError("script text is required for voiceover")
    if not os.path.isfile(silent_video_path):
        raise FileNotFoundError(silent_video_path)

    work_dir = work_dir or os.path.join(os.path.dirname(output_path) or ".", "audio_work")
    os.makedirs(work_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(output_path))[0]
    mp3 = os.path.join(work_dir, f"{stem}_voice.mp3")
    srt = os.path.join(work_dir, f"{stem}_captions.srt")

    generate_voiceover(script, mp3, voice=voice)
    if burn_captions:
        create_subtitles(mp3, srt)
    else:
        print("📝 Captions off — voice only")
        srt = ""

    return mux_video_audio_subs(
        silent_video_path,
        mp3,
        srt,
        output_path,
        burn_captions=burn_captions and bool(srt),
        caption_style=caption_style,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Add Edge-TTS + optional Whisper captions to a silent MP4"
    )
    parser.add_argument("video", help="Silent input MP4")
    parser.add_argument("--script", required=True, help="Narration text")
    parser.add_argument("-o", "--output", required=True, help="Output MP4 path")
    parser.add_argument(
        "--voice",
        default=DEFAULT_VOICE_KEY,
        help=f"Preset or Edge-TTS id. Presets: {', '.join(VOICE_PRESETS)}",
    )
    parser.add_argument(
        "--captions",
        default="off",
        help=f"off | on | style. Styles: {', '.join(CAPTION_STYLES)}",
    )
    parser.add_argument("--caption-style", default=None, help="Used when --captions on")
    parser.add_argument("--list", action="store_true", help="Print voices & caption styles")
    args = parser.parse_args()

    if args.list:
        print("Voices:")
        for k, v in VOICE_PRESETS.items():
            print(f"  {k:12} → {v}")
        print("Caption styles:", ", ".join(CAPTION_STYLES))
        raise SystemExit(0)

    enabled, style = parse_captions_option(args.captions, args.caption_style)
    add_voice_and_captions(
        args.video,
        args.script,
        args.output,
        voice=args.voice,
        burn_captions=enabled,
        caption_style=style,
    )
    print(f"✅ Done: {args.output}")
