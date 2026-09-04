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
        container_disk_in_gb=20,
        ports="8000/http",
        network_volume_id="cxgqbfwsvr",
        data_center_id="EU-RO-1"
    )
    pod_id = pod["id"]
    
    start_time = time.time()
    pod_ip = None
    while True:
        info = runpod.get_pod(pod_id)
        if info:
            # Check multiple status fields (some providers use different keys)
            status = info.get("desiredStatus") or info.get("status") or info.get("currentStatus")
            runtime = info.get("runtime")
            
            print(f"   [Debug] Pod ID: {pod_id} | Status: {status}")
            
            if status == "RUNNING" or status == "running":
                # 1. Try runtime gpus podIp
                if runtime and runtime.get("gpus") and len(runtime["gpus"]) > 0:
                    pod_ip = runtime["gpus"][0].get("podIp")
                
                # 2. Try top-level address/publicIp fields
                if not pod_ip:
                    pod_ip = info.get("address") or info.get("publicIp") or info.get("externalIp")
                
                # 3. Check for specific port mapping in runtime ports (RTX 5090 style)
                if runtime and runtime.get("ports"):
                    for p in runtime["ports"]:
                        if p.get("privatePort") == 8000:
                            # Use the public port if we have a base IP/address
                            base_addr = info.get("address") or info.get("publicIp")
                            if base_addr:
                                pod_ip = f"{base_addr}:{p.get('publicPort')}"
                                break

                # 4. Fallback: Construct Proxy URL manually if we have pod_id
                if not pod_ip:
                    # Construct the standard RunPod proxy URL
                    pod_ip = f"{pod_id}-8000.proxy.runpod.net"

                if pod_ip:
                    print(f"⚡ Pod {pod_id} is running at {pod_ip}")
                    break
        
        # Manual Fallback if API is slow (after 60 seconds)
        if time.time() - start_time > 60:
            print("\n⚠️ API is taking too long to report the IP.")
            print(f"Current Pod Info for Debug: {info}")
            manual_ip = input("👉 Please paste the 'Address' or 'Pod IP' from your RunPod dashboard (or press Enter to keep waiting): ").strip()
            if manual_ip:
                pod_ip = manual_ip
                break
        
        print(f"⏳ Waiting for pod initialization... (Elapsed: {int(time.time() - start_time)}s)")
        time.sleep(10)
    
    # Final URL construction
    if not pod_ip:
        raise Exception("Failed to retrieve Pod IP address. Please check your RunPod dashboard.")

    if "proxy.runpod.net" in pod_ip:
        # Proxy URLs already include the port mapping usually, but we ensure it's clean
        if not pod_ip.startswith("http"):
            comfy_url = f"https://{pod_ip}"
        else:
            comfy_url = pod_ip
    elif ":" in pod_ip:
        # Already has a port (e.g. 1.2.3.4:60795)
        comfy_url = f"http://{pod_ip}"
    else:
        # Direct IP needs the port
        comfy_url = f"http://{pod_ip}:8000"
        
    return pod_id, comfy_url

