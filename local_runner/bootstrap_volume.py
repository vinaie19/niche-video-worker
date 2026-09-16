#!/usr/bin/env python3
"""
Download LTX-2.5 model weights onto an existing RunPod network volume using a cheap GPU.

Does NOT create volumes — set NETWORK_VOLUME_ID in local_runner/.env first
(e.g. your Storage-page / global volume id).

Accept the gated license on https://huggingface.co/Lightricks/LTX-2.5 and put
HF_TOKEN in local_runner/.env before bootstrap.

  ENGINE=ltx LTX_VARIANT=distilled \\
    .venv/bin/python local_runner/bootstrap_volume.py

Then destroy the cheap pod (default) and later render on PRO 6000:

  CHANNEL=b ENGINE=ltx VIDEO_ID=sci_ep01_sun_closer \\
    RUNPOD_GPU_TYPE='NVIDIA RTX PRO 6000 Blackwell Server Edition' \\
    .venv/bin/python local_runner/run_test_batch.py
"""

from __future__ import annotations

import os
import sys
import time

import requests
import runpod
from dotenv import load_dotenv

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
load_dotenv(os.path.join(_HERE, ".env"))
load_dotenv(os.path.join(_ROOT, ".env"))

runpod.api_key = os.getenv("RUNPOD_API_KEY")
if not runpod.api_key:
    sys.exit("RUNPOD_API_KEY missing — put it in local_runner/.env")

IMAGE = os.getenv("RUNPOD_IMAGE", "vinaie/niche-video-worker:latest")
VOLUME_MOUNT = os.getenv("VOLUME_MOUNT_PATH", "/runpod-volume")

DEFAULT_CHEAP_GPUS = [
    "NVIDIA RTX A2000",
    "NVIDIA RTX 2000 Ada Generation",
    "NVIDIA RTX A4000",
    "NVIDIA GeForce RTX 3070",
    "NVIDIA GeForce RTX 3080",
    "NVIDIA RTX 4000 Ada Generation",
    "NVIDIA GeForce RTX 4090",
]


def _cheap_gpu_list():
    raw = os.getenv("DOWNLOAD_GPU_TYPES", "").strip()
    if raw:
        return [g.strip() for g in raw.split(",") if g.strip()]
    return list(DEFAULT_CHEAP_GPUS)


def resolve_volume() -> tuple[str, str | None]:
    volume_id = os.getenv("NETWORK_VOLUME_ID", "").strip()
    if not volume_id:
        sys.exit(
            "NETWORK_VOLUME_ID is required. Paste your Storage-page volume id into "
            "local_runner/.env (do not rely on auto-create)."
        )
    data_center = os.getenv("DATA_CENTER_ID", "").strip() or None

    # Prefer DC from traditional networkVolumes list when the id is known there
    try:
        from runpod.api.graphql import run_graphql_query

        r = run_graphql_query(
            "query { myself { networkVolumes { id name size dataCenterId } } }"
        )
        for v in r["data"]["myself"]["networkVolumes"] or []:
            if v["id"] == volume_id:
                data_center = v.get("dataCenterId") or data_center
                print(
                    f"✅ Volume {volume_id} ({v.get('name')}, {v.get('size')}GB @ {data_center})"
                )
                return volume_id, data_center
    except Exception as e:
        print(f"⚠️ Could not list traditional networkVolumes: {e}")

    print(
        f"ℹ️ Using NETWORK_VOLUME_ID={volume_id} "
        f"(not in traditional networkVolumes list — treating as Storage/global volume)"
    )
    if data_center:
        print(f"   DATA_CENTER_ID={data_center}")
    else:
        print(
            "   No DATA_CENTER_ID set — Secure Cloud attach may fail; "
            "set DATA_CENTER_ID to the volume's region in .env"
        )
    return volume_id, data_center


