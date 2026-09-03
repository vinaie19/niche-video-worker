import os
import time
import requests
import boto3
import runpod
import json

# Initialize Cloudflare R2 Client
s3 = boto3.client(
    's3',
    endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY')
)

def wait_for_comfyui():
    """Polls ComfyUI API until it's ready to take jobs."""
    while True:
        try:
            res = requests.get("http://127.0.0.1:8188/system_stats", timeout=2)
            if res.status_code == 200:
                print("✅ ComfyUI is online!")
                break
        except Exception:
            time.sleep(2)

def generate_and_upload(job):
    job_input = job.get("input", {})
    prompt_text = job_input.get("prompt")
    video_id = job_input.get("video_id", "test_vid")
    shot_index = job_input.get("shot_index", 1)

    # Load workflow template
    with open("workflow_api.json", "r") as f:
        workflow = json.load(f)

    # Dynamically inject prompt into target node
    for node_id, node in workflow.items():
        if node.get("_meta", {}).get("title") == "Positive Prompt":
            node["inputs"]["text"] = prompt_text

    # Submit to local ComfyUI engine
    res = requests.post("http://127.0.0.1:8188/prompt", json={"prompt": workflow}).json()
    prompt_id = res["prompt_id"]

    # Poll until video rendering finishes
    output_filename = None
    while not output_filename:
        time.sleep(3)
        history = requests.get(f"http://127.0.0.1:8188/history/{prompt_id}").json()
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
    
    s3.upload_file(local_file_path, os.getenv("R2_BUCKET_NAME"), r2_key)
    r2_public_url = f"{os.getenv('R2_PUBLIC_URL_PREFIX')}/{r2_key}"

    # Cleanup local container disk
    if os.path.exists(local_file_path):
        os.remove(local_file_path)

    return {"output_r2_url": r2_public_url}

wait_for_comfyui()
runpod.serverless.start({"handler": generate_and_upload})
