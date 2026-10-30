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
    # Blackwell RTX PRO 6000 ONLY (96GB). Deliberately narrow: an A100 80GB was
    # acquired once as a fallback and took 10+ min for a single shot versus ~3-5
    # on a Blackwell, and the 48GB cards drop to FORCE_OFFLOAD=true + CPU text
    # encode, which is slower still. Waiting for a Blackwell beats winning a slow
    # card — the acquire loop retries forever, so scarcity costs time, not money.
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


def _launch_pod_global(image, env_vars, docker_args):
    """GLOBAL_VOLUME_ID set: create the pod through REST API v2 with the global volume mounted
    at /runpod-volume, in whichever data center has the GPU. No pinning to the network volume's
    data center, so GPU stock across regions is usable. Candidates come from the live catalog,
    cheapest first, restricted to GLOBAL_GPU_IDS (comma list) and >= GLOBAL_MIN_VRAM_GB."""
    import runpod_v2 as v2

    gvid = os.environ["GLOBAL_VOLUME_ID"].strip()
    allowed = [g.strip() for g in os.getenv("GLOBAL_GPU_IDS", "").split(",") if g.strip()]
    min_vram = int(os.getenv("GLOBAL_MIN_VRAM_GB", "80"))
    avoid = {d.strip() for d in os.getenv("GLOBAL_AVOID_DCS", "").split(",") if d.strip()}
    max_acquire = int(os.getenv("POD_ACQUIRE_RETRIES", "0") or 0)
    acquire_sleep = int(os.getenv("POD_ACQUIRE_SLEEP_S", "45") or 45)
    attempt = 0
    while True:
        attempt += 1
        code, cat = v2.call("GET", "/v2/catalog/gpus", params={"include": "AVAILABILITY", "product": "POD"})
        gpus = cat.get("gpus", []) if code == 200 else []
        cands = []
        for g in gpus:
            if not g.get("secure") or g.get("availability") == "NONE" or (g.get("memory") or 0) < min_vram:
                continue
            if allowed and g["id"] not in allowed:
                continue
            if not any(c.get("available") and c["version"].startswith("13.") for c in g.get("cudaVersions", [])):
                continue  # image is built on CUDA 13 (cu130 torch)
            for dc in g.get("dataCenters", []):
                if dc["id"] not in avoid:
                    cands.append((g["price"].get("secure") or 99, g["id"], g.get("memory"), dc["id"]))
        cands.sort()
        print(f"🔁 Global-volume acquire pass {attempt}: {len(cands)} (gpu, dc) candidates")
        for price, gpu_id, vram, dc in cands:
            force_offload = "false" if (vram or 0) >= 64 else "true"
            body = {
                "name": POD_NAME, "image": image, "cloud": "SECURE",
                "gpu": {"id": gpu_id, "count": 1, "minCudaVersion": "13.0"},
                "dataCenterIds": [dc],
                "disk": int(os.getenv("CONTAINER_DISK_GB", "40")),
                "ports": ["8000/http"],
                "env": {k: v for k, v in {**env_vars, "GPU_VRAM_GB": str(vram), "FORCE_OFFLOAD": force_offload,
                                          "LTX_TE_DEVICE": _ltx_te_device_for_vram(vram)}.items() if v is not None},
                "mounts": {"global": [{"volumeId": gvid, "path": "/runpod-volume"}]},
            }
            if docker_args:
                body["args"] = docker_args
            print(f"   🔎 Trying {gpu_id} ({vram}GB, ${price}/h) in {dc} with global volume {gvid}...")
            code, pod = v2.call("POST", "/v2/pods", body)
            if code == 201:
                print(f"   ✅ Acquired {gpu_id} in {dc}")
                pod_id = pod["id"]
                _persist_pod_id(pod_id)
                return pod_id, _wait_for_running_url(pod_id)
            print(f"   ⚠️ {code}: {pod.get('detail') if isinstance(pod, dict) else pod}")
            if code == 422:
                raise SystemExit(f"Pod request rejected: {pod}")
        if max_acquire > 0 and attempt >= max_acquire:
            raise Exception("No GPU placed with the global volume")
        print(f"⏳ No GPU this pass — sleeping {acquire_sleep}s then retrying (Ctrl+C to stop)...")
        time.sleep(acquire_sleep)


def launch_pod():
    image = "vinaie/niche-video-worker:latest"
    use_global = bool(os.getenv("GLOBAL_VOLUME_ID", "").strip())

    # A saved pod is pinned to the network volume's data center; global mode always places fresh.
    resumed = None if use_global else _try_resume_existing_pod()
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


    if use_global:
        return _launch_pod_global(image, env_vars, docker_args)

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

