import os
import time
import json
import requests
import boto3
import shutil
import threading
import uuid
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

# Cloudflare R2 Client Init
s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
    aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
)

jobs = {}

# Wan / HunyuanVideo 1.5 both use temporal length 4k+1 (e.g. 17, 33, 49, 65, 81)
# 4k+1 temporal lengths (Wan + HunyuanVideo 1.5). Include 73 ≈ 3.0s @ 24fps.
VALID_FRAME_COUNTS = {17, 33, 49, 65, 73, 81, 97, 113, 121, 129}
COMFY_HEADERS = {"Host": "127.0.0.1"}
COMFY_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = "/comfyui/output"
INPUT_DIR = "/comfyui/input"
WORK_DIR = "/workspace/continuous_work"

HY_T2V_480 = "hunyuanvideo1.5_480p_t2v_cfg_distilled_fp8_scaled.safetensors"
HY_T2V_720 = "hunyuanvideo1.5_720p_t2v_fp16.safetensors"
HY_QWEN = "qwen_2.5_vl_7b_fp8_scaled.safetensors"
HY_BYT5 = "byt5_small_glyphxl_fp16.safetensors"
HY_VAE = "hunyuanvideo15_vae_fp16.safetensors"

LTX_CKPT_DISTILLED = "ltx-2.3-22b-distilled-fp8.safetensors"
LTX_CKPT_DEV = "ltx-2.3-22b-dev-fp8.safetensors"
LTX_GEMMA = "gemma_3_12B_it_fp4_mixed.safetensors"
# Official single-stage distilled ManualSigmas (8 steps between endpoints)
LTX_DISTILLED_SIGMAS = "1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0"


def get_engine():
    """wan (default) | hunyuan | ltx — set ENGINE on the pod."""
    eng = os.getenv("ENGINE", "wan").strip().lower()
    if eng in ("hunyuan", "hy", "hunyuanvideo", "hunyuan_video", "hunyuan15"):
        return "hunyuan"
    if eng in ("ltx", "ltx2", "ltx23", "ltxv", "lightricks"):
        return "ltx"
    return "wan"


def hy_variant():
    v = os.getenv("HY_VARIANT", "480p_distilled").strip().lower()
    if v in ("720p", "720", "720p_fp16"):
        return "720p"
    return "480p_distilled"


def ltx_variant():
    v = os.getenv("LTX_VARIANT", "distilled").strip().lower()
    if v in ("dev", "dev_fp8", "full"):
        return "dev"
    return "distilled"


def sageattn_available():
    """Only enable sageattn when the package imports cleanly on this runtime."""
    try:
        import sageattention  # noqa: F401

        print("✅ SageAttention import OK — will use attention_mode=sageattn")
        return True
    except Exception as e:
        print(f"ℹ️ SageAttention unavailable ({e}); defaulting to sdpa")
        return False


def nearest_valid_frames(n):
    """Clamp/snap frame counts to 4k+1 rule (Wan + HunyuanVideo 1.5)."""
    if n in VALID_FRAME_COUNTS:
        return n
    return min(VALID_FRAME_COUNTS, key=lambda v: abs(v - n))


def detect_vram_gb():
    """Prefer env from launcher; fall back to live CUDA query."""
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
    """96GB (RTX PRO 6000): keep resident. 32GB: offload required for MoE."""
    flag = os.getenv("FORCE_OFFLOAD", "").lower()
    if flag in ("true", "1", "yes"):
        return True
    if flag in ("false", "0", "no"):
        return False
    if vram_gb is None:
        vram_gb = detect_vram_gb()
    return vram_gb < 64


def default_fps():
    engine = get_engine()
    if engine == "hunyuan":
        try:
            return max(1, int(os.getenv("HY_FPS", "24")))
        except ValueError:
            return 24
    if engine == "ltx":
        try:
            return max(1, int(os.getenv("LTX_FPS", "24")))
        except ValueError:
            return 24
    return 16


def default_num_frames():
    """Wan: 49 @ 16fps ≈ 3.1s. Hunyuan/LTX: 97 @ 24fps ≈ 4.0s (override with *_NUM_FRAMES)."""
    engine = get_engine()
    if engine == "hunyuan":
        env_key, fallback = "HY_NUM_FRAMES", "49"
    elif engine == "ltx":
        env_key, fallback = "LTX_NUM_FRAMES", "97"
    else:
        env_key, fallback = "WAN_NUM_FRAMES", "49"
    try:
        requested = int(os.getenv(env_key, fallback))
    except ValueError:
        requested = int(fallback)
    return nearest_valid_frames(requested)


