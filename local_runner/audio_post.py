"""
Local post-production: Edge-TTS voiceover + ambient bed + Whisper captions + FFmpeg mux.

Runs on the laptop (CPU). GPU worker stays video-only.

Job fields (test_prompts.py):
  script          — narration text (omit for ambient-only / no VO)
  voice           — preset key or full Edge-TTS id (see VOICE_PRESETS)
  captions        — False | True | caption style key (see CAPTION_STYLES)
  caption_style   — style key when captions=True (default: minimal)
  ambient         — False | "rain" | "rain_city" | path to audio file
  title           — optional one-line overlay from 0:00 (not Whisper captions)
  vo_delay_ms     — ms of ambient-only before VO (default 900 for palate-cleanser hook)
  ambient_volume  — 0.0–1.0 bed level under VO (default 0.38)
"""

from __future__ import annotations

import asyncio
import os
import subprocess
from typing import Optional, Union

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

# Retention defaults: rain hits before the soft VO ("audio hook")
DEFAULT_AMBIENT = "rain_city"
DEFAULT_VO_DELAY_MS = 900
DEFAULT_AMBIENT_VOLUME = 0.38
AMBIENT_PRESETS = ("rain", "rain_city")

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


def _escape_drawtext(text: str) -> str:
    """Escape a short title for ffmpeg drawtext=text=..."""
    return (
        text.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("%", "\\%")
    )


def _probe_duration(path: str) -> float:
    """Return media duration in seconds via ffprobe."""
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            path,
        ],
        text=True,
    ).strip()
    return float(out)


def parse_ambient_option(ambient: Union[bool, str, None] = DEFAULT_AMBIENT) -> Optional[str]:
    """
    Normalize ambient field.

    Returns None (off), a preset name ("rain" / "rain_city"), or an absolute file path.
    """
    if ambient is None or ambient is False:
        return None
    if ambient is True:
        return DEFAULT_AMBIENT
    if isinstance(ambient, str):
        key = ambient.strip()
        if key.lower() in ("", "false", "0", "no", "off", "none"):
            return None
        if key.lower() in ("true", "1", "yes", "on"):
            return DEFAULT_AMBIENT
        low = key.lower()
        if low in AMBIENT_PRESETS:
            return low
        if os.path.isfile(key):
            return os.path.abspath(key)
        print(f"⚠️ ambient '{ambient}' not found; using rain_city. Presets: {', '.join(AMBIENT_PRESETS)}")
        return DEFAULT_AMBIENT
    return DEFAULT_AMBIENT


def generate_ambient_bed(
    duration_s: float,
    output_wav: str,
    preset: str = "rain_city",
    volume: float = DEFAULT_AMBIENT_VOLUME,
) -> str:
    """
    Synthesize a rain / rain+city bed with FFmpeg lavfi (no external sample packs).

    rain      — pink-noise rain texture (heavy droplets feel)
    rain_city — rain + low street hum (default palate-cleanser bed)
    """
    if duration_s <= 0.2:
        raise ValueError(f"duration too short for ambient: {duration_s}")
    os.makedirs(os.path.dirname(os.path.abspath(output_wav)) or ".", exist_ok=True)
    dur = f"{duration_s:.3f}"
    vol = max(0.05, min(1.0, float(volume)))

    if preset == "rain":
        # Broadband rain-ish texture
        af = (
            f"highpass=f=180,lowpass=f=10000,volume={vol:.3f},"
            f"afade=t=in:st=0:d=0.25,afade=t=out:st={max(0.0, duration_s - 0.4):.3f}:d=0.4"
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"anoisesrc=color=pink:amplitude=0.55:duration={dur}",
            "-af",
            af,
            output_wav,
        ]
    else:
        # rain_city: rain layer + low brown-noise street hum
        # [0] pink → rain, [1] brown → hum; amix to one bed
        rain_v = vol
        hum_v = vol * 0.45
        fade_out_st = max(0.0, duration_s - 0.4)
        filter = (
            f"[0:a]highpass=f=200,lowpass=f=11000,volume={rain_v:.3f}[rain];"
            f"[1:a]lowpass=f=160,volume={hum_v:.3f}[hum];"
            f"[rain][hum]amix=inputs=2:duration=longest:dropout_transition=0,"
            f"afade=t=in:st=0:d=0.25,afade=t=out:st={fade_out_st:.3f}:d=0.4[out]"
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"anoisesrc=color=pink:amplitude=0.55:duration={dur}",
            "-f",
            "lavfi",
            "-i",
            f"anoisesrc=color=brown:amplitude=0.4:duration={dur}",
            "-filter_complex",
            filter,
            "-map",
            "[out]",
            output_wav,
        ]

    print(f"🌧️ Ambient bed ({preset}, {duration_s:.1f}s, vol={vol:.2f}) → {output_wav}")
    subprocess.run(cmd, check=True, capture_output=True)
    if not os.path.isfile(output_wav) or os.path.getsize(output_wav) < 100:
        raise RuntimeError(f"Ambient bed empty: {output_wav}")
    return output_wav


