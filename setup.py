import os
import shutil
import subprocess
import time

T5_URL = "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/umt5-xxl-enc-fp8_e4m3fn.safetensors"
T5_EXPECTED_SIZE = 6_731_333_792
T2V_FILENAME = "Wan2_1-T2V-14B_fp8_e4m3fn.safetensors"
T2V_URL = f"https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/{T2V_FILENAME}"
T2V_EXPECTED_SIZE = 14_859_762_840
UPSCALE_FILENAME = "4x-UltraSharp.pth"
UPSCALE_URL = f"https://huggingface.co/Kim2091/UltraSharp/resolve/main/{UPSCALE_FILENAME}"
# Accept any complete-looking download (>= 50MB); exact HF sizes vary by mirror
UPSCALE_MIN_SIZE = 50_000_000

I2V_FILENAME = "Wan2_1-I2V-14B-480P_fp8_e4m3fn.safetensors"
I2V_URL = f"https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/{I2V_FILENAME}"
I2V_EXPECTED_SIZE = 16_993_877_896

# ComfyUI CLIPVisionLoader requires the Comfy-Org repack, not Kijai's open-clip file
CLIP_VISION_FILENAME = "clip_vision_h.safetensors"
CLIP_VISION_URL = (
    "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/"
    f"split_files/clip_vision/{CLIP_VISION_FILENAME}"
)
CLIP_VISION_EXPECTED_SIZE = 1_264_219_396
# Old invalid file that breaks CLIPVisionLoader — delete to free volume space
CLIP_VISION_LEGACY_FILENAME = "open-clip-xlm-roberta-large-vit-huge-14_visual_fp16.safetensors"

# NUCLEAR UPGRADE: Local SSD Caching
# We copy models from the slow Network Volume (/runpod-volume) to the fast local NVMe (/local_models)
CACHE_DIR = "/local_models"

def ensure_t5_model(log):
    """Atomically repair a missing or interrupted T5 download on the volume."""
    volume_root = "/runpod-volume"
    target = os.path.join(volume_root, "models", "text_encoders", "umt5_xxl_fp8.safetensors")
    root_copy = os.path.join(volume_root, "umt5_xxl_fp8.safetensors")

    if not os.path.isdir(volume_root):
        log.write("ℹ️ /runpod-volume is not mounted; skipping T5 repair\n")
        return

    os.makedirs(os.path.dirname(target), exist_ok=True)
    
    target_size = os.path.getsize(target) if os.path.isfile(target) else 0
    if target_size == T5_EXPECTED_SIZE:
        log.write(f"✅ T5 model is complete on volume ({target_size} bytes)\n")
    else:
        root_size = os.path.getsize(root_copy) if os.path.isfile(root_copy) else 0
        if root_size == T5_EXPECTED_SIZE:
            log.write("♻️ Replacing incomplete T5 model with complete volume-root copy\n")
            os.replace(root_copy, target)
        else:
            temp_path = f"{target}.download"
            for path in (target, temp_path):
                if os.path.isfile(path): os.remove(path)

            log.write(f"⬇️ T5 model is incomplete; downloading to volume...\n")
            log.flush()
            subprocess.run(["wget", "--progress=dot:giga", "-O", temp_path, T5_URL], check=True)
            os.replace(temp_path, target)
            log.write(f"✅ T5 model repaired on volume\n")

    # SSD CACHE STEP
    cache_path = os.path.join(CACHE_DIR, "text_encoders", "umt5_xxl_fp8.safetensors")
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    if not os.path.exists(cache_path) or os.path.getsize(cache_path) != T5_EXPECTED_SIZE:
        log.write(f"🚀 Caching T5 to SSD for ultra-fast loading...\n")
        log.flush()
        start = time.time()
        shutil.copy2(target, cache_path)
        log.write(f"⚡ T5 cached in {int(time.time()-start)}s\n")
    else:
        log.write("✅ T5 already cached on SSD\n")

def ensure_t2v_model(log):
    """Ensure the 16-channel text-to-video diffusion model is available and cached."""
    volume_root = "/runpod-volume"
    target = os.path.join(volume_root, "models", "diffusion_models", T2V_FILENAME)

    if not os.path.isdir(volume_root):
        log.write("ℹ️ /runpod-volume is not mounted; skipping T2V model setup\n")
        return

    os.makedirs(os.path.dirname(target), exist_ok=True)
    target_size = os.path.getsize(target) if os.path.isfile(target) else 0
    if target_size != T2V_EXPECTED_SIZE:
        temp_path = f"{target}.download"
        for path in (target, temp_path):
            if os.path.isfile(path): os.remove(path)
        log.write("⬇️ Downloading T2V model to volume...\n")
        log.flush()
        subprocess.run(["wget", "--progress=dot:giga", "-O", temp_path, T2V_URL], check=True)
        os.replace(temp_path, target)
        log.write(f"✅ T2V model installed on volume\n")
    else:
        log.write(f"✅ T2V model is complete on volume\n")

    # SSD CACHE STEP
    cache_path = os.path.join(CACHE_DIR, "diffusion_models", T2V_FILENAME)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    if not os.path.exists(cache_path) or os.path.getsize(cache_path) != T2V_EXPECTED_SIZE:
        log.write(f"🚀 Caching T2V (15GB) to SSD... this takes ~2 mins but saves 20 mins later\n")
        log.flush()
        start = time.time()
        shutil.copy2(target, cache_path)
        log.write(f"⚡ T2V cached in {int(time.time()-start)}s\n")
    else:
        log.write("✅ T2V already cached on SSD\n")


