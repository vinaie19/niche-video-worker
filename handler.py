import os
import time
import json
import base64
import requests
import boto3
import threading
import uuid
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
    aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
)

jobs = {}

# LTX temporal lengths: 8k+1 (up to ~40s @24fps for one-pass multishot on 96GB)
def _build_valid_frame_counts(max_frames=961):
    return {8 * k + 1 for k in range(2, (max_frames - 1) // 8 + 1)}


VALID_FRAME_COUNTS = _build_valid_frame_counts()
COMFY_HEADERS = {"Host": "127.0.0.1"}
COMFY_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = "/comfyui/output"
INPUT_DIR = "/comfyui/input"

LTX_UNET_DISTILLED = "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors"
LTX_UNET_DEV = "ltx-2.5-22b-dev-transformer-comfy-int8-convrot.safetensors"
LTX_GEMMA = "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors"
LTX_VIDEO_VAE = "ltx-2.5-video-vae-bf16.safetensors"
LTX_AUDIO_VAE = "ltx-2.5-audio-vae-bf16.safetensors"
LTX_DISTILLED_SIGMAS = "1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0"


def get_engine():
    """LTX-2.5 only. ENGINE aliases still accepted for older launchers."""
    eng = os.getenv("ENGINE", "ltx").strip().lower()
    if eng and eng not in ("ltx", "ltx2", "ltx23", "ltx25", "ltxv", "lightricks"):
        print(f"⚠️ ENGINE={eng} ignored — this image is LTX-2.5 only")
    return "ltx"


def ltx_variant():
    v = os.getenv("LTX_VARIANT", "distilled").strip().lower()
    if v in ("dev", "dev_int8", "full"):
        return "dev"
    return "distilled"


def nearest_valid_frames(n):
    if n in VALID_FRAME_COUNTS:
        return n
    return min(VALID_FRAME_COUNTS, key=lambda v: abs(v - n))


def detect_vram_gb():
    env_vram = os.getenv("GPU_VRAM_GB")
    if env_vram:
        try:
            return float(env_vram)
        except ValueError:
            pass
    try:
        import torch

        if torch.cuda.is_available():
            return torch.cuda.get_device_properties(0).total_memory / (1024**3)
    except Exception:
        pass
    return 32.0


def should_force_offload(vram_gb=None):
    flag = os.getenv("FORCE_OFFLOAD", "").lower()
    if flag in ("true", "1", "yes"):
        return True
    if flag in ("false", "0", "no"):
        return False
    if vram_gb is None:
        vram_gb = detect_vram_gb()
    return vram_gb < 64


def default_ltx_te_device(vram_gb=None):
    """CLIPLoader device: 'default' | 'cpu' (never pass 'gpu')."""
    explicit = os.getenv("LTX_TE_DEVICE", "").strip().lower()
    if explicit in ("cpu",):
        return "cpu"
    if explicit in ("default", "gpu", "cuda"):
        return "default"
    if vram_gb is None:
        vram_gb = detect_vram_gb()
    return "default" if float(vram_gb) >= 64 else "cpu"


def default_fps():
    try:
        return max(1, int(os.getenv("LTX_FPS", "24")))
    except ValueError:
        return 24


def default_num_frames():
    try:
        requested = int(os.getenv("LTX_NUM_FRAMES", "97"))
    except ValueError:
        requested = 97
    return nearest_valid_frames(requested)


def default_steps():
    try:
        return max(1, int(os.getenv("LTX_STEPS", "8")))
    except ValueError:
        return 8


def wait_for_comfyui():
    print("⏳ Waiting for internal ComfyUI engine...")
    while True:
        try:
            res = requests.get(f"{COMFY_URL}/system_stats", timeout=2, headers=COMFY_HEADERS)
            if res.status_code == 200:
                print("✅ ComfyUI is online and operational!")
                break
        except Exception:
            time.sleep(2)


def model_search_roots():
    return ["/local_models", "/runpod-volume/models", "/runpod-volume", "/workspace/models"]


def find_model_file(subfolder, predicates, fallback_ext=(".safetensors",)):
    for vol in model_search_roots():
        path = os.path.join(vol, subfolder)
        if not os.path.isdir(path):
            continue
        files = [f for f in os.listdir(path) if f.endswith(fallback_ext)]
        matches = [f for f in files if all(p(f) for p in predicates)]
        if matches:
            return sorted(matches)[0], vol
    return None, None


def detect_ltx_models():
    """Locate LTX-2.5 split weights (UNET + Gemma4 + video/audio VAEs)."""
    variant = ltx_variant()
    want_unet = LTX_UNET_DEV if variant == "dev" else LTX_UNET_DISTILLED

    unet, uvol = find_model_file("diffusion_models", [lambda f: f == want_unet])
    if not unet:
        unet, uvol = find_model_file(
            "diffusion_models",
            [
                lambda f: "ltx" in f.lower() and "2.5" in f,
                lambda f: ("distill" in f.lower()) if variant == "distilled" else ("dev" in f.lower()),
            ],
        )

    gemma, _ = find_model_file(
        "text_encoders",
        [lambda f: f == LTX_GEMMA or ("gemma4" in f.lower() and "ltx-2.5" in f.lower())],
    )
    if not gemma:
        gemma, _ = find_model_file(
            "text_encoders",
            [lambda f: "gemma4" in f.lower() and "ltx" in f.lower()],
        )

    video_vae, _ = find_model_file(
        "vae",
        [lambda f: f == LTX_VIDEO_VAE or ("ltx-2.5" in f.lower() and "video" in f.lower() and "vae" in f.lower())],
    )
    audio_vae, _ = find_model_file(
        "vae",
        [lambda f: f == LTX_AUDIO_VAE or ("ltx-2.5" in f.lower() and "audio" in f.lower() and "vae" in f.lower())],
    )

    if unet:
        print(f"🎯 LTX UNET from {uvol}: {unet}")
    return {
        "unet": unet,
        "gemma": gemma,
        "video_vae": video_vae,
        "audio_vae": audio_vae,
        "variant": variant,
    }


def save_start_image(job_id, start_image_url=None, start_image_b64=None):
    """Download/decode an I2V first frame into /comfyui/input/. Returns the filename."""
    os.makedirs(INPUT_DIR, exist_ok=True)
    filename = f"{job_id}_start.png"
    dest = os.path.join(INPUT_DIR, filename)
    if start_image_url:
        res = requests.get(start_image_url, timeout=60)
        res.raise_for_status()
        with open(dest, "wb") as f:
            f.write(res.content)
    elif start_image_b64:
        raw = start_image_b64
        if raw.startswith("data:"):
            raw = raw.split(",", 1)[1]
        with open(dest, "wb") as f:
            f.write(base64.b64decode(raw))
    else:
        raise ValueError("save_start_image requires start_image_url or start_image_b64")
    print(f"🖼️ Saved I2V start frame → {dest}")
    return filename


def patch_ltx_workflow(workflow, prompt_text, models, num_frames=None, steps=None, start_image_filename=None, negative_prompt=None):
    """Patch LTX-2.5 single-stage distilled AV T2V/I2V for vertical Shorts (~1088×1920)."""
    if num_frames is None:
        num_frames = default_num_frames()
    else:
        num_frames = nearest_valid_frames(int(num_frames))
    if steps is None:
        steps = default_steps()
    else:
        steps = max(1, int(steps))

    # 1080 is not divisible by 32 — use 1088 then ffmpeg to exact Shorts size
    width = int(os.getenv("LTX_WIDTH", "1088"))
    height = int(os.getenv("LTX_HEIGHT", "1920"))
    video_cfg = float(os.getenv("LTX_CFG", os.getenv("LTX_VIDEO_CFG", "1")))
    audio_cfg = float(os.getenv("LTX_AUDIO_CFG", str(video_cfg)))
    fps = default_fps()
    sigmas = os.getenv("LTX_SIGMAS", LTX_DISTILLED_SIGMAS).strip()
    unet = models.get("unet")
    gemma = models.get("gemma")
    video_vae = models.get("video_vae")
    audio_vae = models.get("audio_vae")
    te_device = default_ltx_te_device()

    default_negative = "pc game, console game, video game, cartoon, childish, ugly, blurry, low quality, worst quality, deformed, text, watermark, logo, people, faces, humans"

    for node in workflow.values():
        class_type = node.get("class_type")
        title = (node.get("_meta") or {}).get("title", "")

        if class_type == "CLIPLoader":
            if gemma:
                node["inputs"]["clip_name"] = gemma
            node["inputs"]["type"] = "ltxv"
            node["inputs"]["device"] = te_device

        if class_type == "UNETLoader" and unet:
            node["inputs"]["unet_name"] = unet

        if class_type == "VAELoader":
            name = (node["inputs"].get("vae_name") or "").lower()
            if "audio" in name or "Audio" in title:
                if audio_vae:
                    node["inputs"]["vae_name"] = audio_vae
            else:
                if video_vae:
                    node["inputs"]["vae_name"] = video_vae

        if class_type == "CLIPTextEncode" and (
            title == "Positive Prompt" or "Positive" in title
        ):
            node["inputs"]["text"] = prompt_text

        if class_type == "CLIPTextEncode" and (
            title == "Negative Prompt" or "Negative" in title
        ):
            node["inputs"]["text"] = negative_prompt or default_negative

        if class_type == "EmptyLTXVLatentVideo":
            node["inputs"]["width"] = width
            node["inputs"]["height"] = height
            node["inputs"]["length"] = num_frames

        if class_type == "LTXVEmptyLatentAudio":
            node["inputs"]["frames_number"] = num_frames
            node["inputs"]["frame_rate"] = fps

        if class_type == "LTXVConditioning":
            node["inputs"]["frame_rate"] = fps

        if class_type == "LTXVDualCFGGuider":
            node["inputs"]["video_cfg"] = video_cfg
            node["inputs"]["audio_cfg"] = audio_cfg

        if class_type == "ManualSigmas":
            node["inputs"]["sigmas"] = sigmas

        if class_type == "CreateVideo":
            node["inputs"]["fps"] = fps

        if class_type == "LoadImage" and start_image_filename:
            node["inputs"]["image"] = start_image_filename

    print(
        f"🎚️ LTX-2.5 patch | {width}x{height} | frames={num_frames} "
        f"(~{num_frames / fps:.1f}s @{fps}fps) | distilled_sigmas | "
        f"video_cfg={video_cfg} audio_cfg={audio_cfg} | variant={models.get('variant')} | TE={te_device}"
    )
    return workflow


def should_unload_models_between_jobs():
    flag = os.getenv("KEEP_MODELS_LOADED", "").strip().lower()
    if flag in ("true", "1", "yes"):
        return False
    if flag in ("false", "0", "no"):
        return True
    return False  # LTX: keep resident by default


def free_comfy_memory(force=False):
    if not force and not should_unload_models_between_jobs():
        print("🧠 Keeping models loaded (skip /free between shots)")
        return
    try:
        requests.post(
            f"{COMFY_URL}/free",
            json={"unload_models": True, "free_memory": True},
            headers=COMFY_HEADERS,
            timeout=30,
        )
        print("🧹 ComfyUI /free — unloaded models + freed memory")
        time.sleep(3)
    except Exception as e:
        print(f"⚠️ ComfyUI /free failed: {e}")


def _is_oom_error(err) -> bool:
    text = str(err).lower()
    return any(
        needle in text
        for needle in (
            "outofmemory",
            "out of memory",
            "allocation on device",
            "cuda out of memory",
            "torch.outofmemoryerror",
            "cudamalloc",
        )
    )


def submit_and_wait(workflow, timeout_s=1800, oom_retries=1):
    try:
        requests.post(f"{COMFY_URL}/refresh_custom_nodes", headers=COMFY_HEADERS, timeout=2)
    except Exception:
        pass

    attempts = 1 + max(0, int(oom_retries))
    last_err = None

    for attempt in range(1, attempts + 1):
        res_raw = requests.post(
            f"{COMFY_URL}/prompt",
            json={"prompt": workflow},
            headers=COMFY_HEADERS,
            timeout=60,
        )
        if res_raw.status_code != 200:
            raise RuntimeError(f"ComfyUI Validation Error: {res_raw.text}")

        prompt_id = res_raw.json()["prompt_id"]
        start_poll = time.time()
        try:
            while True:
                if time.time() - start_poll > timeout_s:
                    raise TimeoutError(f"Generation timed out after {timeout_s}s")

                time.sleep(5)
                try:
                    hist_res = requests.get(
                        f"{COMFY_URL}/history/{prompt_id}",
                        headers=COMFY_HEADERS,
                        timeout=5,
                    )
                    history = hist_res.json()
                    if prompt_id not in history:
                        continue

                    status = history[prompt_id].get("status", {})
                    for msg in status.get("messages", []):
                        if msg[0] == "execution_error":
                            raise RuntimeError(f"ComfyUI Execution Error: {msg[1]}")

                    outputs = history[prompt_id].get("outputs", {})
                    for node_output in outputs.values():
                        for key in ("gifs", "videos", "images"):
                            if key in node_output and node_output[key]:
                                filename = node_output[key][0].get("filename")
                                if filename and filename.lower().endswith(
                                    (".mp4", ".webm", ".gif", ".mkv")
                                ):
                                    free_comfy_memory(force=False)
                                    return filename
                        for key, val in node_output.items():
                            if not isinstance(val, list) or not val:
                                continue
                            first = val[0]
                            if isinstance(first, dict):
                                filename = first.get("filename")
                                if filename and filename.lower().endswith(
                                    (".mp4", ".webm", ".mkv")
                                ):
                                    free_comfy_memory(force=False)
                                    return filename

                    if os.path.isdir(OUTPUT_DIR):
                        candidates = [
                            f
                            for f in os.listdir(OUTPUT_DIR)
                            if f.lower().endswith((".mp4", ".webm", ".mkv"))
                        ]
                        if candidates:
                            newest = max(
                                candidates,
                                key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)),
                            )
                            if os.path.getmtime(os.path.join(OUTPUT_DIR, newest)) >= start_poll - 2:
                                free_comfy_memory(force=False)
                                return newest
                except (TimeoutError, RuntimeError):
                    raise
                except Exception as e:
                    print(f"⚠️ Polling error: {e}")
        except RuntimeError as e:
            last_err = e
            if _is_oom_error(e) and attempt < attempts:
                print(
                    f"💥 OOM on attempt {attempt}/{attempts} — freeing VRAM and retrying..."
                )
                free_comfy_memory(force=True)
                continue
            if _is_oom_error(e):
                free_comfy_memory(force=True)
            raise

    raise last_err or RuntimeError("ComfyUI submit failed with no output")


