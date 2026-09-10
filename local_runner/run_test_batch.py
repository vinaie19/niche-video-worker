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

# Prefer RTX 5090, then 4500 (same 32GB + offload). No 6000 for now.
GPU_FALLBACKS = [
    ("NVIDIA GeForce RTX 5090", 32),
    ("NVIDIA RTX PRO 4500 Blackwell", 32)
]


def _guess_vram_gb(gpu_type_id):
    """Best-effort VRAM when RUNPOD_GPU_TYPE is a custom / unmatched string."""
    name = (gpu_type_id or "").lower()
    if "6000" in name and "blackwell" in name:
        return 96
    if "5090" in name or "4500" in name:
        return 32
    if "4090" in name or ("4000" in name and "ada" in name) or " l4" in f" {name}":
        return 24
    # RTX 2000 Ada / A2000 — 16GB (cheap download pod; tight for LTX render)
    if "2000" in name:
        return 16
    return 32


def launch_pod():
    image = "vinaie/niche-video-worker:latest"
    preferred = os.getenv("RUNPOD_GPU_TYPE", "").strip().strip('"')
    # Put preferred GPU first if set, then remaining fallbacks (deduped)
    ordered = []
    if preferred:
        match = next((g for g in GPU_FALLBACKS if g[0] == preferred), None)
        ordered.append(match if match else (preferred, _guess_vram_gb(preferred)))
    for gpu_id, vram in GPU_FALLBACKS:
        if not any(g[0] == gpu_id for g in ordered):
            ordered.append((gpu_id, vram))

    env_vars = {
        "R2_ACCOUNT_ID": os.getenv("R2_ACCOUNT_ID"),
        "R2_ACCESS_KEY_ID": os.getenv("R2_ACCESS_KEY_ID"),
        "R2_SECRET_ACCESS_KEY": os.getenv("R2_SECRET_ACCESS_KEY"),
        "R2_BUCKET_NAME": os.getenv("R2_BUCKET_NAME"),
        "R2_PUBLIC_URL_PREFIX": os.getenv("R2_PUBLIC_URL_PREFIX"),
        # wan (default) | hunyuan | ltx — LTX A/B: ENGINE=ltx LTX_VARIANT=distilled
        "ENGINE": os.getenv("ENGINE", "wan"),
        "HY_VARIANT": os.getenv("HY_VARIANT", "480p_distilled"),
        "HY_NUM_FRAMES": os.getenv("HY_NUM_FRAMES", "81"),
        "HY_STEPS": os.getenv("HY_STEPS", "30"),
        "HY_FPS": os.getenv("HY_FPS", "24"),
        "LTX_VARIANT": os.getenv("LTX_VARIANT", "distilled"),
        "LTX_NUM_FRAMES": os.getenv("LTX_NUM_FRAMES", "97"),
        "LTX_STEPS": os.getenv("LTX_STEPS", "8"),
        "LTX_FPS": os.getenv("LTX_FPS", "24"),
        "LTX_WIDTH": os.getenv("LTX_WIDTH", "544"),
        "LTX_HEIGHT": os.getenv("LTX_HEIGHT", "960"),
        # Hunyuan/LTX: keep weights resident between shots (skip /free). Wan still unloads.
        "KEEP_MODELS_LOADED": os.getenv(
            "KEEP_MODELS_LOADED",
            "true" if os.getenv("ENGINE", "wan").strip().lower() in (
                "hunyuan", "hy", "hunyuanvideo", "hunyuan_video", "hunyuan15",
                "ltx", "ltx2", "ltx23", "ltxv", "lightricks",
            ) else "",
        ),
        # Wan 2.2 I2V MoE pair (~29GB) — needs ~75GB network volume
        "INSTALL_WAN22_I2V": os.getenv("INSTALL_WAN22_I2V", "true"),
        # 5090-safe defaults (override per job in test_prompts if needed)
        "WAN_NUM_FRAMES": os.getenv("WAN_NUM_FRAMES", "49"),
        "WAN_STEPS": os.getenv("WAN_STEPS", "16"),
    }

    pod = None
    gpu_type_id = None
    gpu_vram = None
    last_error = None

    # Keep polling until a GPU is free (stock flickers on RunPod).
    # POD_ACQUIRE_RETRIES=0 means forever. Sleep between full passes over the GPU list.
    try:
        max_acquire = int(os.getenv("POD_ACQUIRE_RETRIES", "0"))
    except ValueError:
        max_acquire = 0
    try:
        acquire_sleep = int(os.getenv("POD_ACQUIRE_SLEEP_S", "45"))
    except ValueError:
        acquire_sleep = 45

    print(f"🚀 Launching Dedicated GPU Pod with image: {image}...")
    print(
        f"   ENGINE={env_vars.get('ENGINE')} HY_VARIANT={env_vars.get('HY_VARIANT')} "
        f"LTX_VARIANT={env_vars.get('LTX_VARIANT')}"
    )
    print(
        f"   Acquire loop: retries={'∞' if max_acquire <= 0 else max_acquire} "
        f"| sleep={acquire_sleep}s between passes"
    )

    attempt = 0
    while pod is None:
        attempt += 1
        if max_acquire > 0 and attempt > max_acquire:
            break
        print(f"🔁 Acquire pass {attempt}" + (f"/{max_acquire}" if max_acquire > 0 else "") + "...")

        for gpu_type_id, gpu_vram in ordered:
            # 96GB: keep weights resident. 32/24GB: offload required for 81-frame MoE.
            force_offload = os.getenv("FORCE_OFFLOAD")
            if force_offload is None or force_offload.strip() == "":
                force_offload = "false" if gpu_vram >= 64 else "true"
            else:
                force_offload = force_offload.strip().lower()

            # Hunyuan A/B: 40GB is enough (weights on network volume). Wan MoE cache: 75–100GB.
            try:
                container_disk = int(os.getenv("CONTAINER_DISK_GB", "40"))
            except ValueError:
                container_disk = 40

            print(
                f"   🔎 Trying {gpu_type_id} ({gpu_vram}GB, FORCE_OFFLOAD={force_offload}, "
                f"disk={container_disk}GB)..."
            )
            try:
                pod = runpod.create_pod(
                    name="test-batch-pod",
                    image_name=image,
                    gpu_type_id=gpu_type_id,
                    container_disk_in_gb=container_disk,
                    ports="8000/http",
                    network_volume_id="cxgqbfwsvr",
                    data_center_id="EU-RO-1",
                    env={
                        **env_vars,
                        "GPU_VRAM_GB": str(gpu_vram),
                        "FORCE_OFFLOAD": force_offload,
                    }
                )
                print(f"   ✅ Acquired {gpu_type_id}")
                break
            except Exception as e:
                last_error = e
                print(f"   ⚠️ Unavailable: {e}")
                pod = None

        if pod is None:
            print(f"⏳ No GPU this pass — sleeping {acquire_sleep}s then retrying (Ctrl+C to stop)...")
            time.sleep(acquire_sleep)

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
    
    # Hunyuan first boot can take 40–60+ min for HF downloads; Wan cold cache ~20 min.
    try:
        max_retries = int(os.getenv("HEALTH_MAX_RETRIES", "720"))  # default ~60 min
    except ValueError:
        max_retries = 720
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
            if "num_frames" in vid:
                payload["num_frames"] = int(vid["num_frames"])
            else:
                engine = os.getenv("ENGINE", "wan").strip().lower()
                if engine in ("hunyuan", "hy", "hunyuanvideo") and os.getenv("HY_NUM_FRAMES"):
                    payload["num_frames"] = int(os.getenv("HY_NUM_FRAMES"))
                elif engine in ("ltx", "ltx2", "ltx23", "ltxv") and os.getenv("LTX_NUM_FRAMES"):
                    payload["num_frames"] = int(os.getenv("LTX_NUM_FRAMES"))
                elif os.getenv("WAN_NUM_FRAMES"):
                    payload["num_frames"] = int(os.getenv("WAN_NUM_FRAMES"))
            if "steps" in vid:
                payload["steps"] = int(vid["steps"])
            else:
                engine = os.getenv("ENGINE", "wan").strip().lower()
                if engine in ("hunyuan", "hy", "hunyuanvideo") and os.getenv("HY_STEPS"):
                    payload["steps"] = int(os.getenv("HY_STEPS"))
                elif engine in ("ltx", "ltx2", "ltx23", "ltxv") and os.getenv("LTX_STEPS"):
                    payload["steps"] = int(os.getenv("LTX_STEPS"))
                elif os.getenv("WAN_STEPS"):
                    payload["steps"] = int(os.getenv("WAN_STEPS"))

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
    from audio_post import add_ambient_and_title, add_voice_and_captions

    os.makedirs("./final_videos", exist_ok=True)
    os.makedirs("./temp_clips", exist_ok=True)

    jobs_by_id = {v["video_id"]: v for v in test_jobs}
    mode_by_id = {vid: j.get("shot_mode", "multi_cut") for vid, j in jobs_by_id.items()}

    for vid_id, urls in rendered_urls.items():
        urls = [url for url in urls if url]
        if not urls:
            continue

        job = jobs_by_id.get(vid_id, {})
        script = (job.get("script") or "").strip()
        silent_path = f"./temp_clips/{vid_id}_silent.mp4"
        output_video = f"./final_videos/{vid_id}_complete.mp4"

        # Continuous already returns one final clip
        if mode_by_id.get(vid_id) in ("continuous", "single_shot", "singleshot"):
            r = requests.get(urls[0], stream=True)
            with open(silent_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"⬇️ Continuous silent clip: {silent_path}")
        else:
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

            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    list_file,
                    "-c",
                    "copy",
                    silent_path,
                ],
                check=True,
            )
            print(f"⬇️ Stitched silent video: {silent_path}")

        if script:
            from audio_post import parse_captions_option

            # captions: False | True | "minimal"|"clean"|"boxed"|"yellow"|"tiny"
            # caption_style: optional when captions=True
            captions_field = job.get("captions", job.get("burn_captions", False))
            captions_on, caption_style = parse_captions_option(
                captions_field, job.get("caption_style")
            )
            try:
                ambient = job.get("ambient", "rain_city")
                vo_delay_ms = int(job.get("vo_delay_ms", 900))
                ambient_volume = float(job.get("ambient_volume", 0.38))
                voice_volume = float(job.get("voice_volume", 1.0))
                add_voice_and_captions(
                    silent_path,
                    script,
                    output_video,
                    work_dir=f"./temp_clips/{vid_id}_audio",
                    voice=job.get("voice"),
                    burn_captions=captions_on,
                    caption_style=caption_style,
                    ambient=ambient,
                    vo_delay_ms=vo_delay_ms,
                    ambient_volume=ambient_volume,
                    voice_volume=voice_volume,
                )
                mode = (
                    f"voice + captions({caption_style})"
                    if captions_on
                    else "voice + ambient"
                )
                print(f"🎉 Complete Video ({mode}): {output_video}")
            except Exception as e:
                print(f"⚠️ Audio post failed ({e}); keeping silent copy as final.")
                subprocess.run(["cp", "-f", silent_path, output_video], check=True)
                print(f"🎉 Silent Video Saved: {output_video}")
        else:
            try:
                add_ambient_and_title(
                    silent_path,
                    output_video,
                    work_dir=f"./temp_clips/{vid_id}_audio",
                    ambient=job.get("ambient", False),
                    ambient_volume=float(job.get("ambient_volume", 0.38)),
                    title=job.get("title"),
                )
                print(f"🎉 Complete Video (LTX AV / ambient + title, no VO): {output_video}")
            except Exception as e:
                print(f"⚠️ Audio post failed ({e}); keeping silent copy as final.")
                subprocess.run(["cp", "-f", silent_path, output_video], check=True)
                print(f"🎉 Silent Video Saved: {output_video}")


def destroy_pod(pod_id):
    print(f"🔥 Auto-terminating Pod {pod_id}...")
    runpod.terminate_pod(pod_id)


if __name__ == "__main__":
    from test_prompts import test_jobs, hunyuan_ab_jobs, ltx_ab_jobs

    engine = os.getenv("ENGINE", "wan").strip().lower()
    if engine in ("hunyuan", "hy", "hunyuanvideo", "hunyuan_video", "hunyuan15"):
        jobs = hunyuan_ab_jobs
    elif engine in ("ltx", "ltx2", "ltx23", "ltxv", "lightricks"):
        jobs = ltx_ab_jobs
    else:
        jobs = test_jobs
    print(f"🧪 Batch engine={engine} | jobs={[j['video_id'] for j in jobs]}")

    pod_id = None
    try:
        pod_id, comfy_url = launch_pod()
        urls = execute_batch(comfy_url, jobs)
        download_and_stitch(urls, jobs)
    except Exception as e:
        print(f"❌ Batch Execution Failed: {e}")
        raise
    finally:
        if pod_id:
            destroy_pod(pod_id)
