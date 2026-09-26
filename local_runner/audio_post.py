"""
Local post-production: Edge-TTS voiceover + ambient bed + Whisper captions + FFmpeg mux.

Runs on the laptop (CPU). GPU worker stays video-only.

Job fields (test_prompts.py):
  script          — narration text (omit for ambient-only / no VO)
  script_beats    — optional list of {text, rate?, pitch?, pause_ms?} for per-beat pacing
  voice           — preset key or full Edge-TTS id (see VOICE_PRESETS)
  voice_rate      — default Edge-TTS rate when a beat omits rate (e.g. "-8%")
  voice_pitch     — default Edge-TTS pitch (e.g. "-2Hz")
  captions        — False | True | caption style key (see CAPTION_STYLES)
  caption_style   — style key when captions=True (default: clean)
  ambient         — False | "rain" | "rain_city" | "space" | "ltx" | path to audio file
                    "ltx" keeps native LTX AV bed and mixes VO on top (duck under narration)
  title           — optional one-line overlay from 0:00 (not Whisper captions)
  vo_delay_ms     — ms of ambient-only before VO (default 900 for palate-cleanser hook)
  ambient_volume  — 0.0–1.0 bed level under VO (default 0.38)
"""

from __future__ import annotations

import asyncio
import os
import re
import subprocess
from typing import Any, Optional, Union

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

# Retention defaults: rain hits before the soft VO ("audio hook")
DEFAULT_AMBIENT = "rain_city"
DEFAULT_VO_DELAY_MS = 900
DEFAULT_AMBIENT_VOLUME = 0.38
AMBIENT_PRESETS = ("rain", "rain_city", "space")
# Special: extract + duck native video audio (LTX one-pass / multishot)
AMBIENT_LTX = "ltx"