def execute_batch(comfy_url, test_jobs):
    print(f"⏳ Waiting for Worker API at {comfy_url} to become reachable...")
    print("   (Initial 30s wait to allow pod networking to stabilize...)")
    time.sleep(30)
    
    print("   (Now polling for health check - this can take 2-3 more minutes)")
    max_retries = 100 # Increased to ~8 minutes total
    for i in range(max_retries):
        try:
            res = requests.get(f"{comfy_url}/health", timeout=10)
            if res.status_code == 200:
                health_data = res.json()
                print("✅ Worker is online and ready for jobs!")
                
                if "setup_log" in health_data:
                    print("\n📜 --- Worker Setup Log ---")
                    print(health_data["setup_log"])
                    print("---------------------------\n")
                
                if "diagnostics" in health_data:
                    print("📂 --- Worker Diagnostics ---")
                    print(json.dumps(health_data["diagnostics"], indent=2))
                    print("-----------------------------\n")
                break
            else:
                print(f"   [Debug] Received status {res.status_code} from {comfy_url}/health")
        except requests.exceptions.ConnectionError:
            # This is expected while the proxy/server is booting
            pass
        except Exception as e:
            print(f"   [Debug] Connection note: {type(e).__name__}")
        
        if (i + 1) % 6 == 0: # Print every 30 seconds
            print(f"   Still waiting... ({int((i+1)*5)}s elapsed)")
        time.sleep(5)
    else:
        raise Exception("Worker failed to become reachable in time. Please check your pod logs in the RunPod dashboard.")

    rendered_urls = {}
    for vid in test_jobs:
        vid_id = vid["video_id"]
        rendered_urls[vid_id] = []
        for idx, prompt in enumerate(vid["shots"]):
            print(f"🎬 Rendering {vid_id} - Shot {idx+1}/4...")
            payload = {"prompt": prompt, "video_id": vid_id, "shot_index": idx + 1}
            
            try:
                response = requests.post(f"{comfy_url}/prompt", json=payload, timeout=600)
                
                if response.status_code != 200:
                    print(f"   ❌ HTTP Error {response.status_code} from worker")
                    print(f"   [Debug] Response: {response.text[:1000]}")
                    continue

                res = response.json()
                
                if "error" in res:
                    print(f"   ❌ Error from Worker: {res['error']}")
                    # Print everything useful from the response
                    for key in ["details", "diagnostics", "setup_log"]:
                        if key in res:
                            print(f"   🔍 {key.capitalize()}: {json.dumps(res[key], indent=2)}")
                    print("   🛑 Stopping the batch after the first render error")
                    return rendered_urls
                
                r2_url = res.get("output_r2_url")
                rendered_urls[vid_id].append(r2_url)
                print(f"   ✅ R2 URL: {r2_url}")
            except requests.exceptions.Timeout:
                print(f"   ❌ Timeout: Worker took too long to respond for {vid_id}")
            except Exception as e:
                print(f"   ❌ Failed to communicate with worker: {str(e)}")
                if 'response' in locals():
                    print(f"   [Debug] Response Text: {response.text[:500]}")
    return rendered_urls

def download_and_stitch(rendered_urls):
    os.makedirs("./final_videos", exist_ok=True)
    os.makedirs("./temp_clips", exist_ok=True)

    for vid_id, urls in rendered_urls.items():
        urls = [url for url in urls if url]
        if not urls:
            print(f"⚠️ Skipping {vid_id}: no clips rendered successfully")
            continue

        local_paths = []
        for idx, url in enumerate(urls):
            path = f"./temp_clips/{vid_id}_shot_{idx+1}.mp4"
            r = requests.get(url, stream=True)
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            local_paths.append(path)

        # Create FFmpeg file list
        list_file = f"./temp_clips/{vid_id}_list.txt"
        with open(list_file, "w") as f:
            for p in local_paths:
                f.write(f"file '{os.path.abspath(p)}'\n")

        output_video = f"./final_videos/{vid_id}_20sec_1080p.mp4"
        cmd = f"ffmpeg -y -f concat -safe 0 -i {list_file} -c copy {output_video}"
        subprocess.run(cmd, shell=True, check=True)
        print(f"🎉 Complete Video Created: {output_video}")

def destroy_pod(pod_id):
    print(f"🔥 Auto-terminating Pod {pod_id}...")
    runpod.terminate_pod(pod_id)

if __name__ == "__main__":
    from test_prompts import test_jobs
    pod_id = None
    try:
        pod_id, comfy_url = launch_pod()
        time.sleep(10) # VRAM warm up buffer
        urls = execute_batch(comfy_url, test_jobs)
        download_and_stitch(urls)
    finally:
        if pod_id:
            # destroy_pod(pod_id)
            pass