def _env_flag(name):
    return (os.getenv(name) or "").strip().lower() in ("1", "true", "yes")


def _only_shot():
    """ONLY_SHOT / SHOT_INDEX = 1-based shot to re-render alone (None = all shots)."""
    raw = (os.getenv("ONLY_SHOT") or os.getenv("SHOT_INDEX") or "").strip()
    if not raw:
        return None
    try:
        n = int(raw)
    except ValueError:
        raise SystemExit(f"ONLY_SHOT/SHOT_INDEX must be a 1-based int, got {raw!r}")
    if n < 1:
        raise SystemExit(f"ONLY_SHOT/SHOT_INDEX must be >= 1, got {n}")
    return n


def _missing_shot_indices(vid):
    """MISSING_SHOTS_ONLY=1 → 0-based indices of shots with no temp_clips/{vid}_shot_N.mp4
    yet (None when the flag is off). Lets approved local shots survive a full run."""
    if not _env_flag("MISSING_SHOTS_ONLY"):
        return None
    n = len(vid["shots"])
    return [i for i in range(n) if not os.path.isfile(f"./temp_clips/{vid['video_id']}_shot_{i + 1}.mp4")]


def _save_render_manifest(rendered_urls, path=None):
    # Single-shot re-renders get their own manifest so the full-run one is not clobbered.
    if path is None:
        only = _only_shot()
        path = (
            f"./temp_clips/render_manifest_shot_{only}.json"
            if only
            else "./temp_clips/render_manifest.json"
        )
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


def _normalize_shot_entry(shot):
    """Accept a prompt string or {prompt|shot, num_frames?, steps?, chunks?, upscale?, start_image?, start_image_url?, negative_prompt?}."""
    if isinstance(shot, dict):
        prompt = (shot.get("prompt") or shot.get("shot") or "").strip()
        if not prompt:
            raise ValueError(f"shot dict missing prompt/shot text: {shot!r}")
        meta = {
            "prompt": prompt,
            "num_frames": shot.get("num_frames"),
            "steps": shot.get("steps"),
            "chunks": shot.get("chunks"),
            "upscale": shot.get("upscale"),
            "start_image": shot.get("start_image"),
            "start_image_url": shot.get("start_image_url"),
            "negative_prompt": shot.get("negative_prompt"),
        }
        return meta
    return {
        "prompt": str(shot),
        "num_frames": None,
        "steps": None,
        "chunks": None,
        "upscale": None,
        "start_image": None,
        "start_image_url": None,
        "negative_prompt": None,
    }


def _upload_start_image(local_path, video_id, shot_index):
    """Upload a local I2V first frame to R2 under stills/<video_id>/shot_N.png. Returns the public URL."""
    if not os.path.isfile(local_path):
        raise FileNotFoundError(f"start_image not found: {local_path}")
    ext = os.path.splitext(local_path)[1] or ".png"
    r2_key = f"stills/{video_id}/shot_{shot_index}{ext}"
    s3_client.upload_file(local_path, os.getenv("R2_BUCKET_NAME"), r2_key)
    url = f"{os.getenv('R2_PUBLIC_URL_PREFIX')}/{r2_key}"
    print(f"🖼️ Uploaded start image {local_path} → {url}")
    return url


def _build_shot_payload(vid, idx, shot, shot_mode, join_style=None, override_prompt=None, override_frames=None):
    entry = _normalize_shot_entry(shot)
    payload = {
        "prompt": override_prompt if override_prompt is not None else entry["prompt"],
        "video_id": vid["video_id"],
        "shot_index": idx + 1,
        "shot_mode": shot_mode,
        "chunks": entry["chunks"] if entry["chunks"] is not None else vid.get("chunks", 2),
        "upscale": entry["upscale"] if entry["upscale"] is not None else vid.get("upscale", True),
    }
    if entry["start_image_url"]:
        payload["start_image_url"] = entry["start_image_url"]
    elif entry["start_image"]:
        payload["start_image_url"] = _upload_start_image(
            entry["start_image"], vid["video_id"], idx + 1
        )
    if join_style:
        payload["join_style"] = join_style
    # Per-shot num_frames wins over job/env default (LTX uses 8k+1 frame grid).
    if override_frames is not None:
        payload["num_frames"] = int(override_frames)
    elif entry["num_frames"] is not None:
        payload["num_frames"] = int(entry["num_frames"])
    elif "num_frames" in vid:
        payload["num_frames"] = int(vid["num_frames"])
    elif os.getenv("LTX_NUM_FRAMES"):
        payload["num_frames"] = int(os.getenv("LTX_NUM_FRAMES"))
    if entry["steps"] is not None:
        payload["steps"] = int(entry["steps"])
    elif "steps" in vid:
        payload["steps"] = int(vid["steps"])
    elif os.getenv("LTX_STEPS"):
        payload["steps"] = int(os.getenv("LTX_STEPS"))
    # Optional per-shot negative prompt
    if entry.get("negative_prompt"):
        payload["negative_prompt"] = entry["negative_prompt"]
    elif vid.get("negative_prompt"):
        payload["negative_prompt"] = vid["negative_prompt"]
    return payload