def launch_download_pod(volume_id: str, data_center: str | None) -> tuple[str, str]:
    try:
        container_disk = int(os.getenv("CONTAINER_DISK_GB", "20"))
    except ValueError:
        container_disk = 20

    env_vars = {
        "ENGINE": "ltx",
        "LTX_VARIANT": os.getenv("LTX_VARIANT", "distilled"),
        "HF_TOKEN": os.getenv("HF_TOKEN")
        or os.getenv("HUGGING_FACE_HUB_TOKEN")
        or os.getenv("HUGGINGFACE_TOKEN")
        or "",
        "R2_ACCOUNT_ID": os.getenv("R2_ACCOUNT_ID", ""),
        "R2_ACCESS_KEY_ID": os.getenv("R2_ACCESS_KEY_ID", ""),
        "R2_SECRET_ACCESS_KEY": os.getenv("R2_SECRET_ACCESS_KEY", ""),
        "R2_BUCKET_NAME": os.getenv("R2_BUCKET_NAME", ""),
        "R2_PUBLIC_URL_PREFIX": os.getenv("R2_PUBLIC_URL_PREFIX", ""),
        "FORCE_OFFLOAD": "true",
        "LTX_TE_DEVICE": "cpu",
        "GPU_VRAM_GB": "16",
        "KEEP_MODELS_LOADED": "",
    }
    if not env_vars["HF_TOKEN"]:
        print(
            "⚠️ HF_TOKEN missing — gated LTX-2.5 downloads will fail. "
            "Accept the license on Hugging Face and set HF_TOKEN in .env"
        )

    ordered = _cheap_gpu_list()
    print(f"🚀 Download pod | ENGINE=ltx | volume={volume_id} | mount={VOLUME_MOUNT}")
    print(f"   Cheap GPU order: {ordered}")

    pod = None
    last_error = None
    gpu_used = None
    try:
        max_acquire = int(os.getenv("POD_ACQUIRE_RETRIES", "0"))
    except ValueError:
        max_acquire = 0
    try:
        acquire_sleep = int(os.getenv("POD_ACQUIRE_SLEEP_S", "30"))
    except ValueError:
        acquire_sleep = 30

    attempt = 0
    while pod is None:
        attempt += 1
        if max_acquire > 0 and attempt > max_acquire:
            break
        print(f"🔁 Acquire pass {attempt}...")
        for gpu_type_id in ordered:
            print(f"   🔎 Trying {gpu_type_id}...")
            try:
                kwargs = dict(
                    name="model-download-ltx25",
                    image_name=IMAGE,
                    gpu_type_id=gpu_type_id,
                    cloud_type=os.getenv("RUNPOD_CLOUD_TYPE", "SECURE"),
                    container_disk_in_gb=container_disk,
                    volume_in_gb=0,
                    ports="8000/http",
                    network_volume_id=volume_id,
                    volume_mount_path=VOLUME_MOUNT,
                    env=env_vars,
                )
                if data_center:
                    kwargs["data_center_id"] = data_center
                pod = runpod.create_pod(**kwargs)
                gpu_used = gpu_type_id
                print(f"   ✅ Acquired {gpu_type_id}")
                break
            except Exception as e:
                last_error = e
                print(f"   ⚠️ Unavailable: {e}")
                pod = None
        if pod is None:
            print(f"⏳ Sleeping {acquire_sleep}s...")
            time.sleep(acquire_sleep)

    if not pod:
        raise SystemExit(f"No cheap GPU available. Last error: {last_error}")

    pod_id = pod["id"]
    print(f"📡 Pod {pod_id} on {gpu_used} — waiting for RUNNING...")

    start = time.time()
    comfy_url = None
    while True:
        info = runpod.get_pod(pod_id)
        if not info:
            print(f"⚠️ get_pod({pod_id}) returned empty — pod may have died")
            time.sleep(8)
            if time.time() - start > 180:
                raise SystemExit(f"Pod {pod_id} disappeared before RUNNING")
            continue
        status = info.get("desiredStatus") or info.get("status")
        runtime = info.get("runtime") or {}
        if int(time.time() - start) % 30 < 9:
            print(f"   pod status={status} runtime={bool(runtime)}")
        if status in ("RUNNING", "running"):
            pod_ip = f"{pod_id}-8000.proxy.runpod.net"
            if runtime.get("ports"):
                for p in runtime["ports"]:
                    if p.get("privatePort") == 8000 and info.get("publicIp"):
                        pod_ip = f"{info['publicIp']}:{p.get('publicPort')}"
                        break
            if "proxy.runpod.net" in pod_ip:
                comfy_url = f"https://{pod_ip}"
            else:
                comfy_url = f"http://{pod_ip}"
            print(f"⚡ Running → {comfy_url}")
            break
        if status in ("EXITED", "TERMINATED", "FAILED"):
            raise SystemExit(f"Pod {pod_id} ended early with status={status}")
        if time.time() - start > 600:
            raise SystemExit("Pod did not reach RUNNING in 10 minutes")
        time.sleep(8)

    return pod_id, comfy_url