def default_steps():
    engine = get_engine()
    if engine == "hunyuan":
        env_key, fallback, soft = "HY_STEPS", "30", 30
    elif engine == "ltx":
        # Distilled ManualSigmas schedule is fixed (~8); steps env is informational / future use
        env_key, fallback, soft = "LTX_STEPS", "8", 8
    else:
        env_key, fallback, soft = "WAN_STEPS", "16", 16
    try:
        return max(1, int(os.getenv(env_key, fallback)))
    except ValueError:
        return soft


def wait_for_comfyui():
    """Polls internal ComfyUI instance until active."""
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


def detect_models(prefer_i2v=False):
    """Auto-detect Wan 2.2 MoE high/low + T5/VAE/CLIP/UltraSharp on volume/SSD."""
    kind = "i2v" if prefer_i2v else "t2v"

    def _find_expert(noise_tag):
        model, vol = find_model_file(
            "diffusion_models",
            [
                lambda f: "2.2" in f.lower() or "2_2" in f.lower() or "wan2.2" in f.lower(),
                lambda f: kind in f.lower(),
                lambda f: noise_tag in f.lower(),
                lambda f: "fp8" in f.lower(),
            ],
        )
        if model:
            return model, vol
        # Filename variants: high_noise / HIGH
        alt = "high" if noise_tag == "high_noise" else "low"
        return find_model_file(
            "diffusion_models",
            [
                lambda f: kind in f.lower(),
                lambda f: alt in f.lower() and "noise" in f.lower(),
                lambda f: "fp8" in f.lower(),
            ],
        )

    high, hvol = _find_expert("high_noise")
    low, lvol = _find_expert("low_noise")

    text_encoder, _ = find_model_file(
        "text_encoders",
        [lambda f: "umt5" in f.lower()],
    )
    vae, _ = find_model_file(
        "vae",
        [lambda f: "vae" in f.lower()],
    )
    clip_vision, _ = find_model_file(
        "clip_vision",
        [lambda f: f.lower() == "clip_vision_h.safetensors"],
    )
    if not clip_vision:
        clip_vision, _ = find_model_file(
            "clip_vision",
            [
                lambda f: "clip_vision" in f.lower() or f.lower().startswith("clip_vision"),
                lambda f: "open-clip" not in f.lower(),
            ],
        )
    upscale, _ = find_model_file(
        "upscale_models",
        [lambda f: "ultrasharp" in f.lower() or f.endswith(".pth")],
        fallback_ext=(".pth", ".safetensors"),
    )

    if high:
        print(f"🎯 Wan 2.2 {kind.upper()} high-noise from {hvol}: {high}")
    if low:
        print(f"🎯 Wan 2.2 {kind.upper()} low-noise from {lvol}: {low}")

    return {
        "diffusion_high": high,
        "diffusion_low": low,
        "diffusion": high,  # backwards-compat alias
        "text_encoder": text_encoder,
        "vae": vae,
        "clip_vision": clip_vision,
        "upscale": upscale,
    }


