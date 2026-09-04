import os
import shutil

def setup_model_links():
    """Nuclear Option: Force-link models into ComfyUI internal folders."""
    vol_paths = ["/runpod-volume", "/workspace/models"]
    internal_base = "/comfyui/models"
    
    print("🚀 Starting Aggressive Symlink Setup...")
    
    # Folders that ComfyUI cares about
    folders = ["diffusion_models", "text_encoders", "vae", "upscale_models", "checkpoints"]
    
    for folder in folders:
        dst = os.path.join(internal_base, folder)
        linked = False
        
        for vol in vol_paths:
            src = os.path.join(vol, folder)
            if os.path.exists(src) and os.path.isdir(src):
                print(f"📂 Found source: {src}")
                
                # NUCLEAR: Remove existing destination entirely to make room for link
                if os.path.exists(dst):
                    print(f"♻️ Clearing existing path at {dst}...")
                    if os.path.islink(dst):
                        os.unlink(dst)
                    elif os.path.isdir(dst):
                        shutil.rmtree(dst)
                    else:
                        os.remove(dst)
                
                try:
                    os.symlink(src, dst)
                    print(f"✅ Created symlink: {src} -> {dst}")
                    linked = True
                    break
                except Exception as e:
                    print(f"⚠️ Link failed for {folder}: {str(e)}")
        
        if not linked:
            # If no folder exists, maybe the files are just in the root of the volume?
            # We check if the volume itself has .safetensors and if so, link it to diffusion_models
            for vol in vol_paths:
                if os.path.exists(vol) and any(f.endswith(".safetensors") for f in os.listdir(vol)):
                    print(f"🧪 Volume root contains safetensors. Linking {vol} -> {dst}")
                    if not os.path.exists(dst):
                        os.symlink(vol, dst)
                        break

if __name__ == "__main__":
    setup_model_links()
