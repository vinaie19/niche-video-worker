import os
import shutil
import subprocess

T5_URL = "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/umt5-xxl-enc-fp8_e4m3fn.safetensors"
T5_EXPECTED_SIZE = 6_731_333_792
T2V_FILENAME = "Wan2_1-T2V-14B_fp8_e4m3fn.safetensors"
T2V_URL = f"https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/{T2V_FILENAME}"
T2V_EXPECTED_SIZE = 14_859_762_840


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
        log.write(f"✅ T5 model is complete ({target_size} bytes)\n")
        return

    root_size = os.path.getsize(root_copy) if os.path.isfile(root_copy) else 0
    if root_size == T5_EXPECTED_SIZE:
        log.write("♻️ Replacing incomplete T5 model with complete volume-root copy\n")
        os.replace(root_copy, target)
        return

    temp_path = f"{target}.download"
    for path in (target, temp_path):
        if os.path.isfile(path):
            os.remove(path)

    log.write(
        f"⬇️ T5 model is incomplete ({target_size} bytes); downloading a clean copy...\n"
    )
    log.flush()
    subprocess.run(
        ["wget", "--progress=dot:giga", "-O", temp_path, T5_URL],
        check=True,
    )

    downloaded_size = os.path.getsize(temp_path)
    if downloaded_size != T5_EXPECTED_SIZE:
        os.remove(temp_path)
        raise RuntimeError(
            f"T5 download has wrong size: {downloaded_size}; expected {T5_EXPECTED_SIZE}"
        )

    os.replace(temp_path, target)
    log.write(f"✅ T5 model repaired atomically ({downloaded_size} bytes)\n")


def ensure_t2v_model(log):
    """Ensure the 16-channel text-to-video diffusion model is available."""
    volume_root = "/runpod-volume"
    target = os.path.join(volume_root, "models", "diffusion_models", T2V_FILENAME)

    if not os.path.isdir(volume_root):
        log.write("ℹ️ /runpod-volume is not mounted; skipping T2V model setup\n")
        return

    os.makedirs(os.path.dirname(target), exist_ok=True)
    target_size = os.path.getsize(target) if os.path.isfile(target) else 0
    if target_size == T2V_EXPECTED_SIZE:
        log.write(f"✅ T2V model is complete ({target_size} bytes)\n")
        return

    temp_path = f"{target}.download"
    for path in (target, temp_path):
        if os.path.isfile(path):
            os.remove(path)

    log.write(
        "⬇️ The installed diffusion model is I2V (36 channels). "
        "Downloading the required T2V model (16 channels)...\n"
    )
    log.flush()
    subprocess.run(
        ["wget", "--progress=dot:giga", "-O", temp_path, T2V_URL],
        check=True,
    )

    downloaded_size = os.path.getsize(temp_path)
    if downloaded_size != T2V_EXPECTED_SIZE:
        os.remove(temp_path)
        raise RuntimeError(
            f"T2V download has wrong size: {downloaded_size}; expected {T2V_EXPECTED_SIZE}"
        )

    os.replace(temp_path, target)
    log.write(f"✅ T2V model installed atomically ({downloaded_size} bytes)\n")


def setup_model_links():
    """Nuclear Option: Force-link models into ComfyUI internal folders."""
    # We check both the root and the 'models' subdirectory
    vol_paths = [
        "/runpod-volume", 
        "/runpod-volume/models",
        "/workspace/models"
    ]
    internal_base = "/comfyui/models"
    
    log_file = "/workspace/setup.log"
    with open(log_file, "w") as log:
        log.write("🚀 Starting Aggressive Symlink Setup...\n")
        ensure_t5_model(log)
        ensure_t2v_model(log)
        
        # Folders that ComfyUI cares about
        folders = ["diffusion_models", "text_encoders", "vae", "upscale_models", "checkpoints"]
        
        for folder in folders:
            dst = os.path.join(internal_base, folder)
            linked = False
            
            for vol in vol_paths:
                src = os.path.join(vol, folder)
                if os.path.exists(src) and os.path.isdir(src):
                    log.write(f"📂 Found source: {src}\n")
                    
                    # NUCLEAR: Remove existing destination entirely to make room for link
                    if os.path.exists(dst):
                        log.write(f"♻️ Clearing existing path at {dst}...\n")
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
                # Fallback: Check if the volume root itself contains the model files
                for vol in vol_paths:
                    if os.path.exists(vol) and os.path.isdir(vol):
                        files = os.listdir(vol)
                        if any(f.endswith(".safetensors") for f in files):
                            log.write(f"🧪 Volume {vol} contains safetensors. Linking {vol} -> {dst}\n")
                            if os.path.exists(dst):
                                if os.path.islink(dst): os.unlink(dst)
                                elif os.path.isdir(dst): shutil.rmtree(dst)
                            try:
                                os.symlink(vol, dst)
                                linked = True
                                break
                            except:
                                pass
                
                if not linked:
                    log.write(f"ℹ️ No valid source found for {folder} in any path\n")

if __name__ == "__main__":
    setup_model_links()