def patch_common_workflow(
    workflow,
    prompt_text,
    models,
    use_sage,
    force_offload,
    num_frames=None,
    steps=None,
):
    """Apply prompt / MoE model / VRAM / attention patches for Wan 2.2 graphs."""
    if num_frames is None:
        num_frames = default_num_frames()
    else:
        num_frames = nearest_valid_frames(int(num_frames))
    if steps is None:
        steps = default_steps()
    else:
        steps = max(1, int(steps))

    for node in workflow.values():
        class_type = node.get("class_type")
        title = (node.get("_meta") or {}).get("title", "")

        if title == "Positive Prompt" or class_type in [
            "WanVideoTextEncode",
            "WanVideoTextEncodeCached",
        ]:
            if "positive_prompt" in node["inputs"]:
                node["inputs"]["positive_prompt"] = prompt_text
            elif "text" in node["inputs"]:
                node["inputs"]["text"] = prompt_text
            if models["text_encoder"] and "model_name" in node["inputs"]:
                node["inputs"]["model_name"] = models["text_encoder"]
            # Encode on GPU (fast). /free between jobs + MoE offload frees VRAM after.
            if "quantization" in node["inputs"]:
                node["inputs"]["quantization"] = (
                    "fp8_e4m3fn" if force_offload else "disabled"
                )
            if "device" in node["inputs"]:
                node["inputs"]["device"] = "gpu"
            node["inputs"]["use_disk_cache"] = True

        if class_type == "WanVideoModelLoader":
            title_l = title.lower()
            if "low" in title_l and models.get("diffusion_low"):
                node["inputs"]["model"] = models["diffusion_low"]
            elif models.get("diffusion_high"):
                node["inputs"]["model"] = models["diffusion_high"]
            # Scaled FP8 Comfy-Org weights
            node["inputs"]["quantization"] = "fp8_e4m3fn_scaled"
            node["inputs"]["attention_mode"] = "sageattn" if use_sage else "sdpa"
            node["inputs"]["load_device"] = "offload_device" if force_offload else "main_device"

        if class_type in ("WanVideoEmptyEmbeds", "WanVideoImageToVideoEncode") and "num_frames" in node["inputs"]:
            node["inputs"]["num_frames"] = num_frames

        if class_type == "WanVideoSampler":
            # Scale MoE high/low boundary with step count (preserve graph ratio).
            old_steps = int(node["inputs"].get("steps") or steps)
            old_start = int(node["inputs"].get("start_step") or 0)
            old_end = node["inputs"].get("end_step", -1)
            node["inputs"]["steps"] = steps
            if old_steps > 0 and old_start > 0:
                node["inputs"]["start_step"] = max(0, int(round(old_start * steps / old_steps)))
            if old_end is not None and int(old_end) != -1 and old_steps > 0:
                node["inputs"]["end_step"] = max(
                    1, min(steps - 1, int(round(int(old_end) * steps / old_steps)))
                )
            # High-noise pass should offload before low-noise loads
            if "High Noise" in title:
                node["inputs"]["force_offload"] = True
            else:
                node["inputs"]["force_offload"] = force_offload

        if class_type == "WanVideoVAELoader" and models["vae"]:
            node["inputs"]["model_name"] = models["vae"]

        if class_type == "CLIPVisionLoader" and models["clip_vision"]:
            node["inputs"]["clip_name"] = models["clip_vision"]

        if class_type == "UpscaleModelLoader" and models["upscale"]:
            node["inputs"]["model_name"] = models["upscale"]

    print(f"🎚️ Workflow patch | frames={num_frames} (~{num_frames / 16:.1f}s) | steps={steps}")
    return workflow


def detect_hunyuan_models():
    """Locate HunyuanVideo 1.5 UNET / DualCLIP / VAE on volume or SSD cache."""
    variant = hy_variant()
    want_unet = HY_T2V_720 if variant == "720p" else HY_T2V_480

    unet, uvol = find_model_file(
        "diffusion_models",
        [lambda f: f == want_unet],
    )
    if not unet:
        # Fall back to any hunyuan t2v match for the variant
        if variant == "720p":
            unet, uvol = find_model_file(
                "diffusion_models",
                [
                    lambda f: "hunyuan" in f.lower() and "720" in f and "t2v" in f.lower(),
                ],
            )
        else:
            unet, uvol = find_model_file(
                "diffusion_models",
                [
                    lambda f: "hunyuan" in f.lower()
                    and "480" in f
                    and "t2v" in f.lower()
                    and "fp8" in f.lower(),
                ],
            )

    qwen, _ = find_model_file("text_encoders", [lambda f: f == HY_QWEN or "qwen" in f.lower()])
    byt5, _ = find_model_file("text_encoders", [lambda f: f == HY_BYT5 or "byt5" in f.lower()])
    vae, _ = find_model_file(
        "vae",
        [lambda f: f == HY_VAE or ("hunyuan" in f.lower() and "vae" in f.lower())],
    )

    if unet:
        print(f"🎯 Hunyuan UNET from {uvol}: {unet}")
    return {
        "unet": unet,
        "qwen": qwen,
        "byt5": byt5,
        "vae": vae,
        "variant": variant,
    }


