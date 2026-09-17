import os
import sys
import time
import json
import requests
import boto3
import subprocess
import runpod
from dotenv import load_dotenv

# Line-buffer logs when stdout is not a TTY (agent/CI pipes).
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(line_buffering=True)
        sys.stderr.reconfigure(line_buffering=True)
    except Exception:
        pass

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)

runpod.api_key = os.getenv("RUNPOD_API_KEY")

s3_client = boto3.client(
    's3',
    endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY')
)

POD_NAME = os.getenv("RUNPOD_POD_NAME", "niche-ltx25-render")

# LTX-2.5 @ 1088x1920 needs ~96GB — do not fall back to 32GB cards (OOM / useless offload).
GPU_FALLBACKS = [
    ("NVIDIA RTX PRO 6000 Blackwell Server Edition", 96),
    ("NVIDIA RTX PRO 6000 Blackwell Workstation Edition", 96),
    ("NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition", 96),
]


def _guess_vram_gb(gpu_type_id):
    """Best-effort VRAM when RUNPOD_GPU_TYPE is a custom / unmatched string."""
    name = (gpu_type_id or "").lower()
    # Blackwell 6000 family only — do NOT treat Ada 6000 (48GB) as 96GB
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


def _ltx_te_device_for_vram(vram_gb):
    """CLIPLoader device: only 'default' | 'cpu' (not 'gpu').
    default ≈ GPU/main device; cpu = force CPU encode (32GB-safe)."""
    explicit = os.getenv("LTX_TE_DEVICE", "").strip().lower()
    if explicit in ("cpu",):
        return "cpu"
    if explicit in ("default", "gpu", "cuda"):
        return "default"
    return "default" if float(vram_gb) >= 64 else "cpu"


