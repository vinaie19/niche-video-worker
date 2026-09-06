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

# Under-$1/hr capable GPUs for Wan 14B FP8 + UltraSharp (EU-RO-1 volume region)
# Prefer 32GB, then 24GB with worker-side force_offload.
GPU_FALLBACKS = [
    ("NVIDIA GeForce RTX 5090", 32),
    ("NVIDIA RTX PRO 4500 Blackwell", 32),
    ("NVIDIA GeForce RTX 4090", 24),
    ("NVIDIA L4", 24),
    ("NVIDIA RTX PRO 4000 Blackwell", 24),
]


def launch_pod():
    image = "vinaie/niche-video-worker:latest"
    preferred = os.getenv("RUNPOD_GPU_TYPE", "").strip().strip('"')
    # Put preferred GPU first if set, then remaining fallbacks (deduped)
    ordered = []
    if preferred:
        match = next((g for g in GPU_FALLBACKS if g[0] == preferred), None)
        ordered.append(match if match else (preferred, 32))
    for gpu_id, vram in GPU_FALLBACKS:
        if not any(g[0] == gpu_id for g in ordered):
            ordered.append((gpu_id, vram))

    env_vars = {
        "R2_ACCOUNT_ID": os.getenv("R2_ACCOUNT_ID"),
        "R2_ACCESS_KEY_ID": os.getenv("R2_ACCESS_KEY_ID"),
        "R2_SECRET_ACCESS_KEY": os.getenv("R2_SECRET_ACCESS_KEY"),
        "R2_BUCKET_NAME": os.getenv("R2_BUCKET_NAME"),
        "R2_PUBLIC_URL_PREFIX": os.getenv("R2_PUBLIC_URL_PREFIX"),
    }

    pod = None
    gpu_type_id = None
    gpu_vram = None
    last_error = None

    print(f"🚀 Launching Dedicated GPU Pod with image: {image}...")
    for gpu_type_id, gpu_vram in ordered:
        print(f"   🔎 Trying {gpu_type_id} ({gpu_vram}GB)...")
        try:
            pod = runpod.create_pod(
                name="test-batch-pod",
                image_name=image,
                gpu_type_id=gpu_type_id,
                container_disk_in_gb=50,
                ports="8000/http",
                network_volume_id="cxgqbfwsvr",
                data_center_id="EU-RO-1",
                env={
                    **env_vars,
                    "GPU_VRAM_GB": str(gpu_vram),
                    "FORCE_OFFLOAD": "true" if gpu_vram <= 24 else "false",
                }
            )
            print(f"   ✅ Acquired {gpu_type_id}")
            break
        except Exception as e:
            last_error = e
            print(f"   ⚠️ Unavailable: {e}")
            pod = None

    if not pod:
        raise Exception(f"No GPU available from fallback list. Last error: {last_error}")

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
    
    max_retries = 240  # first boot may download I2V (~17GB) + CLIP vision
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
        shot_mode = vid.get("shot_mode", "multi_cut")
        chunks = vid.get("chunks", 2)
        upscale = vid.get("upscale", True)

        # Continuous mode: one job with N chained chunks → one R2 URL
        prompts = vid["shots"] if shot_mode == "multi_cut" else [vid["shots"][0]]

        for idx, prompt in enumerate(prompts):
            label = (
                f"{vid_id} continuous ({chunks} chunks)"
                if shot_mode != "multi_cut"
                else f"{vid_id} - Shot {idx+1}/{len(prompts)}"
            )
            print(f"🎬 Submitting {label}...")
            payload = {
                "prompt": prompt,
                "video_id": vid_id,
                "shot_index": idx + 1,
                "shot_mode": shot_mode,
                "chunks": chunks,
                "upscale": upscale,
            }

            try:
                res = requests.post(f"{comfy_url}/prompt", json=payload, timeout=30).json()
                job_id = res.get("job_id")
                if not job_id:
                    print(f"   ❌ Failed to get job_id: {res}")
                    continue

                print(f"   🕒 Job {job_id} queued ({shot_mode}). Polling for status...")

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
                        print("   ⏭️ Skipping this shot and continuing the batch...")
                        finished = True
                    else:
                        progress = status_res.get("progress", status)
                        elapsed = int(time.time() - status_res.get("created_at", time.time()))
                        print(f"   ... {progress} (elapsed: {elapsed}s)")

            except Exception as e:
                print(f"   ❌ Error on shot {idx+1}: {str(e)}")
                print("   ⏭️ Skipping this shot and continuing the batch...")
                continue

    return rendered_urls


def download_and_stitch(rendered_urls, test_jobs):
    os.makedirs("./final_videos", exist_ok=True)
    os.makedirs("./temp_clips", exist_ok=True)

    mode_by_id = {v["video_id"]: v.get("shot_mode", "multi_cut") for v in test_jobs}

    for vid_id, urls in rendered_urls.items():
        urls = [url for url in urls if url]
        if not urls:
            continue

        # Continuous already returns one final clip
        if mode_by_id.get(vid_id) in ("continuous", "single_shot", "singleshot"):
            path = f"./final_videos/{vid_id}_complete.mp4"
            r = requests.get(urls[0], stream=True)
            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"🎉 Continuous Video Downloaded: {path}")
            continue

        local_paths = []
        for idx, url in enumerate(urls):
            path = f"./temp_clips/{vid_id}_shot_{idx+1}.mp4"
            r = requests.get(url, stream=True)
            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            local_paths.append(path)

        list_file = f"./temp_clips/{vid_id}_list.txt"
        with open(list_file, "w") as f:
            for p in local_paths:
                f.write(f"file '{os.path.abspath(p)}'\n")

        output_video = f"./final_videos/{vid_id}_complete.mp4"
        subprocess.run(
            f"ffmpeg -y -f concat -safe 0 -i {list_file} -c copy {output_video}",
            shell=True,
            check=True,
        )
        print(f"🎉 Complete Video Created: {output_video}")


def destroy_pod(pod_id):
    print(f"🔥 Auto-terminating Pod {pod_id}...")
    runpod.terminate_pod(pod_id)


if __name__ == "__main__":
    from test_prompts import test_jobs

    pod_id = None
    try:
        pod_id, comfy_url = launch_pod()
        urls = execute_batch(comfy_url, test_jobs)
        download_and_stitch(urls, test_jobs)
    except Exception as e:
        print(f"❌ Batch Execution Failed: {e}")
        raise
    finally:
        if pod_id:
            destroy_pod(pod_id)
