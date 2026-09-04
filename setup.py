import os
import shutil

def setup_model_links():
    """Nuclear Option: Force-link models into ComfyUI internal folders."""
    vol_paths = ["/runpod-volume", "/workspace/models"]
    internal_base = "/comfyui/models"
    
    log_file = "/workspace/setup.log"
    with open(log_file, "w") as log:
        log.write("🚀 Starting Aggressive Symlink Setup...\n")
        
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
                # If no folder exists, maybe the files are just in the root of the volume?
                for vol in vol_paths:
                    if os.path.exists(vol) and os.path.isdir(vol):
                        files = os.listdir(vol)
                        if any(f.endswith(".safetensors") for f in files):
                            log.write(f"🧪 Volume root {vol} contains safetensors. Linking {vol} -> {dst}\n")
                            if os.path.exists(dst):
                                if os.path.islink(dst): os.unlink(dst)
                                elif os.path.isdir(dst): shutil.rmtree(dst)
                            os.symlink(vol, dst)
                            linked = True
                            break
                
                if not linked:
                    log.write(f"ℹ️ No valid source found for {folder}\n")

if __name__ == "__main__":
    setup_model_links()