def _persist_pod_id(pod_id: str):
    """Remember pod id in local_runner/.env so the next run can resume it."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    lines = []
    if os.path.isfile(env_path):
        with open(env_path) as f:
            lines = f.read().splitlines()
    out, seen = [], False
    for line in lines:
        if line.startswith("RUNPOD_POD_ID="):
            out.append(f"RUNPOD_POD_ID={pod_id}")
            seen = True
        else:
            out.append(line)
    if not seen:
        out.append(f"RUNPOD_POD_ID={pod_id}")
    with open(env_path, "w") as f:
        f.write("\n".join(out) + "\n")
    os.environ["RUNPOD_POD_ID"] = pod_id
    print(f"💾 Saved RUNPOD_POD_ID={pod_id} to local_runner/.env")


def _pod_comfy_url(pod_id: str, info: dict | None = None) -> str:
    info = info or runpod.get_pod(pod_id) or {}
    runtime = info.get("runtime") or {}
    pod_ip = None
    if runtime.get("ports"):
        for p in runtime["ports"]:
            if p.get("privatePort") == 8000:
                base = info.get("publicIp") or info.get("address")
                if base and p.get("publicPort"):
                    pod_ip = f"{base}:{p.get('publicPort')}"
                    break
    if not pod_ip:
        pod_ip = f"{pod_id}-8000.proxy.runpod.net"
    if "proxy.runpod.net" in pod_ip:
        return f"https://{pod_ip}" if not pod_ip.startswith("http") else pod_ip
    if ":" in pod_ip:
        return f"http://{pod_ip}"
    return f"http://{pod_ip}:8000"


def _wait_for_running_url(pod_id: str, timeout_s: int = 600) -> str:
    """Block until pod is RUNNING and return worker base URL."""
    start = time.time()
    while True:
        info = runpod.get_pod(pod_id)
        if not info:
            if time.time() - start > 120:
                raise RuntimeError(f"Pod {pod_id} disappeared while waiting for RUNNING")
            time.sleep(5)
            continue
        status = (info.get("desiredStatus") or info.get("status") or "").upper()
        runtime = info.get("runtime") or {}
        if status in ("RUNNING",) and (runtime.get("ports") or runtime.get("gpus") or True):
            # Prefer proxy URL once desiredStatus is RUNNING; ports may lag a few seconds
            if runtime.get("ports") or time.time() - start > 30:
                url = _pod_comfy_url(pod_id, info)
                print(f"⚡ Pod {pod_id} is running → {url}")
                return url
        if status in ("EXITED", "TERMINATED", "FAILED"):
            raise RuntimeError(f"Pod {pod_id} ended with status={status}")
        if time.time() - start > timeout_s:
            raise TimeoutError(f"Pod {pod_id} did not reach RUNNING in {timeout_s}s")
        time.sleep(5)


def _try_resume_existing_pod():
    """
    Resume a stopped pod (keeps image layers on container disk).
    Set RUNPOD_POD_ID in .env, or leave empty to skip.
    """
    pod_id = (os.getenv("RUNPOD_POD_ID") or "").strip()
    if not pod_id:
        return None
    print(f"♻️ Trying to resume existing pod {pod_id}...")
    try:
        info = runpod.get_pod(pod_id)
    except Exception as e:
        print(f"⚠️ get_pod({pod_id}) failed: {e}")
        return None
    if not info:
        print(f"⚠️ Pod {pod_id} not found — will create a new one")
        return None
    status = (info.get("desiredStatus") or info.get("status") or "").upper()
    print(f"   current status={status}")
    if status in ("RUNNING",):
        url = _wait_for_running_url(pod_id)
        return pod_id, url
    if status in ("EXITED", "STOPPED", "DEAD"):
        try:
            runpod.resume_pod(pod_id, gpu_count=1)
            print(f"   resume requested for {pod_id}")
        except Exception as e:
            print(f"⚠️ resume failed ({e}) — will create a new pod")
            return None
        url = _wait_for_running_url(pod_id)
        return pod_id, url
    # Creating / other — wait a bit
    try:
        url = _wait_for_running_url(pod_id, timeout_s=180)
        return pod_id, url
    except Exception as e:
        print(f"⚠️ Could not bring {pod_id} up ({e})")
        return None


def launch_pod():
    image = "vinaie/niche-video-worker:latest"

    resumed = _try_resume_existing_pod()
    if resumed:
        return resumed

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
        # LTX-2.5 only
        "ENGINE": os.getenv("ENGINE", "ltx"),
        "HF_TOKEN": os.getenv("HF_TOKEN")
        or os.getenv("HUGGING_FACE_HUB_TOKEN")
        or os.getenv("HUGGINGFACE_TOKEN")
        or "",
        "LTX_VARIANT": os.getenv("LTX_VARIANT", "distilled"),
        "LTX_NUM_FRAMES": os.getenv("LTX_NUM_FRAMES", "97"),
        "LTX_STEPS": os.getenv("LTX_STEPS", "8"),
        "LTX_FPS": os.getenv("LTX_FPS", "24"),
        "LTX_WIDTH": os.getenv("LTX_WIDTH", "1088"),
        "LTX_HEIGHT": os.getenv("LTX_HEIGHT", "1920"),
        "KEEP_MODELS_LOADED": os.getenv("KEEP_MODELS_LOADED", "true"),
        # Triton JIT (Gemma4 TE) needs gcc; also set in rebuilt image
        "CC": "gcc",
        "CXX": "g++",
        "DEBIAN_FRONTEND": "noninteractive",
    }

    # Existing Hub image lacks gcc; override CMD to install + patch before worker.
    # Set SKIP_CC_BOOTSTRAP=true once vinaie/niche-video-worker:latest includes build-essential.
    skip_cc = (os.getenv("SKIP_CC_BOOTSTRAP") or "").strip().lower() in ("1", "true", "yes")
    docker_args = None
    if not skip_cc:
        import base64

        boot = r"""#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive CC=gcc CXX=g++
echo '🔧 Installing build-essential for Triton/Gemma4...'
apt-get update -qq
apt-get install -y -qq --no-install-recommends build-essential python3-dev
python3 - <<'PY'
from pathlib import Path
p = Path("/comfyui/comfy/text_encoders/gemma4.py")
if p.is_file():
    t = p.read_text()
    old = "freqs = (inv_exp @ pos_exp).transpose(1, 2)"
    new = (
        "freqs = torch.matmul(inv_exp.cpu().float(), pos_exp.cpu().float())"
        ".to(device=device, dtype=dtype).transpose(1, 2)"
    )
    if old in t:
        p.write_text(t.replace(old, new, 1))
        print("✅ Patched gemma4 freqs → CPU matmul")
    else:
        print("ℹ️ gemma4 freqs patch skipped (already patched or different source)")
