import os
import shutil
import subprocess
import time

# LTX-2.5 only — single model stack for Channel A + B
ENGINE = os.getenv("ENGINE", "ltx").strip().lower()

# LTX-2.5 distilled int8 (Comfy official consumer layout) — ~39GB
LTX_BASE = "https://huggingface.co/Lightricks/LTX-2.5/resolve/main"
LTX_UNET = "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors"
LTX_UNET_URL = f"{LTX_BASE}/diffusion_models/{LTX_UNET}"
LTX_UNET_SIZE = 21_504_034_224
LTX_GEMMA = "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors"
LTX_GEMMA_URL = f"{LTX_BASE}/text_encoders/{LTX_GEMMA}"
LTX_GEMMA_SIZE = 15_372_969_374
LTX_VIDEO_VAE = "ltx-2.5-video-vae-bf16.safetensors"
LTX_VIDEO_VAE_URL = f"{LTX_BASE}/vae/{LTX_VIDEO_VAE}"
LTX_VIDEO_VAE_SIZE = 1_472_223_346
LTX_AUDIO_VAE = "ltx-2.5-audio-vae-bf16.safetensors"
LTX_AUDIO_VAE_URL = f"{LTX_BASE}/vae/{LTX_AUDIO_VAE}"
LTX_AUDIO_VAE_SIZE = 364_866_540

# Optional quality path (not downloaded by default)
LTX_DEV_UNET = "ltx-2.5-22b-dev-transformer-comfy-int8-convrot.safetensors"
LTX_DEV_UNET_URL = f"{LTX_BASE}/diffusion_models/{LTX_DEV_UNET}"
LTX_DEV_UNET_SIZE = 21_504_034_224

CACHE_DIR = "/local_models"


def _hf_wget_cmd(url, temp_path):
    """wget with optional HF_TOKEN for gated Lightricks/LTX-2.5 downloads."""
    cmd = ["wget", "--progress=dot:giga", "-O", temp_path]
    token = (
        os.getenv("HF_TOKEN")
        or os.getenv("HUGGING_FACE_HUB_TOKEN")
        or os.getenv("HUGGINGFACE_TOKEN")
        or ""
    ).strip()
    if token:
        cmd.extend(["--header", f"Authorization: Bearer {token}"])
    cmd.append(url)
    return cmd


def _ensure_volume_file(log, rel_dir, filename, url, expected_size, label, cache_ssd=True):
    """Download a model onto the network volume and optionally mirror it to SSD cache."""
    volume_root = "/runpod-volume"
    target = os.path.join(volume_root, "models", rel_dir, filename)

    if not os.path.isdir(volume_root):
        log.write(f"ℹ️ /runpod-volume is not mounted; skipping {label} setup\n")
        return

    os.makedirs(os.path.dirname(target), exist_ok=True)
    target_size = os.path.getsize(target) if os.path.isfile(target) else 0
    if target_size != expected_size:
        temp_path = f"{target}.download"
        for path in (target, temp_path):
            if os.path.isfile(path):
                os.remove(path)
        log.write(f"⬇️ Downloading {label} to volume...\n")
        log.flush()
        subprocess.run(_hf_wget_cmd(url, temp_path), check=True)
        got = os.path.getsize(temp_path)
        if got != expected_size:
            os.remove(temp_path)
            raise RuntimeError(
                f"{label} size mismatch: got {got}, expected {expected_size}. "
                "If gated, accept the LTX-2.5 license and set HF_TOKEN on the pod."
            )
        os.replace(temp_path, target)
        log.write(f"✅ {label} installed on volume\n")
    else:
        log.write(f"✅ {label} is complete on volume\n")

    if not cache_ssd:
        log.write(f"ℹ️ Skipping SSD cache for {label} (large file; volume symlink is enough)\n")
        return

    cache_path = os.path.join(CACHE_DIR, rel_dir, filename)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    if not os.path.exists(cache_path) or os.path.getsize(cache_path) != expected_size:
        log.write(f"🚀 Caching {label} to SSD...\n")
        log.flush()
        start = time.time()
        shutil.copy2(target, cache_path)
        log.write(f"⚡ {label} cached in {int(time.time() - start)}s\n")
    else:
        log.write(f"✅ {label} already cached on SSD\n")


def ltx_variant():
    """distilled (default) | dev (same int8 layout, higher quality UNET)."""
    v = os.getenv("LTX_VARIANT", "distilled").strip().lower()
    if v in ("dev", "dev_int8", "full"):
        return "dev"
    return "distilled"