def maybe_scale_to_shorts(src_path, dst_path, copy_audio=True):
    """Scale/crop 1088×1920 (or other) → exact 1080×1920 Shorts delivery."""
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        src_path,
        "-vf",
        "scale=1080:1920:flags=lanczos",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "18",
    ]
    if copy_audio:
        cmd.extend(["-c:a", "aac", "-b:a", "192k", "-map", "0:v:0", "-map", "0:a:0?"])
    else:
        cmd.extend(["-an"])
    cmd.append(dst_path)
    subprocess.run(cmd, check=True, capture_output=True)


def upload_to_r2(local_file_path, r2_key):
    print(
        f"☁️ Uploading {os.path.basename(local_file_path)} to Cloudflare R2... "
        f"(Size: {os.path.getsize(local_file_path)} bytes)"
    )
    s3.upload_file(local_file_path, os.getenv("R2_BUCKET_NAME"), r2_key)
    return f"{os.getenv('R2_PUBLIC_URL_PREFIX')}/{r2_key}"


def execute_multi_cut(
    job_id,
    prompt_text,
    video_id,
    shot_index,
    num_frames=None,
    steps=None,
    start_image_url=None,
    start_image_b64=None,
    negative_prompt=None,
):
    """LTX-2.5 native AV T2V (or I2V, when a start image is given) at ~1088×1920,
    then deliver exact 1080×1920."""
    is_i2v = bool(start_image_url or start_image_b64)
    workflow_path = (
        "/workspace/workflow_ltx_i2v.json" if is_i2v else "/workspace/workflow_ltx_t2v.json"
    )
    with open(workflow_path, "r") as f:
        workflow = json.load(f)

    start_image_filename = None
    if is_i2v:
        start_image_filename = save_start_image(
            job_id, start_image_url=start_image_url, start_image_b64=start_image_b64
        )

    models = detect_ltx_models()
    if not models.get("unet"):
        raise RuntimeError(
            "LTX-2.5 UNET not found — set ENGINE=ltx and check setup.py download"
        )
    if not models.get("gemma"):
        raise RuntimeError("LTX-2.5 Gemma4 text encoder not found")
    if not models.get("video_vae") or not models.get("audio_vae"):
        raise RuntimeError("LTX-2.5 video/audio VAEs not found")

    vram_gb = detect_vram_gb()
    te_device = default_ltx_te_device(vram_gb)
    print(
        f"🖥️ LTX-2.5 | variant={models['variant']} | VRAM≈{vram_gb:.0f}GB | "
        f"TE={te_device} | native AV @1088x1920 | force_offload={should_force_offload(vram_gb)}"
    )

    workflow = patch_ltx_workflow(
        workflow,
        prompt_text,
        models,
        num_frames=num_frames,
        steps=steps,
        start_image_filename=start_image_filename,
        negative_prompt=negative_prompt,
    )
    output_filename = submit_and_wait(workflow, timeout_s=2400)
    local_file_path = os.path.join(OUTPUT_DIR, output_filename)

    scaled_path = os.path.join(OUTPUT_DIR, f"ltx_{job_id}_1080p.mp4")
    try:
        maybe_scale_to_shorts(local_file_path, scaled_path, copy_audio=True)
        upload_path = scaled_path
    except Exception as e:
        print(f"⚠️ LTX 1080p scale failed ({e}); uploading native resolution")
        upload_path = local_file_path

    r2_key = f"renders/{video_id}/shot_{shot_index}.mp4"
    r2_public_url = upload_to_r2(upload_path, r2_key)
    for path in (local_file_path, scaled_path):
        if os.path.exists(path):
            os.remove(path)

    jobs[job_id]["status"] = "completed"
    jobs[job_id]["output_r2_url"] = r2_public_url
    # Preserve caller shot_mode (multi_cut vs ltx_multishot / continuous).
    if not jobs[job_id].get("shot_mode"):
        jobs[job_id]["shot_mode"] = "multi_cut"
    jobs[job_id]["engine"] = "ltx"


