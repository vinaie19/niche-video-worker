import os
import time
import json
import requests
import boto3
from flask import Flask, request, jsonify

app = Flask(__name__)

# Cloudflare R2 Client Init
s3 = boto3.client(
    's3',
    endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY')
)

def wait_for_comfyui():
    """Polls internal ComfyUI instance until active."""
    print("⏳ Waiting for internal ComfyUI engine...")
    while True:
        try:
            # Explicit Host header for aiohttp stability
            res = requests.get("http://127.0.0.1:8188/system_stats", timeout=2, headers={"Host": "127.0.0.1"})
            if res.status_code == 200:
                print("✅ ComfyUI is online and operational!")
                break
        except Exception:
            time.sleep(2)

def execute_render(prompt_text, video_id, shot_index):
    # Load API workflow
    with open("/workspace/workflow_api.json", "r") as f:
        workflow = json.load(f)

    # Set prompt text on node title "Positive Prompt"
    for node_id, node in workflow.items():
        if node.get("_meta", {}).get("title") == "Positive Prompt":
            node["inputs"]["text"] = prompt_text

    # Submit job with explicit Host header
    res = requests.post("http://127.0.0.1:8188/prompt", json={"prompt": workflow}, headers={"Host": "127.0.0.1"}).json()
    prompt_id = res["prompt_id"]

    # Poll history endpoint until finished
    output_filename = None
    while not output_filename:
        time.sleep(3)
        history = requests.get(f"http://127.0.0.1:8188/history/{prompt_id}", headers={"Host": "127.0.0.1"}).json()
        if prompt_id in history:
            outputs = history[prompt_id]["outputs"]
            for node_id, node_output in outputs.items():
                if "gifs" in node_output or "videos" in node_output:
                    key = "gifs" if "gifs" in node_output else "videos"
                    output_filename = node_output[key][0]["filename"]
                    break

    # Upload local MP4 to Cloudflare R2
    local_file_path = f"/comfyui/output/{output_filename}"
    r2_key = f"renders/{video_id}/shot_{shot_index}.mp4"
    
    print(f"☁️ Uploading {output_filename} to Cloudflare R2...")
    s3.upload_file(local_file_path, os.getenv("R2_BUCKET_NAME"), r2_key)
    r2_public_url = f"{os.getenv('R2_PUBLIC_URL_PREFIX')}/{r2_key}"

    # Delete local file to preserve container disk space
    if os.path.exists(local_file_path):
        os.remove(local_file_path)

    return r2_public_url

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ready"})

@app.route('/prompt', methods=['POST'])
def handle_prompt():
    data = request.json
    url = execute_render(
        prompt_text=data.get("prompt"),
        video_id=data.get("video_id"),
        shot_index=data.get("shot_index")
    )
    return jsonify({"output_r2_url": url})

if __name__ == "__main__":
    wait_for_comfyui()
    app.run(host="0.0.0.0", port=8000)