def ensure_upscale_model(log):
    """Ensure 4x-UltraSharp exists on the volume for 1080p Shorts upscaling."""
    volume_root = "/runpod-volume"
    target = os.path.join(volume_root, "models", "upscale_models", UPSCALE_FILENAME)

    if not os.path.isdir(volume_root):
        log.write("ℹ️ /runpod-volume is not mounted; skipping upscale model setup\n")
        return

    os.makedirs(os.path.dirname(target), exist_ok=True)
    target_size = os.path.getsize(target) if os.path.isfile(target) else 0
    if target_size >= UPSCALE_MIN_SIZE:
        log.write(f"✅ Upscale model is complete on volume ({target_size} bytes)\n")
    else:
        temp_path = f"{target}.download"
        for path in (target, temp_path):
            if os.path.isfile(path):
                os.remove(path)
        log.write(f"⬇️ Downloading {UPSCALE_FILENAME} to volume...\n")
        log.flush()
        subprocess.run(["wget", "--progress=dot:giga", "-O", temp_path, UPSCALE_URL], check=True)
        downloaded_size = os.path.getsize(temp_path)
        if downloaded_size < UPSCALE_MIN_SIZE:
            os.remove(temp_path)
            raise RuntimeError(
                f"Upscale download too small: {downloaded_size}; expected >= {UPSCALE_MIN_SIZE}"
            )
        os.replace(temp_path, target)
        log.write(f"✅ Upscale model installed on volume ({downloaded_size} bytes)\n")

    cache_path = os.path.join(CACHE_DIR, "upscale_models", UPSCALE_FILENAME)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    if not os.path.exists(cache_path) or os.path.getsize(cache_path) < UPSCALE_MIN_SIZE:
        log.write("🚀 Caching upscale model to SSD...\n")
        log.flush()
        start = time.time()
        shutil.copy2(target, cache_path)
        log.write(f"⚡ Upscale model cached in {int(time.time() - start)}s\n")
    else:
        log.write("✅ Upscale model already cached on SSD\n")


def _ensure_volume_file(log, rel_dir, filename, url, expected_size, label):
    """Download a model onto the network volume and mirror it to SSD cache."""
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
        subprocess.run(["wget", "--progress=dot:giga", "-O", temp_path, url], check=True)
        os.replace(temp_path, target)
        log.write(f"✅ {label} installed on volume\n")
    else:
        log.write(f"✅ {label} is complete on volume\n")

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


def ensure_i2v_model(log):
    """Ensure Wan 2.1 I2V 480P FP8 is available for continuous last-frame chaining."""
    _ensure_volume_file(
        log,
        "diffusion_models",
        I2V_FILENAME,
        I2V_URL,
        I2V_EXPECTED_SIZE,
        "I2V 14B 480P FP8",
    )


def ensure_clip_vision(log):
    """Ensure ComfyUI-compatible CLIP vision weights for Wan I2V conditioning."""
    # Remove the Kijai open-clip file — CLIPVisionLoader rejects it as invalid
    legacy_paths = [
        os.path.join("/runpod-volume/models/clip_vision", CLIP_VISION_LEGACY_FILENAME),
        os.path.join(CACHE_DIR, "clip_vision", CLIP_VISION_LEGACY_FILENAME),
    ]
    for legacy in legacy_paths:
        if os.path.isfile(legacy):
            try:
                os.remove(legacy)
                log.write(f"🧹 Removed invalid CLIP vision file: {legacy}\n")
            except Exception as e:
                log.write(f"⚠️ Could not remove legacy CLIP file {legacy}: {e}\n")

    _ensure_volume_file(
        log,
        "clip_vision",
        CLIP_VISION_FILENAME,
        CLIP_VISION_URL,
        CLIP_VISION_EXPECTED_SIZE,
        "CLIP Vision H (Comfy-Org)",
    )


def setup_model_links():
    """Nuclear Option: Force-link models into ComfyUI internal folders."""
    # Priority: 1. Local Cache (SSD), 2. Network Volume
    src_roots = [
        CACHE_DIR,
        "/runpod-volume/models",
        "/runpod-volume",
        "/workspace/models"
    ]
    internal_base = "/comfyui/models"
    
    log_file = "/workspace/setup.log"
    with open(log_file, "w") as log:
        log.write("🚀 Starting Nuclear Symlink Setup with SSD Caching...\n")
        ensure_t5_model(log)
        ensure_t2v_model(log)
        ensure_i2v_model(log)
        ensure_clip_vision(log)
        ensure_upscale_model(log)
        
        folders = [
            "diffusion_models",
            "text_encoders",
            "vae",
            "upscale_models",
            "clip_vision",
            "checkpoints",
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
                            if os.path.islink(dst): os.unlink(dst)
                            elif os.path.isdir(dst): shutil.rmtree(dst)
                            else: os.remove(dst)
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