def patch_hunyuan_workflow(workflow, prompt_text, models, num_frames=None, steps=None):
    """Patch native HunyuanVideo 1.5 T2V graph for vertical Shorts."""
    if num_frames is None:
        num_frames = default_num_frames()
    else:
        num_frames = nearest_valid_frames(int(num_frames))
    if steps is None:
        steps = default_steps()
    else:
        steps = max(1, int(steps))

    variant = models.get("variant") or hy_variant()
    if variant == "720p":
        width = int(os.getenv("HY_WIDTH", "720"))
        height = int(os.getenv("HY_HEIGHT", "1280"))
        cfg = float(os.getenv("HY_CFG", "6"))
        shift = float(os.getenv("HY_SHIFT", "9"))
    else:
        # 480p CFG-distilled defaults (official: cfg=1, shift=5, steps=50; we use 20 for A/B speed)
        width = int(os.getenv("HY_WIDTH", "480"))
        height = int(os.getenv("HY_HEIGHT", "832"))
        cfg = float(os.getenv("HY_CFG", "1"))
        shift = float(os.getenv("HY_SHIFT", "5"))
    fps = default_fps()

    for node in workflow.values():
        class_type = node.get("class_type")
        title = (node.get("_meta") or {}).get("title", "")

        if class_type == "DualCLIPLoader":
            if models.get("qwen"):
                node["inputs"]["clip_name1"] = models["qwen"]
            if models.get("byt5"):
                node["inputs"]["clip_name2"] = models["byt5"]
            node["inputs"]["type"] = "hunyuan_video_15"

        if class_type == "UNETLoader" and models.get("unet"):
            node["inputs"]["unet_name"] = models["unet"]

        if class_type == "VAELoader" and models.get("vae"):
            node["inputs"]["vae_name"] = models["vae"]

        if class_type == "CLIPTextEncode" and (
            title == "Positive Prompt" or "Positive" in title
        ):
            node["inputs"]["text"] = prompt_text

        if class_type == "EmptyHunyuanVideo15Latent":
            node["inputs"]["width"] = width
            node["inputs"]["height"] = height
            node["inputs"]["length"] = num_frames

        if class_type == "ModelSamplingSD3":
            node["inputs"]["shift"] = shift

        if class_type == "CFGGuider":
            node["inputs"]["cfg"] = cfg

        if class_type == "BasicScheduler":
            node["inputs"]["steps"] = steps

        if class_type == "VHS_VideoCombine":
            node["inputs"]["frame_rate"] = fps

    print(
        f"🎚️ Hunyuan patch | {width}x{height} | frames={num_frames} "
        f"(~{num_frames / fps:.1f}s @{fps}fps) | steps={steps} | cfg={cfg} | shift={shift}"
    )
    return workflow


def detect_ltx_models():
    """Locate LTX-2.3 FP8 checkpoint + Gemma encoder on volume or SSD cache."""
    variant = ltx_variant()
    want_ckpt = LTX_CKPT_DEV if variant == "dev" else LTX_CKPT_DISTILLED

    ckpt, cvol = find_model_file("checkpoints", [lambda f: f == want_ckpt])
    if not ckpt:
        ckpt, cvol = find_model_file(
            "checkpoints",
            [
                lambda f: "ltx" in f.lower()
                and "2.3" in f
                and "fp8" in f.lower()
                and (("distill" in f.lower()) if variant == "distilled" else ("dev" in f.lower())),
            ],
        )

    gemma, _ = find_model_file(
        "text_encoders",
        [lambda f: f == LTX_GEMMA or ("gemma" in f.lower() and "fp4" in f.lower())],
    )
    if not gemma:
        gemma, _ = find_model_file(
            "text_encoders",
            [lambda f: "gemma" in f.lower()],
        )

    if ckpt:
        print(f"🎯 LTX checkpoint from {cvol}: {ckpt}")
    return {
        "ckpt": ckpt,
        "gemma": gemma,
        "variant": variant,
    }


