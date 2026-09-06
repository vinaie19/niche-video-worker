import os
import time
import json
import requests
import boto3
import shutil
import threading
import uuid
from flask import Flask, request, jsonify

app = Flask(__name__)

# Cloudflare R2 Client Init
s3 = boto3.client(
    's3',
    endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY')
)

# Global job tracker
jobs = {}

# Wan VAE requires temporal length 4k+1 (e.g. 17, 33, 49, 65, 81)
VALID_FRAME_COUNTS = {17, 33, 49, 65, 81, 97, 113, 129}


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
    """Clamp/snap frame counts to Wan's 4k+1 rule."""
    if n in VALID_FRAME_COUNTS:
        return n
    # Snap to nearest valid count
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
            return torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    except Exception:
        pass
    return 32.0  # assume comfortable card


def should_force_offload(vram_gb=None):
    """24GB cards need offload for Wan 14B + UltraSharp; 32GB+ can stay resident."""
    flag = os.getenv("FORCE_OFFLOAD", "").lower()
    if flag in ("true", "1", "yes"):
        return True
    if flag in ("false", "0", "no"):
        return False
    if vram_gb is None:
        vram_gb = detect_vram_gb()
    return vram_gb <= 26


def wait_for_comfyui():
    """Polls internal ComfyUI instance until active."""
    print("⏳ Waiting for internal ComfyUI engine...")
    while True:
        try:
            res = requests.get("http://127.0.0.1:8188/system_stats", timeout=2, headers={"Host": "127.0.0.1"})
            if res.status_code == 200:
                print("✅ ComfyUI is online and operational!")
                break
        except Exception:
            time.sleep(2)