def execute_render_async(
    job_id,
    prompt_text,
    video_id,
    shot_index,
    shot_mode="multi_cut",
    chunks=2,
    upscale=True,
    num_frames=None,
    steps=None,
    join_style=None,
    start_image_url=None,
    start_image_b64=None,
    negative_prompt=None,
):
    try:
        jobs[job_id]["status"] = "processing"
        mode = (shot_mode or "multi_cut").lower().strip()
        # multi_cut = independent short clips (caller stitches; audio jumps).
        # ltx_multishot / continuous / cut / continue = one native AV pass
        # (caller sends a combined chronological prompt + total frames).
        if mode not in (
            "multi_cut",
            "ltx_multishot",
            "continuous",
            "cut",
            "continue",
            "single_shot",
            "singleshot",
        ):
            raise RuntimeError(f"Unknown shot_mode={shot_mode!r}")
        print(
            f"🎬 LTX render mode={mode} join_style={join_style or '-'} "
            f"frames={num_frames} shot_index={shot_index}"
        )
        execute_multi_cut(
            job_id,
            prompt_text,
            video_id,
            shot_index,
            num_frames=num_frames,
            steps=steps,
            start_image_url=start_image_url,
            start_image_b64=start_image_b64,
            negative_prompt=negative_prompt,
        )
        jobs[job_id]["shot_mode"] = mode
        if join_style:
            jobs[job_id]["join_style"] = join_style
    except Exception as e:
        import traceback

        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"💥 Execution Error: {error_msg}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = error_msg