def _nearest_ltx_frames(n):
    """Match handler 8k+1 grid (local, so we don't under-request multishot length)."""
    n = max(17, int(n))
    k = max(2, round((n - 1) / 8))
    return 8 * k + 1


def render_video_shots(comfy_url, vid, manifest, indices=None):
    """Generate every shot for one video (or only `indices`, 0-based). Returns list of R2 URLs."""
    from ltx_multishot import (
        build_multishot_prompt,
        is_multishot_mode,
        normalize_join_style,
        sum_shot_frames,
    )

    vid_id = vid["video_id"]
    shot_mode = vid.get("shot_mode", "multi_cut")
    join_style = normalize_join_style(vid.get("join_style"), shot_mode)
    urls = []

    only = _only_shot()
    if only and is_multishot_mode(shot_mode):
        raise SystemExit(
            f"ONLY_SHOT={only} not supported for {vid_id} shot_mode={shot_mode} (one-pass multishot)"
        )

    if is_multishot_mode(shot_mode):
        # One native AV pass: chronological cut|continue prompt, continuous bed.
        shots = list(vid["shots"])
        prompt = build_multishot_prompt(shots, join_style=join_style)
        total_frames = _nearest_ltx_frames(
            sum_shot_frames(shots, default_frames=vid.get("num_frames", 97))
        )
        print(
            f"\n🎬 Generate {vid_id} — LTX multishot join={join_style} "
            f"({len(shots)} beats → {total_frames} frames, one pass)."
        )
        print(f"🎬 Submitting {vid_id} multishot ({join_style})...")
        payload = _build_shot_payload(
            vid,
            0,
            shots[0],
            shot_mode="ltx_multishot",
            join_style=join_style,
            override_prompt=prompt,
            override_frames=total_frames,
        )
        url = _submit_and_poll_shot(comfy_url, payload, vid_id, manifest, label=f"{vid_id} multishot")
        if url:
            urls.append(url)
        return urls

    prompts = vid["shots"]
    n = len(prompts)
    if indices is not None:
        indices = list(indices)
        print(
            f"\n🧩 MISSING_SHOTS_ONLY: rendering {vid_id} shots {[i + 1 for i in indices]} of {n} "
            f"(keeping local {[i + 1 for i in range(n) if i not in indices]})"
        )
    elif only:
        if only > n:
            raise SystemExit(f"ONLY_SHOT={only} out of range for {vid_id} ({n} shots)")
        indices = [only - 1]
        print(
            f"\n🎯 ONLY_SHOT={only}: rendering {vid_id} shot {only}/{n} ONLY "
            f"(skipping shots {[i + 1 for i in range(n) if i != only - 1]})"
        )
    else:
        indices = range(n)
        print(f"\n🎬 Generate {vid_id} — {n} shot(s). Stitch after this short only.")

    for idx in indices:
        prompt = prompts[idx]
        entry = _normalize_shot_entry(prompt)
        frames_note = (
            f" frames={entry['num_frames']}"
            if entry.get("num_frames") is not None
            else ""
        )
        label = f"{vid_id} - Shot {idx+1}/{n}{frames_note}"
        print(f"🎬 Submitting {label}...")
        payload = _build_shot_payload(vid, idx, prompt, shot_mode)
        url = _submit_and_poll_shot(comfy_url, payload, vid_id, manifest, label=label)
        if url:
            urls.append(url)
    return urls


