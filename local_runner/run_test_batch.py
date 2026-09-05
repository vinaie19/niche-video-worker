import os
import time
import json
import requests
import boto3
import subprocess
import runpod
from dotenv import load_dotenv

load_dotenv()

runpod.api_key = os.getenv("RUNPOD_API_KEY")

s3_client = boto3.client(
    's3',
    endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY')
)

def launch_pod():
    image = "vinaie/niche-video-worker:latest"
    print(f"🚀 Launching Dedicated GPU Pod with image: {image}...")
    pod = runpod.create_pod(
        name="test-batch-pod",
        image_name=image,
        gpu_type_id=os.getenv("RUNPOD_GPU_TYPE"),
        container_disk_in_gb=50,
        ports="8000/http",
        network_volume_id="cxgqbfwsvr",
        data_center_id="EU-RO-1",
        env={
            "R2_ACCOUNT_ID": os.getenv("R2_ACCOUNT_ID"),
            "R2_ACCESS_KEY_ID": os.getenv("R2_ACCESS_KEY_ID"),
            "R2_SECRET_ACCESS_KEY": os.getenv("R2_SECRET_ACCESS_KEY"),
            "R2_BUCKET_NAME": os.getenv("R2_BUCKET_NAME"),
            "R2_PUBLIC_URL_PREFIX": os.getenv("R2_PUBLIC_URL_PREFIX")
        }
    )
    pod_id = pod["id"]
    
    start_time = time.time()
    pod_ip = None
    while True:
        info = runpod.get_pod(pod_id)
        if info:
            status = info.get("desiredStatus") or info.get("status")
            runtime = info.get("runtime")
            
            if status == "RUNNING" or status == "running":
                if runtime and runtime.get("gpus"):
                    pod_ip = runtime["gpus"][0].get("podIp")
                if not pod_ip:
                    pod_ip = info.get("address") or info.get("publicIp")
                
                if runtime and runtime.get("ports"):
                    for p in runtime["ports"]:
                        if p.get("privatePort") == 8000:
                            base_addr = info.get("address") or info.get("publicIp")
                            if base_addr:
                                pod_ip = f"{base_addr}:{p.get('publicPort')}"
                                break

                if not pod_ip:
                    pod_ip = f"{pod_id}-8000.proxy.runpod.net"

                if pod_ip:
                    print(f"⚡ Pod {pod_id} is running at {pod_ip}")
                    break
        
        if time.time() - start_time > 60:
            print("\n⚠️ API is taking too long to report the IP.")
            manual_ip = input("👉 Please paste the 'Address' or 'Pod IP' from your RunPod dashboard: ").strip()
            if manual_ip:
                pod_ip = manual_ip
                break
        
        time.sleep(10)
    
    if not pod_ip:
        raise Exception("Failed to retrieve Pod IP address.")

    if "proxy.runpod.net" in pod_ip:
        comfy_url = f"https://{pod_ip}" if not pod_ip.startswith("http") else pod_ip
    elif ":" in pod_ip:
        comfy_url = f"http://{pod_ip}"
    else:
        comfy_url = f"http://{pod_ip}:8000"
        
    return pod_id, comfy_url

def execute_batch(comfy_url, test_jobs):
    print(f"⏳ Waiting for Worker API at {comfy_url} to become reachable...")
    time.sleep(30)
    
    max_retries = 100
    for i in range(max_retries):
        try:
            res = requests.get(f"{comfy_url}/health", timeout=10)
            if res.status_code == 200:
                health_data = res.json()
                print("✅ Worker is online and ready for jobs!")
                if "setup_log" in health_data:
                    print("\n📜 --- Worker Setup Log ---")
                    print(health_data["setup_log"])
                break
        except:
            pass
        time.sleep(5)
    else:
        raise Exception("Worker failed to become reachable.")

    rendered_urls = {}
    for vid in test_jobs:
        vid_id = vid["video_id"]
        rendered_urls[vid_id] = []
        for idx, prompt in enumerate(vid["shots"]):
            print(f"🎬 Submitting {vid_id} - Shot {idx+1}/4...")
            payload = {"prompt": prompt, "video_id": vid_id, "shot_index": idx + 1}
            
            try:
                # Step 1: Submit job and get job_id
                res = requests.post(f"{comfy_url}/prompt", json=payload, timeout=30).json()
                job_id = res.get("job_id")
                if not job_id:
                    print(f"   ❌ Failed to get job_id: {res}")
                    continue
                
                print(f"   🕒 Job {job_id} queued. Polling for status...")

                # Step 2: Poll status endpoint
                finished = False
                while not finished:
                    time.sleep(10)
                    status_res = requests.get(f"{comfy_url}/status/{job_id}", timeout=10).json()
                    status = status_res.get("status")
                    
                    if status == "completed":
                        r2_url = status_res.get("output_r2_url")
                        rendered_urls[vid_id].append(r2_url)
                        print(f"   ✅ Success! R2 URL: {r2_url}")
                        finished = True
                    elif status == "failed":
                        print(f"   ❌ Job Failed: {status_res.get('error')}")
                        finished = True
                        return rendered_urls # Stop on first error
                    else:
                        print(f"   ... still {status} (elapsed: {int(time.time() - status_res['created_at'])}s)")
            
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                return rendered_urls

    return rendered_urls

def download_and_stitch(rendered_urls):
    os.makedirs("./final_videos", exist_ok=True)
    os.makedirs("./temp_clips", exist_ok=True)

    for vid_id, urls in rendered_urls.items():
        urls = [url for url in urls if url]
        if not urls: continue

        local_paths = []
        for idx, url in enumerate(urls):
            path = f"./temp_clips/{vid_id}_shot_{idx+1}.mp4"
            r = requests.get(url, stream=True)
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            local_paths.append(path)

        list_file = f"./temp_clips/{vid_id}_list.txt"
        with open(list_file, "w") as f:
            for p in local_paths:
                f.write(f"file '{os.path.abspath(p)}'\n")

        output_video = f"./final_videos/{vid_id}_complete.mp4"
        subprocess.run(f"ffmpeg -y -f concat -safe 0 -i {list_file} -c copy {output_video}", shell=True, check=True)
        print(f"🎉 Complete Video Created: {output_video}")

if __name__ == "__main__":
    from test_prompts import test_jobs
    pod_id = None
    try:
        pod_id, comfy_url = launch_pod()
        urls = execute_batch(comfy_url, test_jobs)
        download_and_stitch(urls)
    finally:
        if pod_id:
            # runpod.terminate_pod(pod_id)
            pass