def patch_ltx_workflow(workflow, prompt_text, models, num_frames=None, steps=None):
    """Patch native LTX-2.3 single-stage distilled AV T2V for vertical Shorts."""
    if num_frames is None:
        num_frames = default_num_frames()
    else:
        num_frames = nearest_valid_frames(int(num_frames))
    # Distilled path uses fixed ManualSigmas; steps kept for logging / future BasicScheduler
    if steps is None:
        steps = default_steps()
    else:
        steps = max(1, int(steps))

    width = int(os.getenv("LTX_WIDTH", "480"))
    height = int(os.getenv("LTX_HEIGHT", "832"))
    cfg = float(os.getenv("LTX_CFG", "1"))
    fps = default_fps()
    sigmas = os.getenv("LTX_SIGMAS", LTX_DISTILLED_SIGMAS).strip()
    ckpt = models.get("ckpt")
    gemma = models.get("gemma")

    for node in workflow.values():
        class_type = node.get("class_type")
        title = (node.get("_meta") or {}).get("title", "")

        if class_type == "LTXAVTextEncoderLoader":
            if gemma:
                node["inputs"]["text_encoder"] = gemma
            if ckpt:
                node["inputs"]["ckpt_name"] = ckpt
            # Keep Gemma on CPU — with --highvram it otherwise occupies ~11GB and OOMs the 29GB ckpt on 32GB GPUs
            node["inputs"]["device"] = os.getenv("LTX_TE_DEVICE", "cpu")

        if class_type in ("CheckpointLoaderSimple", "LTXVAudioVAELoader") and ckpt:
            node["inputs"]["ckpt_name"] = ckpt

        if class_type == "CLIPTextEncode" and (
            title == "Positive Prompt" or "Positive" in title
        ):
            node["inputs"]["text"] = prompt_text

        if class_type == "EmptyLTXVLatentVideo":
            node["inputs"]["width"] = width
            node["inputs"]["height"] = height
            node["inputs"]["length"] = num_frames

        if class_type == "LTXVEmptyLatentAudio":
            node["inputs"]["frames_number"] = num_frames
            node["inputs"]["frame_rate"] = fps

        if class_type == "LTXVConditioning":
            node["inputs"]["frame_rate"] = fps

        if class_type == "CFGGuider":
            node["inputs"]["cfg"] = cfg

        if class_type == "ManualSigmas":
            node["inputs"]["sigmas"] = sigmas

        if class_type == "CreateVideo":
            node["inputs"]["fps"] = fps

    print(
        f"🎚️ LTX patch | {width}x{height} | frames={num_frames} "
        f"(~{num_frames / fps:.1f}s @{fps}fps) | distilled_sigmas | cfg={cfg} | variant={models.get('variant')}"
    )
    return workflow


def should_unload_models_between_jobs():
    """
    Wan MoE often needs /free between shots (T5 + dual experts).
    Hunyuan / LTX on 32GB+ are happier keeping weights resident —
    unload+reload costs more than it saves.
    Override with KEEP_MODELS_LOADED=true|false.
    """
    flag = os.getenv("KEEP_MODELS_LOADED", "").strip().lower()
    if flag in ("true", "1", "yes"):
        return False
    if flag in ("false", "0", "no"):
        return True
    # Default: keep loaded for Hunyuan + LTX; unload for Wan
    return get_engine() not in ("hunyuan", "ltx")


def free_comfy_memory(force=False):
    """Unload models / free GPU memory. Skip between Hunyuan shots unless force (OOM)."""
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
        # Worker applies /free async; brief pause so VRAM can settle before retry.
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


def submit_and_wait(workflow, timeout_s=1200, oom_retries=1):
    """
    Queue a ComfyUI prompt and return the first output video filename.

    After success: optionally /free (Wan default; Hunyuan keeps models loaded).
    On CUDA OOM: always /free and retry once.
    """
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
                        # SaveVideo / PreviewVideo sometimes nests under ui-style keys
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

                    # Fallback: newest video written under Comfy output dir for this prompt
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
                            # Only accept if written after we queued
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

def extract_last_frame(video_path, png_path):
    """Grab the last frame of a chunk for I2V continuation."""
    os.makedirs(os.path.dirname(png_path), exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-sseof",
            "-0.1",
            "-i",
            video_path,
            "-frames:v",
            "1",
            "-q:v",
            "2",
            png_path,
        ],
        check=True,
        capture_output=True,
    )
    if not os.path.isfile(png_path):
        raise RuntimeError(f"Failed to extract last frame from {video_path}")


