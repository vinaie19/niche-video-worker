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
    try:
        # Load API workflow
        with open("/workspace/workflow_api.json", "r") as f:
            workflow = json.load(f)

        # Set prompt text on node title "Positive Prompt"
        found = False
        for node_id, node in workflow.items():
            if node.get("_meta", {}).get("title") == "Positive Prompt":
                node["inputs"]["text"] = prompt_text
                found = True
        
        if not found:
            print("⚠️ Warning: Could not find node with title 'Positive Prompt'")

        # Submit job with explicit Host header
        res_raw = requests.post("http://127.0.0.1:8188/prompt", json={"prompt": workflow}, headers={"Host": "127.0.0.1"})
        if res_raw.status_code != 200:
            print(f"❌ ComfyUI Error: {res_raw.text}")
            return {"error": f"ComfyUI returned {res_raw.status_code}"}
        
        res = res_raw.json()
        prompt_id = res["prompt_id"]

        # Poll history endpoint until finished
        output_filename = None
        start_poll = time.time()
        while not output_filename:
            # Timeout after 10 minutes (generous for video)
            if time.time() - start_poll > 600:
                return {"error": "Timeout waiting for generation"}

            time.sleep(5)
            hist_res = requests.get(f"http://127.0.0.1:8188/history/{prompt_id}", headers={"Host": "127.0.0.1"})
            history = hist_res.json()
            
            if prompt_id in history:
                # Check for errors in the history
                if "status" in history[prompt_id] and "messages" in history[prompt_id]["status"]:
                    for msg in history[prompt_id]["status"]["messages"]:
                        if msg[0] == "execution_error":
                            return {"error": f"ComfyUI Execution Error: {msg[1]}"}

                outputs = history[prompt_id].get("outputs", {})
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

        return {"output_r2_url": r2_public_url}
    except Exception as e:
        print(f"💥 Execution Error: {str(e)}")
        return {"error": str(e)}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ready"})

@app.route('/prompt', methods=['POST'])
def handle_prompt():
    data = request.json
    result = execute_render(
        prompt_text=data.get("prompt"),
        video_id=data.get("video_id"),
        shot_index=data.get("shot_index")
    )
    return jsonify(result)

if __name__ == "__main__":
    wait_for_comfyui()
    app.run(host="0.0.0.0", port=8000)