@app.route("/", methods=["GET"])
def index():
    return jsonify({"service": "niche-video-worker", "status": "online", "engine": "ltx"})


@app.route("/health", methods=["GET"])
def health_check():
    diag = {}
    for p in [
        "/local_models",
        "/runpod-volume",
        "/workspace/models",
        "/comfyui/models/diffusion_models",
        "/comfyui/models/text_encoders",
        "/comfyui/models/vae",
    ]:
        if os.path.exists(p):
            diag[p] = {"exists": True, "files": os.listdir(p)[:12]}
        else:
            diag[p] = {"exists": False}

    setup_log = ""
    if os.path.exists("/workspace/setup.log"):
        with open("/workspace/setup.log", "r") as f:
            setup_log = f.read()

    return jsonify(
        {
            "status": "ready",
            "engine": "ltx",
            "ltx_version": "2.5",
            "ltx_variant": ltx_variant(),
            "diagnostics": diag,
            "setup_log": setup_log,
            "vram_gb": detect_vram_gb(),
            "force_offload": should_force_offload(),
            "num_frames": default_num_frames(),
            "steps": default_steps(),
            "fps": default_fps(),
            "width": int(os.getenv("LTX_WIDTH", "1088")),
            "height": int(os.getenv("LTX_HEIGHT", "1920")),
            "modes": [
                "multi_cut",
                "ltx_multishot",
                "continuous",
                "cut",
                "continue",
            ],
            "join_styles": ["cut", "continue"],
            "i2v": True,
        }
    )


