import os
import shutil

def setup_model_links():
    """Nuclear Option: Symlink models to ensure ComfyUI sees them BEFORE it starts."""
    vol_paths = ["/runpod-volume", "/workspace/models"]
    internal_base = "/comfyui/models"
    
    print("🚀 Starting Nuclear Symlink Setup...")
    
    # Ensure base directories exist
    os.makedirs(internal_base, exist_ok=True)
    
    folders = ["diffusion_models", "text_encoders", "vae", "upscale_models"]
    
    for folder in folders:
        dst = os.path.join(internal_base, folder)
        linked = False
        
        # Check all possible volume paths
        for vol in vol_paths:
            src = os.path.join(vol, folder)
            if os.path.exists(src):
                print(f"🔗 Found source: {src}")
                
                # Cleanup destination if it's in the way
                if os.path.islink(dst):
                    print(f"♻️ Unlinking existing link at {dst}")
                    os.unlink(dst)
                elif os.path.isdir(dst):
                    if not os.listdir(dst):
                        print(f"♻️ Removing empty dir at {dst}")
                        os.rmdir(dst)
                    else:
                        print(f"⚠️ Destination {dst} is not empty, skipping link.")
                        continue
                
                # Create the link
                if not os.path.exists(dst):
                    try:
                        os.symlink(src, dst)
                        print(f"✅ Successfully linked {folder} from {vol}")
                        linked = True
                        break
                    except Exception as e:
                        print(f"⚠️ Link failed for {folder}: {str(e)}")
        
        if not linked:
            print(f"ℹ️ No valid source found for {folder} in {vol_paths}")

if __name__ == "__main__":
    setup_model_links()
