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
                files = os.listdir(diff_path)
                matches = [f for f in files if "t2v" in f.lower() and "14b" in f.lower() and "fp8" in f.lower() and f.endswith(".safetensors")]
                if matches:
                    diffusion_model_file = sorted(matches)[0]
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

        for node_id, node in workflow.items():
            if node.get("_meta", {}).get("title") == "Positive Prompt" or node.get("class_type") in ["WanVideoTextEncode", "WanVideoTextEncodeCached"]:
                if "positive_prompt" in node["inputs"]:
                    node["inputs"]["positive_prompt"] = prompt_text
                elif "text" in node["inputs"]:
                    node["inputs"]["text"] = prompt_text
                
                if text_encoder_file and "model_name" in node["inputs"]:
                    node["inputs"]["model_name"] = text_encoder_file
                    if "quantization" in node["inputs"]:
                        node["inputs"]["quantization"] = "disabled"
            
            if node.get("class_type") == "WanVideoModelLoader" and diffusion_model_file:
                node["inputs"]["model"] = diffusion_model_file
            
            if node.get("class_type") == "WanVideoVAELoader" and vae_file:
                node["inputs"]["model_name"] = vae_file

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
    for p in ["/local_models", "/runpod-volume", "/workspace/models", "/comfyui/models/diffusion_models"]:
        if os.path.exists(p):
            diag[p] = {"exists": True, "files": os.listdir(p)[:5]}
        else:
            diag[p] = {"exists": False}
    
    setup_log = ""
    if os.path.exists("/workspace/setup.log"):
        with open("/workspace/setup.log", "r") as f:
            setup_log = f.read()

    return jsonify({"status": "ready", "diagnostics": diag, "setup_log": setup_log})

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