PY
python3 /workspace/setup.py
python3 /comfyui/main.py --listen 0.0.0.0 --port 8188 --dont-upcast-attention --reserve-vram 2 &
sleep 5
exec python3 -u /workspace/handler.py
"""
        b64 = base64.b64encode(boot.encode()).decode("ascii")
        # No nested quotes — safe for RunPod GraphQL dockerArgs: "..."
        docker_args = f"bash -c 'echo {b64} | base64 -d | bash'"
        print("🔧 docker_args: apt install gcc + gemma4 patch before worker (SKIP_CC_BOOTSTRAP=true to skip)")


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
        f"   ENGINE=ltx LTX_VARIANT={env_vars.get('LTX_VARIANT')} "
        f"{env_vars.get('LTX_WIDTH')}x{env_vars.get('LTX_HEIGHT')}"
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
            # ≥64GB (Blackwell 6000): keep weights resident. 32/24GB: offload for MoE/LTX fit.
            force_offload = os.getenv("FORCE_OFFLOAD")
            if force_offload is None or force_offload.strip() == "":
                force_offload = "false" if gpu_vram >= 64 else "true"
            else:
                force_offload = force_offload.strip().lower()
            ltx_te_device = _ltx_te_device_for_vram(gpu_vram)

            try:
                container_disk = int(os.getenv("CONTAINER_DISK_GB", "40"))
            except ValueError:
                container_disk = 40

            try:
                volume_id = os.getenv("NETWORK_VOLUME_ID", "").strip()
                data_center = os.getenv("DATA_CENTER_ID", "").strip() or None
                # Network volumes require Secure Cloud. Mount path must match setup.py (/runpod-volume).
                create_kwargs = dict(
                    name=POD_NAME,
                    image_name=image,
                    gpu_type_id=gpu_type_id,
                    cloud_type=os.getenv("RUNPOD_CLOUD_TYPE", "SECURE"),
                    container_disk_in_gb=container_disk,
                    ports="8000/http",
                    volume_mount_path=os.getenv("VOLUME_MOUNT_PATH", "/runpod-volume"),
                    env={
                        **env_vars,
                        "GPU_VRAM_GB": str(gpu_vram),
                        "FORCE_OFFLOAD": force_offload,
                        "LTX_TE_DEVICE": ltx_te_device,
                    },
                )
                if docker_args:
                    create_kwargs["docker_args"] = docker_args
                if volume_id:
                    create_kwargs["network_volume_id"] = volume_id
                if data_center:
                    create_kwargs["data_center_id"] = data_center
                print(
                    f"   🔎 Trying {gpu_type_id} ({gpu_vram}GB, FORCE_OFFLOAD={force_offload}, "
                    f"LTX_TE_DEVICE={ltx_te_device}, disk={container_disk}GB, "
                    f"volume={volume_id or 'none'}, dc={data_center or 'auto'})..."
                )
                pod = runpod.create_pod(**create_kwargs)
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
    _persist_pod_id(pod_id)
    comfy_url = _wait_for_running_url(pod_id)
    return pod_id, comfy_url

def _save_render_manifest(rendered_urls, path="./temp_clips/render_manifest.json"):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(rendered_urls, f, indent=2)
    print(f"💾 Render manifest → {path}")


def wait_for_worker(comfy_url):
    print(f"⏳ Waiting for Worker API at {comfy_url} to become reachable...")
    time.sleep(30)
    try:
        max_retries = int(os.getenv("HEALTH_MAX_RETRIES", "720"))
    except ValueError:
        max_retries = 720
    for _ in range(max_retries):
        try:
            res = requests.get(f"{comfy_url}/health", timeout=10)
            if res.status_code == 200:
                health_data = res.json()
                print("✅ Worker is online and ready for jobs!")
                print(
                    f"   engine={health_data.get('engine')} "
                    f"ltx={health_data.get('ltx_version')} "
                    f"variant={health_data.get('ltx_variant')} "
                    f"{health_data.get('width')}x{health_data.get('height')} "
                    f"frames={health_data.get('num_frames')} "
                    f"fps={health_data.get('fps')}"
                )
                if "setup_log" in health_data:
                    print("\n📜 --- Worker Setup Log ---")
                    print(health_data["setup_log"])
                return
        except Exception:
            pass
        time.sleep(5)
    raise Exception("Worker failed to become reachable.")


def _build_shot_payload(vid, idx, prompt, shot_mode):
    payload = {
        "prompt": prompt,
        "video_id": vid["video_id"],
        "shot_index": idx + 1,
        "shot_mode": shot_mode,
        "chunks": vid.get("chunks", 2),
        "upscale": vid.get("upscale", True),
    }
    if "num_frames" in vid:
        payload["num_frames"] = int(vid["num_frames"])
    elif os.getenv("LTX_NUM_FRAMES"):
        payload["num_frames"] = int(os.getenv("LTX_NUM_FRAMES"))
    if "steps" in vid:
        payload["steps"] = int(vid["steps"])
    elif os.getenv("LTX_STEPS"):
        payload["steps"] = int(os.getenv("LTX_STEPS"))
    return payload


def render_video_shots(comfy_url, vid, manifest):
    """Generate every shot for one video. Returns list of R2 URLs."""
    vid_id = vid["video_id"]
    shot_mode = vid.get("shot_mode", "multi_cut")
    prompts = vid["shots"] if shot_mode == "multi_cut" else [vid["shots"][0]]
    urls = []
    n = len(prompts)
    print(f"\n🎬 Generate {vid_id} — {n} shot(s). Stitch after this short only.")

    for idx, prompt in enumerate(prompts):
        label = (
            f"{vid_id} continuous ({vid.get('chunks', 2)} chunks)"
            if shot_mode != "multi_cut"
            else f"{vid_id} - Shot {idx+1}/{n}"
        )
        print(f"🎬 Submitting {label}...")
        payload = _build_shot_payload(vid, idx, prompt, shot_mode)

        try:
            submit_url = f"{comfy_url.rstrip('/')}/render"
            res = None
            raw = None
            for attempt in range(1, 4):
                raw = requests.post(
                    submit_url,
                    json=payload,
                    timeout=60,
                    headers={"Content-Type": "application/json"},
                    allow_redirects=False,
                )
                if raw.status_code == 404:
                    submit_url = f"{comfy_url.rstrip('/')}/prompt"
                    raw = requests.post(
                        submit_url,
                        json=payload,
                        timeout=60,
                        headers={"Content-Type": "application/json"},
                        allow_redirects=False,
                    )
                if raw.status_code in (301, 302, 303, 307, 308):
                    print(
                        f"   ⚠️ Redirect on submit (attempt {attempt}/3): "
                        f"status={raw.status_code} location={raw.headers.get('Location')!r}"
                    )
                elif raw.status_code == 200 and (raw.text or "").strip():
                    try:
                        res = raw.json()
                        break
                    except Exception:
                        print(
                            f"   ⚠️ Non-JSON body (attempt {attempt}/3): "
                            f"status={raw.status_code} body={raw.text[:300]!r}"
                        )
                else:
                    print(
                        f"   ⚠️ Bad submit response (attempt {attempt}/3): "
                        f"status={raw.status_code} body={((raw.text or '')[:300])!r}"
                    )
                    try:
                        h = requests.get(f"{comfy_url}/health", timeout=10)
                        eng = (h.json() or {}).get("engine") if h.ok else "?"
                        print(f"   🩺 health={h.status_code} engine={eng}")
                    except Exception as he:
                        print(f"   🩺 health check failed: {he}")
                time.sleep(5 * attempt)

            if res is None:
                raise RuntimeError(
                    f"submit failed after retries: "
                    f"status={getattr(raw, 'status_code', None)} "
                    f"body={((getattr(raw, 'text', None) or '')[:300])!r}"
                )

            job_id = res.get("job_id")
            if not job_id:
                print(f"   ❌ Failed to get job_id: {res}")
                continue

            print(f"   🕒 Job {job_id} queued ({shot_mode}). Polling for status...")
            finished = False
            while not finished:
                time.sleep(10)
                status_raw = requests.get(f"{comfy_url}/status/{job_id}", timeout=15)
                try:
                    status_res = status_raw.json()
                except Exception:
                    print(
                        f"   ⚠️ Non-JSON /status: status={status_raw.status_code} "
                        f"body={status_raw.text[:200]!r}"
                    )
                    continue
                status = status_res.get("status")
                if status == "completed":
                    r2_url = status_res.get("output_r2_url")
                    urls.append(r2_url)
                    manifest[vid_id] = list(urls)
                    print(f"   ✅ Success! R2 URL: {r2_url}")
                    _save_render_manifest(manifest)
                    finished = True
                elif status == "failed":
                    print(f"   ❌ Job Failed: {status_res.get('error')}")
                    print("   ⏭️ Skipping this shot, continuing this short...")
                    finished = True
                else:
                    progress = status_res.get("progress", status)
                    elapsed = int(time.time() - status_res.get("created_at", time.time()))
                    print(f"   ... {progress} (elapsed: {elapsed}s)")
        except Exception as e:
            print(f"   ❌ Error on {label}: {e}")
            print("   ⏭️ Skipping this shot, continuing this short...")
            continue

    return urls


def execute_batch(comfy_url, test_jobs):
    """Per short: generate all its clips → stitch → then start the next short."""
    wait_for_worker(comfy_url)
    n_vids = len(test_jobs)
    print(
        f"\n📋 Batch plan: {n_vids} shorts — "
        f"for each: generate all shots → stitch → next short"
    )
    manifest = {}
    for i, vid in enumerate(test_jobs, start=1):
        vid_id = vid["video_id"]
        print(f"\n{'=' * 60}")
        print(f"📌 Short {i}/{n_vids}: {vid_id}")
        print(f"{'=' * 60}")
        urls = render_video_shots(comfy_url, vid, manifest)
        manifest[vid_id] = urls
        _save_render_manifest(manifest)
        if urls:
            print(f"\n🎞️ Stitching {vid_id} ({len(urls)} clips) before next short...")
            download_and_stitch({vid_id: urls}, [vid])
        else:
            print(f"⚠️ No clips for {vid_id} — skip stitch, moving on")
        if i < n_vids:
            print(f"\n➡️ Starting next short: {test_jobs[i]['video_id']}")
    print(f"\n✅ All {n_vids} shorts processed (generate→stitch per video)")
    return manifest


def download_and_stitch(rendered_urls, test_jobs):
    """Download + concat + audio/title for the given video(s)."""
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
    """Default: stop the pod (keeps image cache for resume). TERMINATE_POD=true → terminate."""
    terminate = (os.getenv("TERMINATE_POD") or "").strip().lower() in ("1", "true", "yes")
    if terminate:
        print(f"🔥 Terminating Pod {pod_id} (TERMINATE_POD=true)...")
        runpod.terminate_pod(pod_id)
        # Stale id would only fail resume — clear it
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.isfile(env_path):
            with open(env_path) as f:
                lines = [ln for ln in f.read().splitlines() if not ln.startswith("RUNPOD_POD_ID=")]
            with open(env_path, "w") as f:
                f.write("\n".join(lines) + ("\n" if lines else ""))
        os.environ.pop("RUNPOD_POD_ID", None)
        return
    print(f"🛑 Stopping Pod {pod_id} (resume next run via RUNPOD_POD_ID; TERMINATE_POD=true to destroy)...")
    try:
        runpod.stop_pod(pod_id)
    except Exception as e:
        print(f"⚠️ stop_pod failed ({e}); leaving pod as-is")
    _persist_pod_id(pod_id)


def _channel_mode():
    ch = os.getenv("CHANNEL", "a").strip().lower()
    if ch in ("b", "science", "sci", "threshold", "threshold_physics"):
        return "b"
    return "a"


def _filter_jobs_by_video_id(jobs):
    raw = (os.getenv("VIDEO_ID") or os.getenv("SCIENCE_ONLY") or "").strip()
    if not raw:
        return jobs
    picked = [j for j in jobs if j.get("video_id") == raw]
    if not picked:
        ids = ", ".join(j.get("video_id", "?") for j in jobs)
        raise SystemExit(f"VIDEO_ID={raw!r} not in batch. Available: {ids}")
    return picked


def _jobs_for_engine(engine):
    from test_prompts import ltx_ab_jobs, science_ltx_jobs

    eng = (engine or "ltx").strip().lower()
    if eng in ("compare", "ab", "all", "wan", "hunyuan", "hy"):
        print(f"⚠️ ENGINE={eng} ignored — LTX-2.5 only; using ltx")
        eng = "ltx"
    elif eng not in ("ltx", "ltx2", "ltx23", "ltx25", "ltxv", "lightricks"):
        eng = "ltx"

    if _channel_mode() == "b":
        return "ltx", _filter_jobs_by_video_id(science_ltx_jobs)
    return "ltx", ltx_ab_jobs


def run_one_engine(engine):
    """Launch/resume pod → render → stop (or terminate if TERMINATE_POD=true)."""
    eng, jobs = _jobs_for_engine(engine)
    os.environ["ENGINE"] = eng
    ch = _channel_mode()
    print(
        f"🧪 CHANNEL={ch} engine={eng} | jobs={[j['video_id'] for j in jobs]}"
    )

    pod_id = None
    try:
        pod_id, comfy_url = launch_pod()
        execute_batch(comfy_url, jobs)
    except Exception as e:
        print(f"❌ Batch Execution Failed ({eng}): {e}")
        raise
    finally:
        if pod_id:
            destroy_pod(pod_id)


if __name__ == "__main__":
    engine = os.getenv("ENGINE", "ltx").strip().lower()
    run_one_engine(engine)