# Short keys → Edge-TTS neural voice IDs
VOICE_PRESETS = {
    "christopher": "en-US-ChristopherNeural",  # calm male (default)
    "guy": "en-US-GuyNeural",  # deeper male
    # DavisNeural removed from Edge-TTS catalog; Guy is the closest narrative male.
    "davis": "en-US-GuyNeural",
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
# FontSize is ASS relative; ~15–16 reads on 1080x1920 without a box.
CAPTION_STYLES = {
    "minimal": (
        "FontName=Arial,FontSize=10,PrimaryColour=&H00FFFFFF&,"
        "OutlineColour=&H80000000&,BorderStyle=1,Outline=1,Shadow=0,"
        "Alignment=2,MarginV=52"
    ),
    "clean": (
        "FontName=Arial,FontSize=11,PrimaryColour=&H00FFFFFF&,"
        "OutlineColour=&H00000000&,BorderStyle=1,Outline=1,Shadow=0,"
        "Alignment=2,MarginV=56"
    ),
    "boxed": (
        "FontName=Arial,FontSize=10,PrimaryColour=&H00FFFFFF&,"
        "OutlineColour=&H00000000&,BackColour=&H80000000&,BorderStyle=3,"
        "Outline=1,Shadow=0,Alignment=2,MarginV=52"
    ),
    "yellow": (
        "FontName=Arial,FontSize=12,PrimaryColour=&H0000FFFF&,"
        "OutlineColour=&H00000000&,BorderStyle=1,Outline=2,Shadow=0,"
        "Alignment=2,MarginV=56"
    ),
    "tiny": (
        "FontName=Arial,FontSize=8,PrimaryColour=&H00FFFFFF&,"
        "OutlineColour=&H80000000&,BorderStyle=1,Outline=1,Shadow=0,"
        "Alignment=2,MarginV=48"
    ),
}

DEFAULT_CAPTION_STYLE = "clean"
DEFAULT_VOICE_RATE = os.getenv("EDGE_TTS_RATE", "+0%")
DEFAULT_VOICE_PITCH = os.getenv("EDGE_TTS_PITCH", "+0Hz")

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


def _normalize_rate(rate: Optional[str] = None) -> str:
    raw = (rate if rate is not None else DEFAULT_VOICE_RATE) or "+0%"
    raw = str(raw).strip()
    if not raw:
        return "+0%"
    # Allow bare ints like "-8" → "-8%"
    if raw[-1].isdigit():
        return f"{raw}%"
    return raw


def _normalize_pitch(pitch: Optional[str] = None) -> str:
    raw = (pitch if pitch is not None else DEFAULT_VOICE_PITCH) or "+0Hz"
    raw = str(raw).strip()
    if not raw:
        return "+0Hz"
    if raw[-1].isdigit():
        return f"{raw}Hz"
    return raw


def script_beats_to_text(beats: list) -> str:
    """Join beat texts for Whisper / logging."""
    parts = []
    for b in beats or []:
        t = (b.get("text") or "").strip()
        if t:
            parts.append(t)
    return "\n\n".join(parts)


def normalize_script_beats(
    script: Optional[str] = None,
    script_beats: Optional[list] = None,
    default_rate: Optional[str] = None,
    default_pitch: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Build a list of beats: {text, rate, pitch, pause_ms}.

    Accepts:
      - script_beats: list of dicts (preferred)
      - tagged script blocks:
            [rate=-12%][pause_after=400]
            Hook line...
      - plain script → one beat with defaults
    """
    rate0 = _normalize_rate(default_rate)
    pitch0 = _normalize_pitch(default_pitch)

    if script_beats:
        out = []
        for i, raw in enumerate(script_beats):
            if not isinstance(raw, dict):
                raise ValueError(f"script_beats[{i}] must be a dict")
            text = (raw.get("text") or "").strip()
            if not text:
                continue
            pause = raw.get("pause_ms", raw.get("pause_after", 0))
            beat = {
                "text": text,
                "rate": _normalize_rate(raw.get("rate", rate0)),
                "pitch": _normalize_pitch(raw.get("pitch", pitch0)),
                "pause_ms": max(0, int(pause or 0)),
            }
            # Carry the caption override through: TTS always speaks "text", but the
            # burned caption uses "caption_text" when set, so the VO can say
            # "six hundred seventeen point five" while the screen reads "617.5 km/s".
            caption_text = (raw.get("caption_text") or "").strip()
            if caption_text:
                beat["caption_text"] = caption_text
            out.append(beat)
        if not out:
            raise ValueError("script_beats produced no speakable text")
        return out

    if not script or not str(script).strip():
        raise ValueError("script or script_beats is required")

    text = str(script).strip()
    # Tagged multi-beat script?
    if re.search(r"\[(rate|pitch|pause_after|pause_ms)=", text, re.I):
        return _parse_tagged_script(text, rate0, pitch0)

    return [{"text": text, "rate": rate0, "pitch": pitch0, "pause_ms": 0}]


_BEAT_TAG_RE = re.compile(
    r"\[(rate|pitch|pause_after|pause_ms)=([^\]]+)\]",
    re.IGNORECASE,
)


def _parse_tagged_script(text: str, rate0: str, pitch0: str) -> list[dict[str, Any]]:
    """Split a script that uses [rate=…][pause_after=…] headers before each beat."""
    parts = re.split(r"(?=(?:\[(?:rate|pitch|pause_after|pause_ms)=[^\]]+\])+)", text)
    beats = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        rate, pitch, pause = rate0, pitch0, 0
        headers = list(_BEAT_TAG_RE.finditer(part))
        body_start = 0
        for m in headers:
            if m.start() > body_start and part[body_start : m.start()].strip():
                break
            key = m.group(1).lower()
            val = m.group(2).strip()
            if key == "rate":
                rate = _normalize_rate(val)
            elif key == "pitch":
                pitch = _normalize_pitch(val)
            else:
                pause = max(0, int(float(val)))
            body_start = m.end()
        body = part[body_start:].strip()
        if not body:
            continue
        beats.append({"text": body, "rate": rate, "pitch": pitch, "pause_ms": pause})
    if not beats:
        return [{"text": text, "rate": rate0, "pitch": pitch0, "pause_ms": 0}]
    return beats


async def _synthesize_voice(
    text: str,
    output_mp3: str,
    voice: str,
    rate: str = "+0%",
    pitch: str = "+0Hz",
) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(output_mp3)


def _silence_wav(path: str, duration_ms: int, sample_rate: int = 24000) -> str:
    """Write mono silence WAV of duration_ms."""
    dur_s = max(0.01, duration_ms / 1000.0)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"anullsrc=r={sample_rate}:cl=mono",
            "-t",
            f"{dur_s:.3f}",
            path,
        ],
        check=True,
        capture_output=True,
    )
    return path


def _mp3_to_wav(mp3_path: str, wav_path: str, sample_rate: int = 24000) -> str:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            mp3_path,
            "-ac",
            "1",
            "-ar",
            str(sample_rate),
            wav_path,
        ],
        check=True,
        capture_output=True,
    )
    return wav_path


def _concat_wavs(wav_paths: list[str], output_wav: str) -> str:
    if not wav_paths:
        raise ValueError("no wav segments to concat")
    if len(wav_paths) == 1:
        subprocess.run(["cp", "-f", wav_paths[0], output_wav], check=True)
        return output_wav
    list_file = output_wav + ".concat.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for p in wav_paths:
            f.write(f"file '{os.path.abspath(p)}'\n")
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
            output_wav,
        ],
        check=True,
        capture_output=True,
    )
    return output_wav


def generate_voiceover(
    script: Optional[str] = None,
    output_mp3: Optional[str] = None,
    voice: Optional[str] = None,
    rate: Optional[str] = None,
    pitch: Optional[str] = None,
    script_beats: Optional[list] = None,
    work_dir: Optional[str] = None,
) -> str:
    """
    Generate narration via Edge-TTS.

    If script_beats (or tagged script) has multiple rates/pauses, synthesize
    each beat separately and concat with silence. Otherwise one Edge-TTS call.
    """
    if output_mp3 is None:
        raise ValueError("output_mp3 is required")
    _ensure_deps()
    beats = normalize_script_beats(
        script=script,
        script_beats=script_beats,
        default_rate=rate,
        default_pitch=pitch,
    )
    voice_id = resolve_voice(voice)
    os.makedirs(os.path.dirname(os.path.abspath(output_mp3)) or ".", exist_ok=True)

    # Single beat, no trailing pause → one shot (fast path)
    if len(beats) == 1 and not beats[0]["pause_ms"]:
        b = beats[0]
        print(
            f"🎙️ Edge-TTS → {output_mp3} "
            f"(voice={voice_id}, rate={b['rate']}, pitch={b['pitch']})"
        )
        asyncio.run(
            _synthesize_voice(b["text"], output_mp3, voice_id, rate=b["rate"], pitch=b["pitch"])
        )
        if not os.path.isfile(output_mp3) or os.path.getsize(output_mp3) < 100:
            raise RuntimeError(f"Edge-TTS produced empty audio: {output_mp3}")
        return output_mp3

    seg_dir = work_dir or os.path.dirname(os.path.abspath(output_mp3)) or "."
    os.makedirs(seg_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(output_mp3))[0]
    wav_parts: list[str] = []
    print(f"🎙️ Edge-TTS beats → {len(beats)} segments (voice={voice_id})")

    async def _all():
        for i, b in enumerate(beats, start=1):
            mp3_i = os.path.join(seg_dir, f"{stem}_beat{i}.mp3")
            wav_i = os.path.join(seg_dir, f"{stem}_beat{i}.wav")
            print(
                f"   beat {i}/{len(beats)} rate={b['rate']} pitch={b['pitch']} "
                f"pause_ms={b['pause_ms']} | {b['text'][:48].replace(chr(10), ' ')}…"
            )
            await _synthesize_voice(b["text"], mp3_i, voice_id, rate=b["rate"], pitch=b["pitch"])
            if not os.path.isfile(mp3_i) or os.path.getsize(mp3_i) < 100:
                raise RuntimeError(f"Edge-TTS empty beat {i}: {mp3_i}")
            _mp3_to_wav(mp3_i, wav_i)
            wav_parts.append(wav_i)
            if b["pause_ms"] > 0:
                sil = os.path.join(seg_dir, f"{stem}_pause{i}.wav")
                _silence_wav(sil, b["pause_ms"])
                wav_parts.append(sil)

    asyncio.run(_all())
    concat_wav = os.path.join(seg_dir, f"{stem}_beats.wav")
    _concat_wavs(wav_parts, concat_wav)
    # Encode to mp3 for downstream mix (ffmpeg accepts either; keep .mp3 path)
    subprocess.run(
        ["ffmpeg", "-y", "-i", concat_wav, "-codec:a", "libmp3lame", "-q:a", "2", output_mp3],
        check=True,
        capture_output=True,
    )
    if not os.path.isfile(output_mp3) or os.path.getsize(output_mp3) < 100:
        raise RuntimeError(f"Edge-TTS beat concat empty: {output_mp3}")
    dur = _probe_duration(output_mp3)
    print(f"🎙️ Beat VO ready ({dur:.1f}s) → {output_mp3}")
    return output_mp3


def _srt_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    millis = int(round(seconds * 1000))
    hours, rem = divmod(millis, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def _parse_srt_timestamp(ts: str) -> float:
    """Parse 'HH:MM:SS,mmm' → seconds."""
    ts = ts.strip().replace(".", ",")
    hms, ms = ts.split(",")
    h, m, s = hms.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def shift_srt_file(srt_path: str, delay_ms: int, output_path: Optional[str] = None) -> str:
    """
    Shift all SRT cue times by delay_ms (positive = later).

    Needed because Whisper times the raw VO at t=0, but mix_voice_with_ambient
    applies adelay=vo_delay_ms before the VO is heard in the final mux.
    """
    delay_ms = int(delay_ms or 0)
    out = output_path or srt_path
    if delay_ms == 0:
        if out != srt_path:
            subprocess.run(["cp", "-f", srt_path, out], check=True)
        return out

    delay_s = delay_ms / 1000.0
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    cue_re = re.compile(
        r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})"
    )

    def _shift(m: re.Match) -> str:
        start = _parse_srt_timestamp(m.group(1)) + delay_s
        end = _parse_srt_timestamp(m.group(2)) + delay_s
        return f"{_srt_timestamp(start)} --> {_srt_timestamp(end)}"

    shifted = cue_re.sub(_shift, content)
    with open(out, "w", encoding="utf-8") as f:
        f.write(shifted)
    print(f"📝 SRT shifted +{delay_ms}ms → {out}")
    return out


def clamp_srt_file(srt_path: str, max_duration_s: float, output_path: Optional[str] = None) -> str:
    """Drop/truncate cues that extend past max_duration_s (video length)."""
    out = output_path or srt_path
    max_s = max(0.05, float(max_duration_s))
    with open(srt_path, "r", encoding="utf-8") as f:
        blocks = re.split(r"\n\s*\n", f.read().strip())
    kept = []
    idx = 1
    for block in blocks:
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if len(lines) < 2 or "-->" not in lines[1]:
            continue
        start_s, end_s = [
            _parse_srt_timestamp(p.strip()) for p in lines[1].replace(" --> ", "-->").split("-->")
        ]
        if start_s >= max_s - 0.05:
            continue
        end_s = min(end_s, max_s)
        if end_s - start_s < 0.05:
            continue
        text = "\n".join(lines[2:]).strip()
        if not text:
            continue
        kept.append(
            f"{idx}\n{_srt_timestamp(start_s)} --> {_srt_timestamp(end_s)}\n{text}\n"
        )
        idx += 1
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(kept) + ("\n" if kept else ""))
    print(f"📝 SRT clamped to {max_s:.2f}s ({len(kept)} cues) → {out}")
    return out


def create_subtitles_from_beats(
    script_beats: list,
    work_dir: str,
    stem: str,
    srt_path: str,
    default_rate: Optional[str] = None,
    default_pitch: Optional[str] = None,
) -> str:
    """
    Build SRT from Edge-TTS beat wav durations (exact VO timeline).

    Prefer this over Whisper when script_beats exist — cues match narration
    lines and don't drift past the video.
    """
    beats = normalize_script_beats(
        script_beats=script_beats,
        default_rate=default_rate,
        default_pitch=default_pitch,
    )
    if not beats:
        raise ValueError("script_beats empty — cannot build beat captions")

    cues: list[tuple[float, float, str]] = []
    t = 0.0
    for i, b in enumerate(beats, start=1):
        wav = os.path.join(work_dir, f"{stem}_beat{i}.wav")
        if not os.path.isfile(wav):
            raise FileNotFoundError(f"Missing beat wav for captions: {wav}")
        dur = _probe_duration(wav)
        # "caption_text" lets a beat show different text than it speaks, so the VO
        # can say "six hundred seventeen point five" while the caption reads "617.5
        # km/s" (strategy: numbers highlighted). Falls back to "text" when unset.
        lines = [
            ln.strip()
            for ln in str(b.get("caption_text") or b.get("text") or "")
            .replace("\r", "")
            .split("\n")
            if ln.strip()
        ]
        if not lines:
            t += dur
            pause_ms = int(b.get("pause_ms") or 0)
            if pause_ms > 0:
                t += pause_ms / 1000.0
            continue
        weights = [max(1, len(ln)) for ln in lines]
        total_w = float(sum(weights))
        cursor = t
        for ln, w in zip(lines, weights):
            seg = dur * (w / total_w)
            end = cursor + seg
            cues.append((cursor, end, ln))
            cursor = end
        t += dur
        pause_ms = int(b.get("pause_ms") or 0)
        if pause_ms > 0:
            t += pause_ms / 1000.0

    os.makedirs(os.path.dirname(os.path.abspath(srt_path)) or ".", exist_ok=True)
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, (start, end, text) in enumerate(cues, start=1):
            f.write(
                f"{i}\n{_srt_timestamp(start)} --> {_srt_timestamp(end)}\n{text}\n\n"
            )
    print(f"📝 Beat-timed captions ({len(cues)} cues, VO≈{t:.1f}s) → {srt_path}")
    return srt_path


def nearest_ltx_frames(seconds: float, fps: float = 24.0) -> int:
    """Map a target duration to LTX 8k+1 frame count."""
    n = max(17, int(round(float(seconds) * float(fps))))
    k = max(2, round((n - 1) / 8.0))
    return 8 * k + 1


def beat_shot_durations_s(
    script_beats: list,
    work_dir: str,
    stem: str,
    vo_delay_ms: int = 0,
    default_rate: Optional[str] = None,
    default_pitch: Optional[str] = None,
) -> list[float]:
    """
    Per-shot target durations so picture cuts land when the next VO beat starts.

    shot[i] = beat[i] duration + pause_ms[i]/1000
    shot[0] also includes vo_delay_ms (ambient-only hook before narration).
    Requires `{stem}_beat{i}.wav` from generate_voiceover.
    """
    beats = normalize_script_beats(
        script_beats=script_beats,
        default_rate=default_rate,
        default_pitch=default_pitch,
    )
    if not beats:
        raise ValueError("script_beats empty")
    durs: list[float] = []
    for i, b in enumerate(beats, start=1):
        wav = os.path.join(work_dir, f"{stem}_beat{i}.wav")
        if not os.path.isfile(wav):
            raise FileNotFoundError(f"Missing beat wav: {wav}")
        dur = _probe_duration(wav) + max(0, int(b.get("pause_ms") or 0)) / 1000.0
        if i == 1:
            dur += max(0, int(vo_delay_ms or 0)) / 1000.0
        durs.append(max(0.5, dur))
    return durs


def fit_clip_duration(src: str, dst: str, target_s: float, fps: float = 24.0) -> str:
    """
    Fit a clip to target_s without freezing the last frame.

    - Too short: time-stretch (setpts + atempo) so motion continues
    - Too long: trim
    Keeps audio when present (needed for ambient=ltx under VO).
    """
    cur = _probe_duration(src)
    target_s = max(0.5, float(target_s))
    os.makedirs(os.path.dirname(os.path.abspath(dst)) or ".", exist_ok=True)
    has_audio = _probe_has_audio(src)

    if abs(cur - target_s) < 0.04:
        subprocess.run(["cp", "-f", src, dst], check=True)
        return dst

    if cur < target_s:
        # Prefer gentle slowdown over tpad freeze (stuck end-of-shot).
        ratio = target_s / cur
        # Cap extreme stretch; leftover would be rare for our beat windows.
        stretch = min(ratio, 2.0)
        vf = f"setpts={stretch:.6f}*PTS,fps={fps:.3f}"
        print(
            f"🎞️ Stretch {os.path.basename(src)} {cur:.2f}s → {target_s:.2f}s "
            f"(x{stretch:.3f}, no freeze)"
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            src,
            "-vf",
            vf,
            "-t",
            f"{target_s:.3f}",
        ]
        if has_audio:
            # atempo = 1/stretch; chain if outside 0.5–2.0
            tempo = cur / (cur * stretch)  # == 1/stretch
            af_parts = _atempo_chain(tempo)
            cmd += ["-af", ",".join(af_parts), "-c:a", "aac", "-b:a", "192k"]
        else:
            cmd += ["-an"]
        cmd += [
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            dst,
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        # If stretch capped below target, pad remaining with freeze as last resort.
        out_dur = _probe_duration(dst)
        if out_dur + 0.05 < target_s:
            pad = target_s - out_dur
            tmp = dst + ".pad.mp4"
            print(f"🎞️ Residual pad {pad:.2f}s freeze after max stretch")
            vf_pad = f"tpad=stop_mode=clone:stop_duration={pad:.3f},fps={fps:.3f}"
            pad_cmd = [
                "ffmpeg",
                "-y",
                "-i",
                dst,
                "-vf",
                vf_pad,
                "-t",
                f"{target_s:.3f}",
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
            ]
            if has_audio:
                pad_cmd += [
                    "-af",
                    f"apad=pad_dur={pad:.3f}",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "192k",
                ]
            else:
                pad_cmd += ["-an"]
            pad_cmd += [tmp]
            subprocess.run(pad_cmd, check=True, capture_output=True)
            os.replace(tmp, dst)
        return dst

    print(f"🎞️ Trim {os.path.basename(src)} {cur:.2f}s → {target_s:.2f}s")
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        src,
        "-t",
        f"{target_s:.3f}",
        "-vf",
        f"fps={fps:.3f}",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
    ]
    if has_audio:
        cmd += ["-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-an"]
    cmd += [dst]
    subprocess.run(cmd, check=True, capture_output=True)
    return dst


def _atempo_chain(tempo: float) -> list[str]:
    """Build atempo filter chain; each stage must be in [0.5, 2.0]."""
    t = max(0.05, float(tempo))
    parts: list[str] = []
    # Speed up
    while t > 2.0 + 1e-6:
        parts.append("atempo=2.0")
        t /= 2.0
    # Slow down
    while t < 0.5 - 1e-6:
        parts.append("atempo=0.5")
        t /= 0.5
    parts.append(f"atempo={t:.6f}")
    return parts


def concat_clips_crossfade(
    paths: list[str],
    output_path: str,
    fade_s: float = 0.35,
    fps: float = 24.0,
) -> str:
    """
    Soft-cut stitch: video xfade + audio acrossfade.
    paths must already be duration-fitted (include +fade_s on all but last if
    you need final length ≈ sum of beat targets).
    """
    if not paths:
        raise ValueError("no clips to concat")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
    fade_s = max(0.05, min(1.0, float(fade_s)))

    if len(paths) == 1:
        subprocess.run(["cp", "-f", paths[0], output_path], check=True)
        return output_path

    durs = [_probe_duration(p) for p in paths]
    # Ensure every clip has an audio stream for acrossfade (silence if missing).
    prepared: list[str] = []
    work = os.path.join(os.path.dirname(output_path) or ".", "_xfade_prep")
    os.makedirs(work, exist_ok=True)
    for i, p in enumerate(paths):
        if _probe_has_audio(p):
            prepared.append(p)
            continue
        silent = os.path.join(work, f"silent_a_{i}.mp4")
        dur = durs[i]
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                p,
                "-f",
                "lavfi",
                "-i",
                f"anullsrc=r=48000:cl=stereo",
                "-t",
                f"{dur:.3f}",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-shortest",
                silent,
            ],
            check=True,
            capture_output=True,
        )
        prepared.append(silent)
        durs[i] = _probe_duration(silent)

    n = len(prepared)
    cmd = ["ffmpeg", "-y"]
    for p in prepared:
        cmd += ["-i", p]

    filters: list[str] = []
    # Normalize pixel formats for xfade
    for i in range(n):
        filters.append(f"[{i}:v]fps={fps:.3f},format=yuv420p[v{i}]")
        filters.append(f"[{i}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[a{i}]")

    offset = durs[0] - fade_s
    filters.append(
        f"[v0][v1]xfade=transition=fade:duration={fade_s:.3f}:offset={max(0.0, offset):.3f}[vx1]"
    )
    filters.append(
        f"[a0][a1]acrossfade=d={fade_s:.3f}[ax1]"
    )
    for i in range(2, n):
        offset += durs[i - 1] - fade_s
        prev_v = f"vx{i-1}"
        prev_a = f"ax{i-1}"
        filters.append(
            f"[{prev_v}][v{i}]xfade=transition=fade:duration={fade_s:.3f}:offset={max(0.0, offset):.3f}[vx{i}]"
        )
        filters.append(f"[{prev_a}][a{i}]acrossfade=d={fade_s:.3f}[ax{i}]")

    last = n - 1
    filter_complex = ";".join(filters)
    cmd += [
        "-filter_complex",
        filter_complex,
        "-map",
        f"[vx{last}]",
        "-map",
        f"[ax{last}]",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        output_path,
    ]
    print(f"🎞️ Crossfade stitch ({n} clips, fade={fade_s:.2f}s) → {output_path}")
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def fit_shots_to_voice_beats(
    shot_paths: list[str],
    script_beats: list,
    work_dir: str,
    voice_stem: str,
    vo_delay_ms: int = 0,
    voice: Optional[str] = None,
    voice_rate: Optional[str] = None,
    voice_pitch: Optional[str] = None,
    crossfade_s: float = 0.0,
) -> list[str]:
    """
    Ensure VO beat wavs exist, then pad/trim each shot so cut points match narration.
    If crossfade_s > 0, every shot except the last is lengthened by crossfade_s so
    that after xfade the timeline still matches VO beat sum.
    Returns paths to fitted clips (same length as shot_paths).
    """
    if len(shot_paths) != len(
        normalize_script_beats(
            script_beats=script_beats, default_rate=voice_rate, default_pitch=voice_pitch
        )
    ):
        beats = normalize_script_beats(
            script_beats=script_beats, default_rate=voice_rate, default_pitch=voice_pitch
        )
        print(
            f"⚠️ shot count {len(shot_paths)} != beat count {len(beats)}; "
            "fitting min(n) shots only"
        )
    os.makedirs(work_dir, exist_ok=True)
    mp3 = os.path.join(work_dir, f"{voice_stem}.mp3")
    # Regenerate beat wavs when missing (or always refresh for accurate timing).
    generate_voiceover(
        script_beats=script_beats,
        output_mp3=mp3,
        voice=voice,
        rate=voice_rate,
        pitch=voice_pitch,
        work_dir=work_dir,
    )
    targets = beat_shot_durations_s(
        script_beats,
        work_dir,
        voice_stem,
        vo_delay_ms=vo_delay_ms,
        default_rate=voice_rate,
        default_pitch=voice_pitch,
    )
    n = min(len(shot_paths), len(targets))
    fade = max(0.0, float(crossfade_s or 0.0))
    fitted = []
    for i in range(n):
        target = targets[i]
        if fade > 0 and i < n - 1:
            target += fade
        dst = os.path.join(work_dir, f"{voice_stem}_fit_shot_{i+1}.mp4")
        fit_clip_duration(shot_paths[i], dst, target)
        fitted.append(dst)
        print(f"   shot {i+1}: target {target:.2f}s → {dst}")
    if len(shot_paths) > n:
        fitted.extend(shot_paths[n:])
    return fitted


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


def _probe_has_audio(path: str) -> bool:
    """True if the file has at least one audio stream."""
    try:
        out = subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a",
                "-show_entries",
                "stream=index",
                "-of",
                "csv=p=0",
                path,
            ],
            text=True,
        ).strip()
        return bool(out)
    except Exception:
        return False


def parse_ambient_option(ambient: Union[bool, str, None] = DEFAULT_AMBIENT) -> Optional[str]:
    """
    Normalize ambient field.

    Returns None (off), a preset name ("rain" / "rain_city" / "space"),
    AMBIENT_LTX ("ltx"), or an absolute file path.
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
        if low in (AMBIENT_LTX, "native", "keep_ltx", "ltx_native"):
            return AMBIENT_LTX
        if low in AMBIENT_PRESETS:
            return low
        candidates = [
            key,
            os.path.abspath(key),
            os.path.join(os.path.dirname(__file__), key),
            os.path.join(os.path.dirname(__file__), "ambient", os.path.basename(key)),
        ]
        for path in candidates:
            if os.path.isfile(path):
                return os.path.abspath(path)
        print(
            f"⚠️ ambient '{ambient}' not found; using rain_city. "
            f"Presets: {', '.join(AMBIENT_PRESETS)}, ltx"
        )
        return DEFAULT_AMBIENT
    return DEFAULT_AMBIENT


def extract_video_audio(
    video_path: str,
    output_wav: str,
    volume: float = 1.0,
) -> str:
    """Extract audio stream from MP4 to WAV, optionally scaled."""
    vol = max(0.0, min(2.0, float(volume)))
    af = f"volume={vol:.3f}" if abs(vol - 1.0) > 1e-3 else "anull"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vn",
        "-af",
        af,
        "-ac",
        "2",
        "-ar",
        "48000",
        output_wav,
    ]
    print(f"🔊 Extract LTX/native audio (vol={vol:.2f}) → {output_wav}")
    subprocess.run(cmd, check=True, capture_output=True)
    if not os.path.isfile(output_wav) or os.path.getsize(output_wav) < 100:
        raise RuntimeError(f"Failed to extract audio from {video_path}")
    return output_wav


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
    space     — deep low hum + faint static (Threshold Physics VO bed)
    """
    if duration_s <= 0.2:
        raise ValueError(f"duration too short for ambient: {duration_s}")
    os.makedirs(os.path.dirname(os.path.abspath(output_wav)) or ".", exist_ok=True)
    dur = f"{duration_s:.3f}"
    vol = max(0.05, min(1.0, float(volume)))

    if preset == "space":
        static_v = vol * 0.35
        hum_v = vol * 0.55
        fade_out_st = max(0.0, duration_s - 0.5)
        filter = (
            f"[0:a]highpass=f=800,lowpass=f=14000,volume={static_v:.3f}[st];"
            f"[1:a]lowpass=f=90,volume={hum_v:.3f}[hum];"
            f"[st][hum]amix=inputs=2:duration=longest:dropout_transition=0,"
            f"afade=t=in:st=0:d=0.35,afade=t=out:st={fade_out_st:.3f}:d=0.5[out]"
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"anoisesrc=color=violet:amplitude=0.12:duration={dur}",
            "-f",
            "lavfi",
            "-i",
            f"anoisesrc=color=brown:amplitude=0.35:duration={dur}",
            "-filter_complex",
            filter,
            "-map",
            "[out]",
            output_wav,
        ]
    elif preset == "rain":
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

    icon = "🌌" if preset == "space" else "🌧️"
    print(f"{icon} Ambient bed ({preset}, {duration_s:.1f}s, vol={vol:.2f}) → {output_wav}")
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
    vo_vol = max(0.1, min(1.5, float(voice_volume)))
    # normalize=0 keeps ambient loud after VO ends (default amix halves levels
    # while the padded silent VO track is still "present").
    filter = (
        f"[1:a]volume={vo_vol:.3f},adelay={delay}|{delay},"
        f"apad=whole_dur={video_duration_s:.3f}[vo];"
        f"[0:a][vo]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
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
    script: Optional[str] = None,
    output_path: str = "",
    work_dir: Optional[str] = None,
    voice: Optional[str] = None,
    burn_captions: bool = False,
    caption_style: Optional[str] = None,
    ambient: Union[bool, str, None] = DEFAULT_AMBIENT,
    vo_delay_ms: int = DEFAULT_VO_DELAY_MS,
    ambient_volume: float = DEFAULT_AMBIENT_VOLUME,
    voice_volume: float = 1.0,
    voice_rate: Optional[str] = None,
    voice_pitch: Optional[str] = None,
    script_beats: Optional[list] = None,
) -> str:
    """Full post pipeline: TTS (optional beats) → ambient bed → Whisper SRT → mux."""
    if not output_path:
        raise ValueError("output_path is required")
    if not script_beats and (not script or not str(script).strip()):
        raise ValueError("script or script_beats is required for voiceover")
    if not os.path.isfile(silent_video_path):
        raise FileNotFoundError(silent_video_path)

    work_dir = work_dir or os.path.join(os.path.dirname(output_path) or ".", "audio_work")
    os.makedirs(work_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(output_path))[0]
    mp3 = os.path.join(work_dir, f"{stem}_voice.mp3")
    mixed = os.path.join(work_dir, f"{stem}_mix.wav")
    srt = os.path.join(work_dir, f"{stem}_captions.srt")

    generate_voiceover(
        script=script,
        output_mp3=mp3,
        voice=voice,
        rate=voice_rate,
        pitch=voice_pitch,
        script_beats=script_beats,
        work_dir=work_dir,
    )
    if burn_captions:
        used_beats = False
        if script_beats:
            try:
                create_subtitles_from_beats(
                    script_beats,
                    work_dir=work_dir,
                    stem=f"{stem}_voice",
                    srt_path=srt,
                    default_rate=voice_rate,
                    default_pitch=voice_pitch,
                )
                used_beats = True
            except Exception as e:
                print(f"⚠️ Beat captions failed ({e}); falling back to Whisper")
        if not used_beats:
            create_subtitles(mp3, srt)
    else:
        print("📝 Captions off — voice only")
        srt = ""

    video_dur = _probe_duration(silent_video_path)
    ambient_key = parse_ambient_option(ambient)
    final_audio = mp3

    if ambient_key == AMBIENT_LTX:
        if not _probe_has_audio(silent_video_path):
            raise RuntimeError(
                "ambient=ltx requested but video has no audio stream "
                "(re-render with LTX native AV, or set ambient=space)"
            )
        bed = os.path.join(work_dir, f"{stem}_ltx_bed.wav")
        extract_video_audio(silent_video_path, bed, volume=ambient_volume)
        mix_voice_with_ambient(
            mp3,
            bed,
            mixed,
            video_duration_s=video_dur,
            vo_delay_ms=vo_delay_ms,
            voice_volume=voice_volume,
        )
        final_audio = mixed
        if burn_captions and srt and vo_delay_ms:
            shift_srt_file(srt, int(vo_delay_ms))
        print("🔊 Keeping LTX native AV under VO")
    elif ambient_key:
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
            voice_volume=voice_volume,
        )
        final_audio = mixed
        # Whisper/beat captions timed at VO t=0; mix delays VO — shift to match.
        if burn_captions and srt and vo_delay_ms:
            shift_srt_file(srt, int(vo_delay_ms))
    else:
        print("🌧️ Ambient off — VO only (weak Shorts hook)")

    if burn_captions and srt:
        clamp_srt_file(srt, video_dur)

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
        # Keep source audio when present (LTX native AV); otherwise silent.
        has_audio = _probe_has_audio(silent_video_path)
        if has_audio:
            cmd += [
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-map",
                "0:v:0",
                "-map",
                "0:a:0",
                "-t",
                f"{video_dur:.3f}",
            ]
            print("🔊 Ambient off — keeping source audio (LTX native AV)")
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
    parser.add_argument(
        "--rate",
        default=DEFAULT_VOICE_RATE,
        help=f"Edge-TTS rate e.g. -8%% (default: {DEFAULT_VOICE_RATE})",
    )
    parser.add_argument(
        "--pitch",
        default=DEFAULT_VOICE_PITCH,
        help=f"Edge-TTS pitch e.g. -2Hz (default: {DEFAULT_VOICE_PITCH})",
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
        voice_rate=args.rate,
        voice_pitch=args.pitch,
    )
    print(f"✅ Done: {args.output}")