def stitch_continuous_chunks(chunk_paths, output_path, fps=16):
    """Concat chunks, dropping the duplicate first frame of each continuation."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if len(chunk_paths) == 1:
        shutil.copy2(chunk_paths[0], output_path)
        return

    inputs = []
    filter_parts = []
    for i, path in enumerate(chunk_paths):
        inputs.extend(["-i", path])
        if i == 0:
            filter_parts.append(f"[{i}:v]setpts=PTS-STARTPTS[v{i}]")
        else:
            filter_parts.append(f"[{i}:v]select='gte(n\\,1)',setpts=N/{fps}/TB[v{i}]")

    concat_inputs = "".join(f"[v{i}]" for i in range(len(chunk_paths)))
    filter_parts.append(f"{concat_inputs}concat=n={len(chunk_paths)}:v=1:a=0[outv]")
    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg",
        "-y",
        *inputs,
        "-filter_complex",
        filter_complex,
        "-map",
        "[outv]",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "18",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def maybe_scale_to_shorts(src_path, dst_path, copy_audio=False):
    """Fast lanczos upscale to 1080x1920 for continuous smoke tests (no UltraSharp)."""
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


def execute_multi_cut_hunyuan(job_id, prompt_text, video_id, shot_index, num_frames=None, steps=None):
    """HunyuanVideo 1.5 native T2V (vertical Shorts). No UltraSharp in-graph — ffmpeg scale after."""
    with open("/workspace/workflow_hunyuan_t2v.json", "r") as f:
        workflow = json.load(f)

    models = detect_hunyuan_models()
    if not models.get("unet"):
        raise RuntimeError(
            "Hunyuan T2V UNET not found — set ENGINE=hunyuan and check setup.py download"
        )
    if not models.get("qwen") or not models.get("byt5"):
        raise RuntimeError("Hunyuan DualCLIP encoders (Qwen + BYT5) not found")
    if not models.get("vae"):
        raise RuntimeError("Hunyuan VAE not found")

    vram_gb = detect_vram_gb()
    print(
        f"🖥️ HunyuanVideo 1.5 | variant={models['variant']} | VRAM≈{vram_gb:.0f}GB"
    )

    workflow = patch_hunyuan_workflow(
        workflow, prompt_text, models, num_frames=num_frames, steps=steps
    )
    output_filename = submit_and_wait(workflow, timeout_s=1800)
    local_file_path = os.path.join(OUTPUT_DIR, output_filename)

    # Match Wan multi_cut delivery: 1080x1920 Shorts
    scaled_path = os.path.join(OUTPUT_DIR, f"hy_{job_id}_1080p.mp4")
    try:
        maybe_scale_to_shorts(local_file_path, scaled_path)
        upload_path = scaled_path
    except Exception as e:
        print(f"⚠️ Hunyuan 1080p scale failed ({e}); uploading native resolution")
        upload_path = local_file_path

    r2_key = f"renders/{video_id}/shot_{shot_index}.mp4"
    r2_public_url = upload_to_r2(upload_path, r2_key)
    for path in (local_file_path, scaled_path):
        if os.path.exists(path):
            os.remove(path)

    jobs[job_id]["status"] = "completed"
    jobs[job_id]["output_r2_url"] = r2_public_url
    jobs[job_id]["shot_mode"] = "multi_cut"
    jobs[job_id]["engine"] = "hunyuan"


def execute_multi_cut_ltx(job_id, prompt_text, video_id, shot_index, num_frames=None, steps=None):
    """LTX-2.3 native AV T2V (vertical Shorts). Distilled FP8 + ManualSigmas; ffmpeg scale after."""
    with open("/workspace/workflow_ltx_t2v.json", "r") as f:
        workflow = json.load(f)

    models = detect_ltx_models()
    if not models.get("ckpt"):
        raise RuntimeError(
            "LTX checkpoint not found — set ENGINE=ltx and check setup.py download"
        )
    if not models.get("gemma"):
        raise RuntimeError("LTX Gemma text encoder not found")

    vram_gb = detect_vram_gb()
    print(
        f"🖥️ LTX-2.3 | variant={models['variant']} | VRAM≈{vram_gb:.0f}GB | native AV"
    )

    workflow = patch_ltx_workflow(
        workflow, prompt_text, models, num_frames=num_frames, steps=steps
    )
    output_filename = submit_and_wait(workflow, timeout_s=1800)
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
    jobs[job_id]["shot_mode"] = "multi_cut"
    jobs[job_id]["engine"] = "ltx"


def execute_multi_cut(job_id, prompt_text, video_id, shot_index, num_frames=None, steps=None):
    """Single-clip T2V path — Wan 2.2 MoE (default), HunyuanVideo 1.5, or LTX-2.3."""
    engine = get_engine()
    if engine == "hunyuan":
        return execute_multi_cut_hunyuan(
            job_id, prompt_text, video_id, shot_index, num_frames=num_frames, steps=steps
        )
    if engine == "ltx":
        return execute_multi_cut_ltx(
            job_id, prompt_text, video_id, shot_index, num_frames=num_frames, steps=steps
        )

    with open("/workspace/workflow_api.json", "r") as f:
        workflow = json.load(f)

    models = detect_models(prefer_i2v=False)
    if not models.get("diffusion_high") or not models.get("diffusion_low"):
        raise RuntimeError("Wan 2.2 T2V high/low FP8 experts not found — check setup.py download")
    use_sage = sageattn_available()
    vram_gb = detect_vram_gb()
    force_offload = should_force_offload(vram_gb)
    print(
        f"🖥️ Wan 2.2 MoE | VRAM≈{vram_gb:.0f}GB | force_offload={force_offload} | "
        f"attention={'sageattn' if use_sage else 'sdpa'}"
    )

    workflow = patch_common_workflow(
        workflow,
        prompt_text,
        models,
        use_sage,
        force_offload,
        num_frames=num_frames,
        steps=steps,
    )
    output_filename = submit_and_wait(workflow, timeout_s=1200)
    local_file_path = os.path.join(OUTPUT_DIR, output_filename)
    r2_key = f"renders/{video_id}/shot_{shot_index}.mp4"
    r2_public_url = upload_to_r2(local_file_path, r2_key)
    if os.path.exists(local_file_path):
        os.remove(local_file_path)

    jobs[job_id]["status"] = "completed"
    jobs[job_id]["output_r2_url"] = r2_public_url
    jobs[job_id]["shot_mode"] = "multi_cut"
    jobs[job_id]["engine"] = "wan"


def execute_continuous(
    job_id, prompt_text, video_id, shot_index, chunks=2, upscale=True, num_frames=None, steps=None
):
    """
    Generate a continuous take by chaining T2V -> I2V(last frame) chunks.
    Default chunk length follows WAN_NUM_FRAMES (49 ≈ 3.1s @ 16fps).
    Hunyuan continuous/I2V chaining is not wired yet — use multi_cut for A/B.
    """
    if get_engine() in ("hunyuan", "ltx"):
        raise RuntimeError(
            f"ENGINE={get_engine()} does not support continuous mode yet — use shot_mode=multi_cut"
        )

    chunks = max(1, int(chunks))
    frames = nearest_valid_frames(int(num_frames)) if num_frames is not None else default_num_frames()
    work_dir = os.path.join(WORK_DIR, job_id)
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(INPUT_DIR, exist_ok=True)

    use_sage = sageattn_available()
    vram_gb = detect_vram_gb()
    force_offload = should_force_offload(vram_gb)
    print(
        f"🎬 Continuous mode | chunks={chunks} (~{chunks * frames / 16:.0f}s) | "
        f"VRAM≈{vram_gb:.0f}GB | force_offload={force_offload} | "
        f"attention={'sageattn' if use_sage else 'sdpa'}"
    )

    chunk_paths = []
    for i in range(chunks):
        jobs[job_id]["progress"] = f"chunk_{i + 1}/{chunks}"
        print(f"🎞️ Continuous chunk {i + 1}/{chunks}...")

        if i == 0:
            with open("/workspace/workflow_t2v_chunk.json", "r") as f:
                workflow = json.load(f)
            models = detect_models(prefer_i2v=False)
            if not models.get("diffusion_high") or not models.get("diffusion_low"):
                raise RuntimeError("Wan 2.2 T2V high/low FP8 experts not found")
            workflow = patch_common_workflow(
                workflow,
                prompt_text,
                models,
                use_sage,
                force_offload,
                num_frames=num_frames,
                steps=steps,
            )
        else:
            with open("/workspace/workflow_i2v_api.json", "r") as f:
                workflow = json.load(f)
            models = detect_models(prefer_i2v=True)
            if not models.get("diffusion_high") or not models.get("diffusion_low"):
                raise RuntimeError(
                    "Wan 2.2 I2V high/low not found — resize network volume to ~100GB "
                    "so setup.py can download the I2V MoE pair"
                )
            if not models["clip_vision"]:
                raise RuntimeError(
                    "CLIP vision model not found — required for I2V continuation"
                )

            start_name = f"cont_{job_id}_chunk{i}.png"
            start_path = os.path.join(INPUT_DIR, start_name)
            extract_last_frame(chunk_paths[-1], start_path)

            workflow = patch_common_workflow(
                workflow,
                prompt_text,
                models,
                use_sage,
                force_offload,
                num_frames=num_frames,
                steps=steps,
            )
            for node in workflow.values():
                if node.get("class_type") == "LoadImage":
                    node["inputs"]["image"] = start_name

        for node in workflow.values():
            if node.get("class_type") == "WanVideoSampler" and "seed" in node["inputs"]:
                node["inputs"]["seed"] = int(node["inputs"]["seed"]) + i

        output_filename = submit_and_wait(workflow, timeout_s=1500)
        src = os.path.join(OUTPUT_DIR, output_filename)
        dst = os.path.join(work_dir, f"chunk_{i + 1:02d}.mp4")
        shutil.move(src, dst)
        chunk_paths.append(dst)
        print(f"✅ Chunk {i + 1} saved: {dst}")

    stitched = os.path.join(work_dir, "stitched_480p.mp4")
    stitch_continuous_chunks(chunk_paths, stitched)
    print(f"🔗 Stitched continuous clip: {stitched}")

    final_path = stitched
    if upscale:
        scaled = os.path.join(work_dir, "continuous_1080p.mp4")
        maybe_scale_to_shorts(stitched, scaled)
        final_path = scaled
        print(f"⬆️ Scaled continuous clip to 1080x1920: {scaled}")

    r2_key = f"renders/{video_id}/continuous.mp4"
    r2_public_url = upload_to_r2(final_path, r2_key)

    try:
        shutil.rmtree(work_dir, ignore_errors=True)
    except Exception:
        pass

    jobs[job_id]["status"] = "completed"
    jobs[job_id]["output_r2_url"] = r2_public_url
    jobs[job_id]["shot_mode"] = "continuous"
    jobs[job_id]["chunks"] = chunks


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
):
    try:
        jobs[job_id]["status"] = "processing"
        mode = (shot_mode or "multi_cut").lower().strip()
        if mode in ("continuous", "single_shot", "singleshot"):
            execute_continuous(
                job_id,
                prompt_text,
                video_id,
                shot_index,
                chunks=chunks,
                upscale=upscale,
                num_frames=num_frames,
                steps=steps,
            )
        else:
            execute_multi_cut(
                job_id,
                prompt_text,
                video_id,
                shot_index,
                num_frames=num_frames,
                steps=steps,
            )
    except Exception as e:
        import traceback

        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"💥 Execution Error: {error_msg}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = error_msg


@app.route("/", methods=["GET"])
def index():
    return jsonify({"service": "niche-video-worker", "status": "online"})


@app.route("/health", methods=["GET"])
def health_check():
    diag = {}
    for p in [
        "/local_models",
        "/runpod-volume",
        "/workspace/models",
        "/comfyui/models/diffusion_models",
        "/comfyui/models/upscale_models",
        "/comfyui/models/clip_vision",
    ]:
        if os.path.exists(p):
            diag[p] = {"exists": True, "files": os.listdir(p)[:8]}
        else:
            diag[p] = {"exists": False}

    setup_log = ""
    if os.path.exists("/workspace/setup.log"):
        with open("/workspace/setup.log", "r") as f:
            setup_log = f.read()

    engine = get_engine()
    return jsonify(
        {
            "status": "ready",
            "engine": engine,
            "hy_variant": hy_variant() if engine == "hunyuan" else None,
            "ltx_variant": ltx_variant() if engine == "ltx" else None,
            "diagnostics": diag,
            "setup_log": setup_log,
            "vram_gb": detect_vram_gb(),
            "force_offload": should_force_offload(),
            "num_frames": default_num_frames(),
            "steps": default_steps(),
            "fps": default_fps(),
            "wan_num_frames": default_num_frames(),
            "wan_steps": default_steps(),
            "modes": ["multi_cut"]
            if engine in ("hunyuan", "ltx")
            else ["multi_cut", "continuous"],
        }
    )


@app.route("/render", methods=["POST"])
@app.route("/prompt", methods=["POST"])
def handle_prompt():
    data = request.json or {}
    job_id = str(uuid.uuid4())
    shot_mode = data.get("shot_mode", "multi_cut")
    chunks = int(data.get("chunks", 2))
    upscale = bool(data.get("upscale", True))
    num_frames = data.get("num_frames")
    steps = data.get("steps")
    if num_frames is not None:
        num_frames = int(num_frames)
    if steps is not None:
        steps = int(steps)

    jobs[job_id] = {
        "status": "queued",
        "video_id": data.get("video_id"),
        "shot_index": data.get("shot_index"),
        "shot_mode": shot_mode,
        "chunks": chunks,
        "num_frames": num_frames,
        "steps": steps,
        "created_at": time.time(),
    }

    # Delay worker start so the HTTP response can leave before heavy work begins
    # (avoids RunPod proxy empty-body when the process is crushed mid-reply).
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
        )

    threading.Thread(target=_start, daemon=True).start()

    return jsonify(
        {
            "job_id": job_id,
            "status": "queued",
            "engine": get_engine(),
            "shot_mode": shot_mode,
            "chunks": chunks,
            "num_frames": num_frames,
            "steps": steps,
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
    # threaded=True so /prompt can return while a job runs (and /status stays responsive)
    app.run(host="0.0.0.0", port=8000, threaded=True)
