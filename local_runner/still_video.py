"""
Zero-GPU Shorts: build an episode from still images on the laptop (no RunPod, no paid API).

Same script, VO, captions and crossfades as the LTX path; only the picture source changes.
Each VO beat becomes one shot: a still (or a composite of layers) with a slow camera move,
optionally crossfading to an end composition (e.g. star -> black disc) and a brightness pulse.

Run:
  CHANNEL=b VIDEO_ID=sci_ep08_metallic_hydrogen python still_video.py
  VIDEO_ID=... STILL_ONLY_SHOTS=1 python still_video.py   # silent shots only, quick look

Picture source per beat (first match wins):
  1. beat["still"] dict (see below), from science_prompts.py or STILL_SPECS here
  2. i2v_stills/<video_id>/shot_N.png  (the approved I2V stills, if any)
  3. procedural starfield

beat["still"] keys (all optional):
  image        path, or "starfield"; relative paths resolve against i2v_stills/<video_id>/, then i2v_stills/
  layers       [{"image": path, "x": 0.5, "y": 0.42, "width": 0.46}]  centre x/y and width as
               fractions of frame; PNG alpha respected, or "circle": true to cut a round mask;
               {"color": "black", "width": 0.3} with no image draws a solid disc;
               width_to / x_to / y_to animate across the shot (shrink, slide);
               "brightness": 0.3 dims a layer; "glow": "orange" adds a soft halo behind it
  end          {"image": ..., "layers": [...]}  composition to crossfade into across the shot
  end_at       (start, finish) fractions of the shot for that crossfade, default (0.35, 0.75)
  move         push_in | pull_out | pan_left | pan_right | pan_up | pan_down | hold (push_in)
  zoom         move strength, default 0.10 (10% scale change / travel)
  pulse        brightness pulse amplitude 0-0.3, default 0;  pulse_hz default 0.5

Output: final_videos/<video_id>_still_complete.mp4  (never overwrites an LTX render).
Image sources: reuse approved stills, NASA/ESA/Wikimedia public-domain or CC0 photos (log them
in i2v_stills/<video_id>/SOURCES.md), or the procedural starfield.
"""

import functools
import math
import os
import random
import subprocess
import sys

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter

from audio_post import (
    _probe_duration,
    add_voice_and_captions,
    beat_shot_durations_s,
    concat_clips_crossfade,
    generate_voiceover,
    parse_captions_option,
)

HERE = os.path.dirname(os.path.abspath(__file__))
STILLS_DIR = os.path.join(HERE, "i2v_stills")
W, H, FPS = 1080, 1920, 24
# Render source at 1.25x so moves never expose an edge and sub-pixel crops stay sharp.
SRC_SCALE = 1.25
TAIL_S = float(os.getenv("STILL_TAIL_S", "2.5"))  # quiet linger after the last VO line
AMBIENT = os.getenv("STILL_AMBIENT", "space")  # stills carry no LTX audio bed
AMBIENT_VOLUME = float(os.getenv("STILL_AMBIENT_VOLUME", "0.18"))

# Per-episode still specs that live outside science_prompts.py: {video_id: [spec_beat1, ...]}.
# None for a beat means "use the default source chain".
STILL_SPECS: dict = {}


def _resolve(path, video_id):
    """Absolute/cwd path, else i2v_stills/<video_id>/path, else i2v_stills/path (other episodes)."""
    for cand in (path, os.path.join(STILLS_DIR, video_id, path), os.path.join(STILLS_DIR, path)):
        if os.path.isfile(cand):
            return cand
    raise FileNotFoundError(f"still not found: {path} (looked in i2v_stills/{video_id}/ and i2v_stills/)")


@functools.lru_cache(maxsize=8)
def _starfield_cached(w, h, seed):
    return _starfield(w, h, seed)


def starfield(w, h, seed=7):
    """Same seed -> same sky within a run, so a start/end crossfade never morphs the nebula."""
    return _starfield_cached(w, h, seed).copy()