def _volume_model_bytes(rel_dir="diffusion_models"):
    total = 0
    for root in (
        os.path.join("/runpod-volume/models", rel_dir),
        os.path.join("/runpod-volume", rel_dir),
    ):
        if not os.path.isdir(root):
            continue
        for name in os.listdir(root):
            path = os.path.join(root, name)
            if os.path.isfile(path):
                total += os.path.getsize(path)
    return total


def ensure_ltx_models(log):
    """Download LTX-2.5 distilled (or dev) int8 + Gemma4 TE + video/audio VAEs."""
    variant = ltx_variant()
    used_gb = _volume_model_bytes() / (1024**3)
    log.write(
        f"⚡ ENGINE=ltx | LTX_VARIANT={variant} | need ~39GB (unet+gemma4+vaes) | "
        f"volume diffusion already ~{used_gb:.1f}GB\n"
    )
    token_ok = bool(
        (
            os.getenv("HF_TOKEN")
            or os.getenv("HUGGING_FACE_HUB_TOKEN")
            or os.getenv("HUGGINGFACE_TOKEN")
            or ""
        ).strip()
    )
    if not token_ok:
        log.write(
            "⚠️ HF_TOKEN not set — gated Lightricks/LTX-2.5 downloads will fail "
            "until you accept the license and pass a token.\n"
        )

    _ensure_volume_file(
        log, "text_encoders", LTX_GEMMA, LTX_GEMMA_URL, LTX_GEMMA_SIZE,
        "LTX-2.5 Gemma4 12B int8", cache_ssd=False,
    )
    _ensure_volume_file(
        log, "vae", LTX_VIDEO_VAE, LTX_VIDEO_VAE_URL, LTX_VIDEO_VAE_SIZE,
        "LTX-2.5 video VAE", cache_ssd=True,
    )
    _ensure_volume_file(
        log, "vae", LTX_AUDIO_VAE, LTX_AUDIO_VAE_URL, LTX_AUDIO_VAE_SIZE,
        "LTX-2.5 audio VAE", cache_ssd=True,
    )
    if variant == "dev":
        _ensure_volume_file(
            log, "diffusion_models", LTX_DEV_UNET, LTX_DEV_UNET_URL, LTX_DEV_UNET_SIZE,
            "LTX-2.5 Dev int8 transformer", cache_ssd=False,
        )
    else:
        _ensure_volume_file(
            log, "diffusion_models", LTX_UNET, LTX_UNET_URL, LTX_UNET_SIZE,
            "LTX-2.5 Distilled int8 transformer", cache_ssd=False,
        )


def setup_model_links():
    """Force-link models into ComfyUI internal folders (SSD cache preferred)."""
    src_roots = [
        CACHE_DIR,
        "/runpod-volume/models",
        "/runpod-volume",
        "/workspace/models",
    ]
    internal_base = "/comfyui/models"

    log_file = "/workspace/setup.log"
    with open(log_file, "w") as log:
        log.write(f"🚀 Starting LTX-2.5 model setup... (ENGINE={ENGINE})\n")
        ensure_ltx_models(log)

        folders = [
            "diffusion_models",
            "text_encoders",
            "vae",
            "latent_upscale_models",
            "upscale_models",
            "clip_vision",
            "checkpoints",
            "loras",
        ]

        for folder in folders:
            dst = os.path.join(internal_base, folder)
            linked = False

            for src_root in src_roots:
                src = os.path.join(src_root, folder)
                if os.path.exists(src) and os.path.isdir(src):
                    log.write(f"📂 Found source at {src_root}: {src}\n")

                    if os.path.exists(dst):
                        try:
                            if os.path.islink(dst):
                                os.unlink(dst)
                            elif os.path.isdir(dst):
                                shutil.rmtree(dst)
                            else:
                                os.remove(dst)
                        except Exception as e:
                            log.write(f"❌ Failed to clear {dst}: {str(e)}\n")

                    try:
                        os.symlink(src, dst)
                        log.write(f"✅ Created symlink: {src} -> {dst}\n")
                        linked = True
                        break
                    except Exception as e:
                        log.write(f"⚠️ Link failed for {folder}: {str(e)}\n")

            if not linked:
                log.write(f"ℹ️ No valid source found for {folder} in any path\n")


if __name__ == "__main__":
    setup_model_links()