def _submit_and_poll_shot(comfy_url, payload, vid_id, manifest, label=""):
    """POST one render job and poll until R2 URL is ready. Returns URL or None."""
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
                        f"   ⚠️ Non-JSON submit body (attempt {attempt}/3): "
                        f"status={raw.status_code} body={raw.text[:200]!r}"
                    )
            else:
                print(
                    f"   ⚠️ Submit failed (attempt {attempt}/3): "
                    f"status={raw.status_code} body={(raw.text or '')[:200]!r}"
                )
            time.sleep(2 * attempt)
        else:
            raise RuntimeError(
                f"Empty/invalid submit response after retries "
                f"(last status={getattr(raw, 'status_code', None)})"
            )

        job_id = res["job_id"]
        print(f"   🕒 Job {job_id} queued ({payload.get('shot_mode')}). Polling for status...")

        poll_s = int(os.getenv("POLL_INTERVAL_S", "10"))
        max_polls = int(os.getenv("MAX_POLLS", "720"))
        for poll_i in range(max_polls):
            time.sleep(poll_s)
            st = requests.get(f"{comfy_url.rstrip('/')}/status/{job_id}", timeout=30)
            data = st.json()
            status = data.get("status")
            if status == "completed":
                url = data.get("output_r2_url")
                print(f"   ✅ {label or vid_id} ready: {url}")
                manifest.setdefault(vid_id, []).append(url)
                _save_render_manifest(manifest)
                return url
            if status == "failed":
                err = data.get("error", "unknown")
                print(f"   ❌ Job failed: {err}")
                return None
            if poll_i % 6 == 0:
                print(f"   … still {status} ({poll_i * poll_s}s)")
        print(f"   ⚠️ Timed out polling {job_id}")
        return None
    except Exception as e:
        print(f"   💥 Submit/poll error for {label or vid_id}: {e}")
        return None


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
        missing = None if _only_shot() else _missing_shot_indices(vid)
        urls = render_video_shots(comfy_url, vid, manifest, indices=missing)
        manifest[vid_id] = urls
        _save_render_manifest(manifest)
        only = _only_shot()
        if missing is not None:
            _finish_missing_shots(vid, missing, urls)
        elif only:
            _finish_only_shot(vid, only, urls)
        elif urls:
            print(f"\n🎞️ Stitching {vid_id} ({len(urls)} clips) before next short...")
            download_and_stitch({vid_id: urls}, [vid])
        else:
            print(f"⚠️ No clips for {vid_id} — skip stitch, moving on")
        if i < n_vids:
            print(f"\n➡️ Starting next short: {test_jobs[i]['video_id']}")
    print(f"\n✅ All {n_vids} shorts processed (generate→stitch per video)")
    return manifest


def _finish_missing_shots(vid, missing, urls):
    """Save newly rendered clips as temp_clips/{vid}_shot_{N}.mp4, then stitch all local shots."""
    vid_id = vid["video_id"]
    if len(urls) != len(missing):
        print(f"⚠️ MISSING_SHOTS_ONLY: got {len(urls)} clip(s) for {len(missing)} shot(s) — skip stitch")
        return
    os.makedirs("./temp_clips", exist_ok=True)
    for idx, url in zip(missing, urls):
        path = f"./temp_clips/{vid_id}_shot_{idx + 1}.mp4"
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"⬇️ MISSING_SHOTS_ONLY: saved {path}")
    local_paths = [f"./temp_clips/{vid_id}_shot_{i}.mp4" for i in range(1, len(vid["shots"]) + 1)]
    print(f"\n🎞️ Stitching {vid_id} from local shots 1..{len(local_paths)}...")
    download_and_stitch({vid_id: local_paths}, [vid], local=True)


def _finish_only_shot(vid, only, urls):
    """Save the re-rendered clip as temp_clips/{vid}_shot_{N}.mp4 (old one → .prev.mp4).
    Stitch is skipped unless RESTITCH_LOCAL=1, which concats the existing local
    shot_1..N clips (with the new one in place) through the normal VO/audio path."""
    vid_id = vid["video_id"]
    if not urls:
        print(f"⚠️ ONLY_SHOT={only}: no clip for {vid_id} — existing local clips untouched")
        return
    os.makedirs("./temp_clips", exist_ok=True)
    path = f"./temp_clips/{vid_id}_shot_{only}.mp4"
    if os.path.isfile(path):
        prev = f"./temp_clips/{vid_id}_shot_{only}.prev.mp4"
        os.replace(path, prev)
        print(f"📦 Backed up old shot {only} → {prev}")
    r = requests.get(urls[0], stream=True)
    r.raise_for_status()
    with open(path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"⬇️ ONLY_SHOT={only}: saved {path}")

    if not _env_flag("RESTITCH_LOCAL") or _env_flag("SKIP_STITCH"):
        print(f"⏭️ ONLY_SHOT set → skip stitch (RESTITCH_LOCAL=1 to rebuild final from local clips)")
        return
    n = len(vid["shots"])
    local_paths = [f"./temp_clips/{vid_id}_shot_{i}.mp4" for i in range(1, n + 1)]
    missing = [p for p in local_paths if not os.path.isfile(p)]
    if missing:
        print(f"⚠️ RESTITCH_LOCAL: missing local clips {missing} — skip stitch")
        return
    print(f"\n🎞️ RESTITCH_LOCAL: stitching {vid_id} from local shots 1..{n} (new shot {only})...")
    download_and_stitch({vid_id: local_paths}, [vid], local=True)