@app.route("/render", methods=["POST"])
@app.route("/prompt", methods=["POST"])
def handle_prompt():
    data = request.json or {}
    job_id = str(uuid.uuid4())
    shot_mode = data.get("shot_mode", "multi_cut")
    join_style = data.get("join_style")
    chunks = int(data.get("chunks", 2))
    upscale = bool(data.get("upscale", True))
    num_frames = data.get("num_frames")
    steps = data.get("steps")
    if num_frames is not None:
        num_frames = int(num_frames)
    if steps is not None:
        steps = int(steps)
    start_image_url = data.get("start_image_url")
    start_image_b64 = data.get("start_image_b64")
    negative_prompt = data.get("negative_prompt")

    jobs[job_id] = {
        "status": "queued",
        "video_id": data.get("video_id"),
        "shot_index": data.get("shot_index"),
        "shot_mode": shot_mode,
        "join_style": join_style,
        "chunks": chunks,
        "num_frames": num_frames,
        "steps": steps,
        "i2v": bool(start_image_url or start_image_b64),
        "created_at": time.time(),
    }

    def _start():
        time.sleep(0.3)
        execute_render_async(
            job_id,
            data.get("prompt"),
            data.get("video_id"),
            data.get("shot_index"),
            shot_mode,
            chunks,
            upscale,
            num_frames,
            steps,
            join_style,
            start_image_url,
            start_image_b64,
            negative_prompt,
        )

    threading.Thread(target=_start, daemon=True).start()

    return jsonify(
        {
            "job_id": job_id,
            "status": "queued",
            "engine": "ltx",
            "shot_mode": shot_mode,
            "join_style": join_style,
            "chunks": chunks,
            "num_frames": num_frames,
            "steps": steps,
            "i2v": bool(start_image_url or start_image_b64),
        }
    )


@app.route("/status/<job_id>", methods=["GET"])
def get_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


if __name__ == "__main__":
    wait_for_comfyui()
    app.run(host="0.0.0.0", port=8000, threaded=True)