def execute_render_async(job_id, prompt_text, video_id, shot_index):
    try:
        jobs[job_id]["status"] = "processing"
        
        # Refresh ComfyUI file list
        try:
            requests.post("http://127.0.0.1:8188/refresh_custom_nodes", headers={"Host": "127.0.0.1"}, timeout=2)
        except:
            pass

        # Load API workflow
        with open("/workspace/workflow_api.json", "r") as f:
            workflow = json.load(f)

        # Model and Path Diagnostics (Optional logging)
        diffusion_model_file = None
        text_encoder_file = None
        vae_file = None

        # Priority: /local_models (SSD), then /runpod-volume, then /workspace
        vols = ["/local_models", "/runpod-volume/models", "/runpod-volume", "/workspace/models"]
        
        for vol in vols:
            diff_path = os.path.join(vol, "diffusion_models")
            if os.path.exists(diff_path):
                files = [f for f in os.listdir(diff_path) if f.endswith(".safetensors")]
                # Prefer T2V, then any Wan 14B FP8 (supports I2V later)
                t2v = [f for f in files if "t2v" in f.lower() and "14b" in f.lower() and "fp8" in f.lower()]
                wan14 = [f for f in files if ("wan2_1" in f.lower() or "wan2.1" in f.lower()) and "14b" in f.lower() and "fp8" in f.lower()]
                matches = t2v or wan14
                if matches:
                    diffusion_model_file = sorted(matches)[0]
                    print(f"🎯 Auto-detected diffusion model from {vol}: {diffusion_model_file}")
                    break

        for vol in vols:
            te_path = os.path.join(vol, "text_encoders")
            if os.path.exists(te_path):
                files = os.listdir(te_path)
                matches = [f for f in files if "umt5" in f and f.endswith(".safetensors")]
                if matches:
                    text_encoder_file = matches[0]
                    break

        for vol in vols:
            vae_path = os.path.join(vol, "vae")
            if os.path.exists(vae_path):
                files = os.listdir(vae_path)
                matches = [f for f in files if "vae" in f and f.endswith(".safetensors")]
                if matches:
                    vae_file = matches[0]
                    break

        use_sage = sageattn_available()
        vram_gb = detect_vram_gb()
        force_offload = should_force_offload(vram_gb)
        print(f"🖥️ VRAM≈{vram_gb:.0f}GB | force_offload={force_offload} | attention={'sageattn' if use_sage else 'sdpa'}")

        for node_id, node in workflow.items():
            class_type = node.get("class_type")

            # Text encoder + disk cache (speeds shots 2+ on same pod)
            if node.get("_meta", {}).get("title") == "Positive Prompt" or class_type in ["WanVideoTextEncode", "WanVideoTextEncodeCached"]:
                if "positive_prompt" in node["inputs"]:
                    node["inputs"]["positive_prompt"] = prompt_text
                elif "text" in node["inputs"]:
                    node["inputs"]["text"] = prompt_text

                if text_encoder_file and "model_name" in node["inputs"]:
                    node["inputs"]["model_name"] = text_encoder_file
                if "quantization" in node["inputs"]:
                    node["inputs"]["quantization"] = "disabled"
                node["inputs"]["use_disk_cache"] = True

            # Diffusion model + safe attention default
            if class_type == "WanVideoModelLoader":
                if diffusion_model_file:
                    node["inputs"]["model"] = diffusion_model_file
                node["inputs"]["attention_mode"] = "sageattn" if use_sage else "sdpa"
                # 24GB: start on offload device; 32GB: keep on main
                node["inputs"]["load_device"] = "offload_device" if force_offload else "main_device"

            # Enforce 4k+1 frame rule for Wan VAE
            if class_type == "WanVideoEmptyEmbeds" and "num_frames" in node["inputs"]:
                requested = int(node["inputs"]["num_frames"])
                fixed = nearest_valid_frames(requested)
                if fixed != requested:
                    print(f"⚠️ num_frames {requested} invalid for Wan VAE; snapping to {fixed} (4k+1)")
                node["inputs"]["num_frames"] = fixed

            # Offload on 24GB cards so UltraSharp 1080p has room after sampling
            if class_type == "WanVideoSampler":
                node["inputs"]["force_offload"] = force_offload

            if class_type == "WanVideoVAELoader" and vae_file:
                node["inputs"]["model_name"] = vae_file

            # Prefer auto-detected UltraSharp if present
            if class_type == "UpscaleModelLoader":
                for vol in vols:
                    up_path = os.path.join(vol, "upscale_models")
                    if os.path.exists(up_path):
                        files = os.listdir(up_path)
                        matches = [f for f in files if "ultrasharp" in f.lower() or f.endswith(".pth")]
                        if matches:
                            node["inputs"]["model_name"] = sorted(matches)[0]
                            break

        # Submit job to ComfyUI
        res_raw = requests.post("http://127.0.0.1:8188/prompt", json={"prompt": workflow}, headers={"Host": "127.0.0.1"})
        if res_raw.status_code != 200:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = f"ComfyUI Validation Error: {res_raw.text}"
            return

        prompt_id = res_raw.json()["prompt_id"]
        
        # Poll history until finished
        output_filename = None
        start_poll = time.time()
        while not output_filename:
            if time.time() - start_poll > 1200: # 20 min timeout for long video renders
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error"] = "Generation timed out after 20 minutes"
                return

            time.sleep(5)
            try:
                hist_res = requests.get(f"http://127.0.0.1:8188/history/{prompt_id}", headers={"Host": "127.0.0.1"}, timeout=5)
                history = hist_res.json()
                if prompt_id in history:
                    if "status" in history[prompt_id] and "messages" in history[prompt_id]["status"]:
                        for msg in history[prompt_id]["status"]["messages"]:
                            if msg[0] == "execution_error":
                                jobs[job_id]["status"] = "failed"
                                jobs[job_id]["error"] = f"ComfyUI Execution Error: {msg[1]}"
                                return

                    outputs = history[prompt_id].get("outputs", {})
                    for node_id, node_output in outputs.items():
                        # Support for both GIF and Video output keys
                        keys = ["gifs", "videos", "images"] # VHS sometimes uses images key for video
                        for key in keys:
                            if key in node_output and node_output[key]:
                                output_filename = node_output[key][0].get("filename")
                                if output_filename:
                                    break
                        if output_filename:
                            break
            except Exception as e:
                print(f"⚠️ Polling error: {str(e)}")
                continue

        # Upload to R2
        local_file_path = f"/comfyui/output/{output_filename}"
        r2_key = f"renders/{video_id}/shot_{shot_index}.mp4"
        
        print(f"☁️ Uploading {output_filename} to Cloudflare R2... (Size: {os.path.getsize(local_file_path)} bytes)")
        s3.upload_file(local_file_path, os.getenv("R2_BUCKET_NAME"), r2_key)
        r2_public_url = f"{os.getenv('R2_PUBLIC_URL_PREFIX')}/{r2_key}"
        
        if os.path.exists(local_file_path):
            os.remove(local_file_path)

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["output_r2_url"] = r2_public_url

    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"💥 Execution Error: {error_msg}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = error_msg

@app.route('/', methods=['GET'])
def index():
    return jsonify({"service": "niche-video-worker", "status": "online"})

@app.route('/health', methods=['GET'])
def health_check():
    diag = {}
    for p in ["/local_models", "/runpod-volume", "/workspace/models", "/comfyui/models/diffusion_models", "/comfyui/models/upscale_models"]:
        if os.path.exists(p):
            diag[p] = {"exists": True, "files": os.listdir(p)[:5]}
        else:
            diag[p] = {"exists": False}
    
    setup_log = ""
    if os.path.exists("/workspace/setup.log"):
        with open("/workspace/setup.log", "r") as f:
            setup_log = f.read()

    return jsonify({
        "status": "ready",
        "diagnostics": diag,
        "setup_log": setup_log,
        "vram_gb": detect_vram_gb(),
        "force_offload": should_force_offload(),
    })

@app.route('/prompt', methods=['POST'])
def handle_prompt():
    data = request.json
    job_id = str(uuid.uuid4())
    
    jobs[job_id] = {
        "status": "queued",
        "video_id": data.get("video_id"),
        "shot_index": data.get("shot_index"),
        "created_at": time.time()
    }
    
    # Start background thread
    thread = threading.Thread(target=execute_render_async, args=(
        job_id,
        data.get("prompt"),
        data.get("video_id"),
        data.get("shot_index")
    ))
    thread.start()
    
    return jsonify({"job_id": job_id, "status": "queued"})

@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)

if __name__ == "__main__":
    wait_for_comfyui()
    app.run(host="0.0.0.0", port=8000)