def wait_for_download(comfy_url: str, pod_id: str | None = None) -> dict:
    """/health is only up after setup.py finishes — that means downloads are done."""
    print(f"⏳ Waiting for boot+download (ENGINE=ltx / LTX-2.5) at {comfy_url}/health ...")
    print("   LTX-2.5 ~39GB may take 15–40+ min (gated HF; needs HF_TOKEN)")

    try:
        max_retries = int(os.getenv("DOWNLOAD_MAX_RETRIES", "1200"))
    except ValueError:
        max_retries = 1200

    for i in range(max_retries):
        if pod_id and i % 12 == 0:
            info = runpod.get_pod(pod_id)
            if not info:
                raise SystemExit(f"Pod {pod_id} disappeared during download")
            st = info.get("desiredStatus") or info.get("status")
            print(f"   pod still {st} | waiting ({i * 5 // 60}m)")
            if st in ("EXITED", "TERMINATED", "FAILED"):
                raise SystemExit(f"Pod {pod_id} died during download: {st}")
        try:
            res = requests.get(f"{comfy_url}/health", timeout=15)
            if res.status_code == 200:
                data = res.json()
                print("\n✅ Worker online — setup.py finished (models on volume)")
                print(
                    f"   engine={data.get('engine')} "
                    f"ltx_version={data.get('ltx_version')} "
                    f"ltx_variant={data.get('ltx_variant')} "
                    f"{data.get('width')}x{data.get('height')} "
                    f"vram={data.get('vram_gb')}"
                )
                return data
            if i % 12 == 0:
                print(f"   health HTTP {res.status_code} ({i * 5 // 60}m)")
        except Exception as e:
            if i % 12 == 0:
                print(f"   still booting/downloading... ({i * 5 // 60}m) {e}")
        time.sleep(5)

    raise SystemExit("Timed out waiting for model download / health")


def main():
    volume_id, data_center = resolve_volume()
    pod_id = None
    try:
        pod_id, comfy_url = launch_download_pod(volume_id, data_center)
        health = wait_for_download(comfy_url, pod_id=pod_id)
        log = health.get("setup_log") or ""
        print("\n📜 --- setup.log (tail) ---")
        print("\n".join(log.strip().splitlines()[-40:]))
        print("\n🎉 Volume bootstrap complete.")
        print(f"   NETWORK_VOLUME_ID={volume_id}")
    finally:
        if pod_id and os.getenv("KEEP_POD", "").lower() not in ("1", "true", "yes"):
            print(f"🔥 Terminating download pod {pod_id}...")
            try:
                runpod.terminate_pod(pod_id)
                print("✅ Download pod destroyed (models remain on network volume)")
            except Exception as e:
                print(f"⚠️ terminate failed: {e} — kill {pod_id} in the RunPod console")
        elif pod_id:
            print(f"KEEP_POD set — leaving {pod_id} running")


if __name__ == "__main__":
    main()