def _starfield(w, h, seed=7):
    """Black sky, soft violet-blue nebula, scattered stars. Pure PIL, deterministic per seed."""
    rnd = random.Random(seed)
    neb = Image.new("L", (w, h), 0)
    for div, weight in ((48, 0.6), (16, 0.4)):  # two octaves: big clouds + finer texture
        layer = Image.effect_noise((max(2, w // div), max(2, h // div)), 80)
        layer = layer.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(w // div))
        neb = Image.blend(neb, layer, weight)
    neb = ImageEnhance.Contrast(neb).enhance(3.0).point(lambda v: max(0, v - 128))
    neb = neb.filter(ImageFilter.GaussianBlur(w // 60))
    img = Image.merge("RGB", (neb.point(lambda v: v * 5 // 10), neb.point(lambda v: v * 4 // 10), neb))
    d = ImageDraw.Draw(img)
    for _ in range(int(w * h / 2500)):
        x, y = rnd.randrange(w), rnd.randrange(h)
        b = rnd.choice((90, 120, 160, 200, 255))
        r = 2 if b == 255 and rnd.random() < 0.15 else 1
        d.ellipse((x - r, y - r, x + r, y + r), fill=(b, b, min(255, b + 20)))
    return img


def _cover(img, w, h):
    """Scale to cover w x h and centre-crop (like CSS background-size: cover)."""
    s = max(w / img.width, h / img.height)
    img = img.resize((max(w, round(img.width * s)), max(h, round(img.height * s))), Image.LANCZOS)
    left, top = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((left, top, left + w, top + h))


@functools.lru_cache(maxsize=16)
def _background(src, video_id, w, h, seed):
    if src == "starfield":
        return starfield(w, h, seed=seed)
    return _cover(Image.open(_resolve(src, video_id)).convert("RGB"), w, h)


@functools.lru_cache(maxsize=16)
def _layer_source(path, video_id):
    return Image.open(_resolve(path, video_id)).convert("RGBA")


def _lerp(layer, key, t, default):
    """Layer value at progress t: key interpolates toward key_to when present."""
    v0 = float(layer.get(key, default))
    return v0 + (float(layer[f"{key}_to"]) - v0) * t if f"{key}_to" in layer else v0


def is_animated(spec):
    return any(k.endswith("_to") for layer in spec.get("layers") or [] for k in layer)


def compose(spec, video_id, w, h, t=0.0):
    """Background image (or starfield) plus positioned layers -> RGB image of w x h.

    t (0-1, already eased) drives any layer width_to / x_to / y_to animation.
    """
    base = _background(spec.get("image") or "starfield", video_id, w, h, int(spec.get("seed", 7))).copy()
    for layer in spec.get("layers") or []:
        lw = max(1, round(w * _lerp(layer, "width", t, 0.4)))
        if layer.get("image"):
            im = _layer_source(layer["image"], video_id)
            im = im.resize((lw, max(1, round(im.height * lw / im.width))), Image.LANCZOS)
        else:  # solid disc, e.g. {"color": "black", "circle": true} for a black hole
            im = Image.new("RGBA", (lw, lw), layer.get("color", "black"))
            layer = {**layer, "circle": True}
        if layer.get("circle"):
            side = min(im.size)  # centre-square first so the mask is a circle, not an ellipse
            left, top = (im.width - side) // 2, (im.height - side) // 2
            im = im.crop((left, top, left + side, top + side))
            mask = Image.new("L", im.size, 0)
            ImageDraw.Draw(mask).ellipse((0, 0, im.width - 1, im.height - 1), fill=255)
            im.putalpha(ImageChops.multiply(im.getchannel("A"), mask.filter(ImageFilter.GaussianBlur(2))))
        if "brightness" in layer:
            alpha = im.getchannel("A")
            im = ImageEnhance.Brightness(im.convert("RGB")).enhance(float(layer["brightness"])).convert("RGBA")
            im.putalpha(alpha)
        cx, cy = _lerp(layer, "x", t, 0.5) * w, _lerp(layer, "y", t, 0.5) * h
        if layer.get("glow"):  # soft halo behind the layer, e.g. "orange" around a black hole
            r = im.width * 0.9
            halo = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            ImageDraw.Draw(halo).ellipse((cx - r, cy - r, cx + r, cy + r), fill=layer["glow"])
            halo = halo.filter(ImageFilter.GaussianBlur(max(2, im.width * 0.35)))
            base = Image.alpha_composite(base.convert("RGBA"), halo).convert("RGB")
        base.paste(im, (round(cx - im.width / 2), round(cy - im.height / 2)), im)
    return base


def _ease(t):
    return t * t * (3 - 2 * t)


def _crop_box(move, zoom, t, sw, sh):
    """Float crop box in source pixels for progress t in [0,1]. Source is 9:16 like the output."""
    if move in ("push_in", "pull_out"):
        k = t if move == "push_in" else 1 - t
        cw, ch = sw / (1 + zoom * k), sh / (1 + zoom * k)
        x0, y0 = (sw - cw) / 2, (sh - ch) / 2
        return (x0, y0, x0 + cw, y0 + ch)
    if move == "hold":
        return (0.0, 0.0, float(sw), float(sh))
    # Pans: fixed crop with slack on every side; travel across part of that slack.
    cw, ch = sw / (1 + max(zoom, 0.05)), sh / (1 + max(zoom, 0.05))
    sx, sy = sw - cw, sh - ch
    fx = fy = 0.5
    if move == "pan_left":
        fx = 1 - t
    elif move == "pan_right":
        fx = t
    elif move == "pan_up":
        fy = 1 - t
    elif move == "pan_down":
        fy = t
    return (sx * fx, sy * fy, sx * fx + cw, sy * fy + ch)


def render_shot(spec, video_id, duration_s, out_path):
    """Write one silent H.264 shot of duration_s from a still spec."""
    sw, sh = round(W * SRC_SCALE), round(H * SRC_SCALE)
    end_spec = spec.get("end")
    start = compose(spec, video_id, sw, sh)
    end = compose(end_spec, video_id, sw, sh) if end_spec else None
    animated = is_animated(spec) or (end_spec is not None and is_animated(end_spec))
    e0, e1 = spec.get("end_at", (0.35, 0.75))
    move, zoom = spec.get("move", "push_in"), float(spec.get("zoom", 0.10))
    pulse, pulse_hz = float(spec.get("pulse", 0.0)), float(spec.get("pulse_hz", 0.5))
    n = max(1, round(duration_s * FPS))

    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", out_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for i in range(n):
            t = i / max(1, n - 1)
            if animated:  # layers move/resize, so recompose this frame
                start = compose(spec, video_id, sw, sh, _ease(t))
                if end_spec is not None:
                    end = compose(end_spec, video_id, sw, sh, _ease(t))
            frame = start
            if end is not None:
                a = _ease(min(1.0, max(0.0, (t - e0) / max(1e-6, e1 - e0))))
                if a > 0:
                    frame = Image.blend(start, end, a)
            box = _crop_box(move, zoom, _ease(t), sw, sh)
            img = frame.resize((W, H), Image.BICUBIC, box=box)
            if pulse:
                img = ImageEnhance.Brightness(img).enhance(
                    1 + pulse * math.sin(2 * math.pi * pulse_hz * i / FPS)
                )
            proc.stdin.write(img.tobytes())
    finally:
        proc.stdin.close()
        if proc.wait() != 0:
            raise RuntimeError(f"ffmpeg failed writing {out_path}")
    return out_path


def shot_spec(beat, idx, video_id):
    """Default source chain: beat['still'] -> STILL_SPECS -> i2v_stills shot_N.png -> starfield."""
    specs = STILL_SPECS.get(video_id) or []
    spec = beat.get("still") or (specs[idx] if idx < len(specs) else None)
    if spec is None:
        still = os.path.join(STILLS_DIR, video_id, f"shot_{idx + 1}.png")
        spec = {"image": still} if os.path.isfile(still) else {"image": "starfield", "seed": idx + 1}
    return dict(spec)


def build(video_id, shots_only=False):
    from science_prompts import science_ltx_jobs

    job = next((j for j in science_ltx_jobs if j["video_id"] == video_id), None)
    if job is None or not job.get("script_beats"):
        raise SystemExit(f"No beat script for {video_id} in science_prompts.py")
    beats = job["script_beats"]
    work = os.path.join(HERE, "temp_clips", f"{video_id}_still")
    os.makedirs(work, exist_ok=True)
    out_dir = os.path.join(HERE, "final_videos")
    os.makedirs(out_dir, exist_ok=True)
    stem = f"{video_id}_still_voice"
    vo_delay_ms = int(job.get("vo_delay_ms", 100))
    fade = float(job.get("crossfade_s", 0.35))

    # Voice first, so every shot is cut to its exact beat length (no stretch/trim later).
    generate_voiceover(
        script_beats=beats, output_mp3=os.path.join(work, f"{stem}.mp3"),
        voice=job.get("voice"), rate=job.get("voice_rate"), pitch=job.get("voice_pitch"),
        work_dir=work,
    )
    targets = beat_shot_durations_s(
        beats, work, stem, vo_delay_ms=vo_delay_ms,
        default_rate=job.get("voice_rate"), default_pitch=job.get("voice_pitch"),
    )

    shot_paths = []
    for i, beat in enumerate(beats):
        dur = targets[i] + (fade if i < len(beats) - 1 else TAIL_S)
        spec = shot_spec(beat, i, video_id)
        path = os.path.join(work, f"shot_{i + 1}.mp4")
        src = spec.get("image", "starfield")
        print(f"🖼️  shot {i + 1}: {os.path.basename(str(src))} {spec.get('move', 'push_in')} {dur:.2f}s")
        render_shot(spec, video_id, dur, path)
        shot_paths.append(path)
    if shots_only:
        print(f"Shots in {work}")
        return work

    silent = os.path.join(work, f"{video_id}_still_silent.mp4")
    if len(shot_paths) > 1 and fade > 0:
        concat_clips_crossfade(shot_paths, silent, fade_s=fade)
    else:
        lst = os.path.join(work, "list.txt")
        with open(lst, "w") as f:
            f.writelines(f"file '{os.path.abspath(p)}'\n" for p in shot_paths)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                        "-i", lst, "-c", "copy", silent], check=True)

    captions_on, caption_style = parse_captions_option(job.get("captions"), job.get("caption_style"))
    output = os.path.join(out_dir, f"{video_id}_still_complete.mp4")
    add_voice_and_captions(
        silent, job.get("script"), output, work_dir=work, voice=job.get("voice"),
        burn_captions=captions_on, caption_style=caption_style,
        ambient=AMBIENT, ambient_volume=AMBIENT_VOLUME, vo_delay_ms=vo_delay_ms,
        voice_volume=float(job.get("voice_volume", 1.0)),
        voice_rate=job.get("voice_rate"), voice_pitch=job.get("voice_pitch"),
        script_beats=beats, caption_chunk_words=job.get("caption_chunk_words"),
    )
    print(f"🎉 Still video ({_probe_duration(output):.1f}s, $0 GPU): {output}")
    return output


if __name__ == "__main__":
    vid = os.getenv("VIDEO_ID") or (sys.argv[1] if len(sys.argv) > 1 else "")
    if not vid:
        raise SystemExit("Set VIDEO_ID=sci_epNN_slug (see science_prompts.py)")
    build(vid, shots_only=os.getenv("STILL_ONLY_SHOTS", "").lower() in ("1", "true", "yes"))