def mix_voice_with_ambient(
    voice_mp3: str,
    ambient_path: str,
    output_wav: str,
    video_duration_s: float,
    vo_delay_ms: int = DEFAULT_VO_DELAY_MS,
    voice_volume: float = 1.0,
) -> str:
    """
    Delay VO so ambient alone owns the first ~1s (swipe decision window),
    then mix under the soft narration. Output length = video duration.
    """
    delay = max(0, int(vo_delay_ms))
    # adelay wants ms per channel for stereo; mono gets one value
    filter = (
        f"[1:a]volume={voice_volume:.3f},adelay={delay}|{delay},"
        f"apad=whole_dur={video_duration_s:.3f}[vo];"
        f"[0:a][vo]amix=inputs=2:duration=first:dropout_transition=0,"
        f"alimiter=limit=0.95[out]"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        ambient_path,
        "-i",
        voice_mp3,
        "-filter_complex",
        filter,
        "-map",
        "[out]",
        "-t",
        f"{video_duration_s:.3f}",
        output_wav,
    ]
    print(f"🎚️ Mix VO + ambient (vo_delay={delay}ms) → {output_wav}")
    subprocess.run(cmd, check=True, capture_output=True)
    return output_wav


def mux_video_audio_subs(
    video_path: str,
    audio_path: str,
    srt_path: str,
    output_path: str,
    burn_captions: bool = False,
    caption_style: Optional[str] = None,
    match_video_duration: bool = True,
) -> str:
    """
    Mux silent Wan MP4 + mixed audio (+ optional burned-in captions).

    By default output length follows the video (ambient fills the bed),
    so a short VO no longer truncates the Short with -shortest.
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
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
    ]
    if match_video_duration:
        cmd += ["-t", f"{_probe_duration(video_path):.3f}"]
    else:
        cmd += ["-shortest"]
    cmd += [
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
    ambient: Union[bool, str, None] = DEFAULT_AMBIENT,
    vo_delay_ms: int = DEFAULT_VO_DELAY_MS,
    ambient_volume: float = DEFAULT_AMBIENT_VOLUME,
) -> str:
    """Full post pipeline: TTS → ambient bed → optional Whisper SRT → mux."""
    if not script or not script.strip():
        raise ValueError("script text is required for voiceover")
    if not os.path.isfile(silent_video_path):
        raise FileNotFoundError(silent_video_path)

    work_dir = work_dir or os.path.join(os.path.dirname(output_path) or ".", "audio_work")
    os.makedirs(work_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(output_path))[0]
    mp3 = os.path.join(work_dir, f"{stem}_voice.mp3")
    mixed = os.path.join(work_dir, f"{stem}_mix.wav")
    srt = os.path.join(work_dir, f"{stem}_captions.srt")

    generate_voiceover(script, mp3, voice=voice)
    if burn_captions:
        create_subtitles(mp3, srt)
    else:
        print("📝 Captions off — voice only")
        srt = ""

    video_dur = _probe_duration(silent_video_path)
    ambient_key = parse_ambient_option(ambient)
    final_audio = mp3

    if ambient_key:
        bed = os.path.join(work_dir, f"{stem}_ambient.wav")
        if ambient_key in AMBIENT_PRESETS:
            generate_ambient_bed(
                video_dur,
                bed,
                preset=ambient_key,
                volume=ambient_volume,
            )
        else:
            # Custom file: loop/trim to video length
            print(f"🌧️ Ambient file → {ambient_key}")
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-stream_loop",
                    "-1",
                    "-i",
                    ambient_key,
                    "-t",
                    f"{video_dur:.3f}",
                    "-af",
                    f"volume={float(ambient_volume):.3f}",
                    bed,
                ],
                check=True,
                capture_output=True,
            )
        mix_voice_with_ambient(
            mp3,
            bed,
            mixed,
            video_duration_s=video_dur,
            vo_delay_ms=vo_delay_ms,
        )
        final_audio = mixed
    else:
        print("🌧️ Ambient off — VO only (weak Shorts hook)")

    return mux_video_audio_subs(
        silent_video_path,
        final_audio,
        srt,
        output_path,
        burn_captions=burn_captions and bool(srt),
        caption_style=caption_style,
        match_video_duration=True,
    )


def add_ambient_and_title(
    silent_video_path: str,
    output_path: str,
    work_dir: Optional[str] = None,
    ambient: Union[bool, str, None] = DEFAULT_AMBIENT,
    ambient_volume: float = DEFAULT_AMBIENT_VOLUME,
    title: Optional[str] = None,
) -> str:
    """Rain/city bed from 0:00, optional one-line title overlay. No VO."""
    if not os.path.isfile(silent_video_path):
        raise FileNotFoundError(silent_video_path)

    work_dir = work_dir or os.path.join(os.path.dirname(output_path) or ".", "audio_work")
    os.makedirs(work_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(output_path))[0]
    video_dur = _probe_duration(silent_video_path)
    ambient_key = parse_ambient_option(ambient)
    title_text = (title or "").strip()

    audio_path = None
    if ambient_key:
        bed = os.path.join(work_dir, f"{stem}_ambient.wav")
        if ambient_key in AMBIENT_PRESETS:
            generate_ambient_bed(
                video_dur,
                bed,
                preset=ambient_key,
                volume=ambient_volume,
            )
        else:
            print(f"🌧️ Ambient file → {ambient_key}")
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-stream_loop",
                    "-1",
                    "-i",
                    ambient_key,
                    "-t",
                    f"{video_dur:.3f}",
                    "-af",
                    f"volume={float(ambient_volume):.3f}",
                    bed,
                ],
                check=True,
                capture_output=True,
            )
        audio_path = bed

    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
    cmd = ["ffmpeg", "-y", "-i", silent_video_path]
    if audio_path:
        cmd += ["-i", audio_path]

    vf = None
    if title_text:
        vf = (
            "drawtext=text='{text}':fontsize=36:fontcolor=white@0.92:"
            "borderw=2:bordercolor=black@0.55:x=(w-text_w)/2:y=h*0.10"
        ).format(text=_escape_drawtext(title_text))
        print(f"📝 Title overlay: {title_text}")

    if vf:
        cmd += ["-vf", vf, "-c:v", "libx264", "-preset", "fast", "-crf", "18"]
    else:
        cmd += ["-c:v", "copy"]

    if audio_path:
        cmd += [
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-t",
            f"{video_dur:.3f}",
        ]
    else:
        cmd += ["-an", "-map", "0:v:0"]
        print("🌧️ Ambient off — silent video")

    cmd += ["-movflags", "+faststart", output_path]
    print(f"🎬 FFmpeg ambient/title mux → {output_path}")
    subprocess.run(cmd, check=True)
    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Add Edge-TTS + ambient bed + optional Whisper captions to a silent MP4"
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
    parser.add_argument(
        "--ambient",
        default=DEFAULT_AMBIENT,
        help=f"off | {' | '.join(AMBIENT_PRESETS)} | path/to.wav (default: {DEFAULT_AMBIENT})",
    )
    parser.add_argument(
        "--vo-delay-ms",
        type=int,
        default=DEFAULT_VO_DELAY_MS,
        help=f"Ambient-only ms before VO (default: {DEFAULT_VO_DELAY_MS})",
    )
    parser.add_argument(
        "--ambient-volume",
        type=float,
        default=DEFAULT_AMBIENT_VOLUME,
        help=f"Bed level 0–1 (default: {DEFAULT_AMBIENT_VOLUME})",
    )
    parser.add_argument("--list", action="store_true", help="Print voices & caption styles")
    args = parser.parse_args()

    if args.list:
        print("Voices:")
        for k, v in VOICE_PRESETS.items():
            print(f"  {k:12} → {v}")
        print("Caption styles:", ", ".join(CAPTION_STYLES))
        print("Ambient presets:", ", ".join(AMBIENT_PRESETS))
        raise SystemExit(0)

    enabled, style = parse_captions_option(args.captions, args.caption_style)
    add_voice_and_captions(
        args.video,
        args.script,
        args.output,
        voice=args.voice,
        burn_captions=enabled,
        caption_style=style,
        ambient=args.ambient,
        vo_delay_ms=args.vo_delay_ms,
        ambient_volume=args.ambient_volume,
    )
    print(f"✅ Done: {args.output}")