def download_and_stitch(rendered_urls, test_jobs, local=False):
    """Download + concat + audio/title for the given video(s).
    local=True: rendered_urls values are existing local shot paths (no download)."""
    from audio_post import add_ambient_and_title, add_voice_and_captions
    from ltx_multishot import is_multishot_mode

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
        script_beats = job.get("script_beats")
        silent_path = f"./temp_clips/{vid_id}_silent.mp4"
        output_video = f"./final_videos/{vid_id}_complete.mp4"

        # One-pass multishot / continuous already returns a single AV clip.
        if not local and (is_multishot_mode(mode_by_id.get(vid_id)) or len(urls) == 1):
            r = requests.get(urls[0], stream=True)
            with open(silent_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"⬇️ One-pass clip (keep LTX AV): {silent_path}")
        else:
            local_paths = list(urls) if local else []
            for idx, url in enumerate([] if local else urls):
                path = f"./temp_clips/{vid_id}_shot_{idx+1}.mp4"
                r = requests.get(url, stream=True)
                with open(path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                local_paths.append(path)

            # Align hard cuts to VO beat windows (stretch/trim) when beats exist.
            # Soft crossfade between shots (Channel B default 0.35s).
            crossfade_s = float(job.get("crossfade_s", 0.35))
            if script_beats and len(local_paths) > 1:
                from audio_post import concat_clips_crossfade, fit_shots_to_voice_beats

                audio_dir = f"./temp_clips/{vid_id}_audio"
                local_paths = fit_shots_to_voice_beats(
                    local_paths,
                    script_beats,
                    work_dir=audio_dir,
                    voice_stem=f"{vid_id}_complete_voice",
                    vo_delay_ms=int(job.get("vo_delay_ms", 500)),
                    voice=job.get("voice"),
                    voice_rate=job.get("voice_rate"),
                    voice_pitch=job.get("voice_pitch"),
                    crossfade_s=crossfade_s if crossfade_s > 0 else 0.0,
                )
                if crossfade_s > 0:
                    concat_clips_crossfade(
                        local_paths,
                        silent_path,
                        fade_s=crossfade_s,
                    )
                else:
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
            else:
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
            print(f"⬇️ Stitched video: {silent_path}")

        if script or script_beats:
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
                script_beats = job.get("script_beats")
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
                    voice_rate=job.get("voice_rate"),
                    voice_pitch=job.get("voice_pitch"),
                    script_beats=script_beats,
                    caption_chunk_words=job.get("caption_chunk_words"),
                    caption_phrases=job.get("caption_phrases"),
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
    return "ltx", _filter_jobs_by_video_id(ltx_ab_jobs)


def run_one_engine(engine):
    """Launch/resume pod → render → stop (or terminate if TERMINATE_POD=true)."""
    eng, jobs = _jobs_for_engine(engine)
    os.environ["ENGINE"] = eng
    ch = _channel_mode()
    print(
        f"🧪 CHANNEL={ch} engine={eng} | jobs={[j['video_id'] for j in jobs]}"
    )
    only = _only_shot()
    if only:
        stitch = "RESTITCH_LOCAL (local shots 1..N)" if _env_flag("RESTITCH_LOCAL") and not _env_flag("SKIP_STITCH") else "SKIP"
        print(f"🎯 ONLY_SHOT={only} → render shot {only} only; stitch={stitch}")

    if not only and _env_flag("MISSING_SHOTS_ONLY"):
        todo = {j["video_id"]: _missing_shot_indices(j) for j in jobs}
        print(f"🧩 MISSING_SHOTS_ONLY → shots to render: { {v: [i + 1 for i in m] for v, m in todo.items()} }")
        if not any(todo.values()):
            # Nothing to render: stitch from local clips and never start (or pay for) a pod.
            for j in jobs:
                _finish_missing_shots(j, [], [])
            return

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
