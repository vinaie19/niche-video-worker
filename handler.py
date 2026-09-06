import os
import time
import json
import requests
import boto3
import shutil
import threading
import uuid
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

# Cloudflare R2 Client Init
s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
    aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
)

jobs = {}

# Wan VAE requires temporal length 4k+1 (e.g. 17, 33, 49, 65, 81)
VALID_FRAME_COUNTS = {17, 33, 49, 65, 81, 97, 113, 129}
COMFY_HEADERS = {"Host": "127.0.0.1"}
COMFY_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = "/comfyui/output"
INPUT_DIR = "/comfyui/input"
WORK_DIR = "/workspace/continuous_work"


def sageattn_available():
    """Only enable sageattn when the package imports cleanly on this runtime."""
    try:
        import sageattention  # noqa: F401

        print("✅ SageAttention import OK — will use attention_mode=sageattn")
        return True
    except Exception as e:
        print(f"ℹ️ SageAttention unavailable ({e}); defaulting to sdpa")
        return False


def nearest_valid_frames(n):
    """Clamp/snap frame counts to Wan's 4k+1 rule."""
    if n in VALID_FRAME_COUNTS:
        return n
    return min(VALID_FRAME_COUNTS, key=lambda v: abs(v - n))


def detect_vram_gb():
    """Prefer env from launcher; fall back to live CUDA query."""
    env_vram = os.getenv("GPU_VRAM_GB")
    if env_vram:
        try:
            return float(env_vram)
        except ValueError:
            pass
    try:
        import torch

        if torch.cuda.is_available():
            return torch.cuda.get_device_properties(0).total_memory / (1024**3)
    except Exception:
        pass
    return 32.0


def should_force_offload(vram_gb=None):
    """24GB cards need offload for Wan 14B + UltraSharp; 32GB+ can stay resident."""
    flag = os.getenv("FORCE_OFFLOAD", "").lower()
    if flag in ("true", "1", "yes"):
        return True
    if flag in ("false", "0", "no"):
        return False
    if vram_gb is None:
        vram_gb = detect_vram_gb()
    return vram_gb <= 26


def wait_for_comfyui():
    """Polls internal ComfyUI instance until active."""
    print("⏳ Waiting for internal ComfyUI engine...")
    while True:
        try:
            res = requests.get(f"{COMFY_URL}/system_stats", timeout=2, headers=COMFY_HEADERS)
            if res.status_code == 200:
                print("✅ ComfyUI is online and operational!")
                break
        except Exception:
            time.sleep(2)


def model_search_roots():
    return ["/local_models", "/runpod-volume/models", "/runpod-volume", "/workspace/models"]


def find_model_file(subfolder, predicates, fallback_ext=(".safetensors",)):
    for vol in model_search_roots():
        path = os.path.join(vol, subfolder)
        if not os.path.isdir(path):
            continue
        files = [f for f in os.listdir(path) if f.endswith(fallback_ext)]
        matches = [f for f in files if all(p(f) for p in predicates)]
        if matches:
            return sorted(matches)[0], vol
    return None, None


def detect_models(prefer_i2v=False):
    """Auto-detect T2V/I2V/T5/VAE/CLIP/UltraSharp filenames on volume/SSD."""
    if prefer_i2v:
        diffusion, dvol = find_model_file(
            "diffusion_models",
            [
                lambda f: "i2v" in f.lower(),
                lambda f: "14b" in f.lower(),
                lambda f: "fp8" in f.lower(),
                lambda f: "480" in f.lower() or "480p" in f.lower(),
            ],
        )
        if not diffusion:
            diffusion, dvol = find_model_file(
                "diffusion_models",
                [
                    lambda f: "i2v" in f.lower(),
                    lambda f: "14b" in f.lower(),
                    lambda f: "fp8" in f.lower(),
                ],
            )
    else:
        diffusion, dvol = find_model_file(
            "diffusion_models",
            [
                lambda f: "t2v" in f.lower(),
                lambda f: "14b" in f.lower(),
                lambda f: "fp8" in f.lower(),
            ],
        )
        if not diffusion:
            diffusion, dvol = find_model_file(
                "diffusion_models",
                [
                    lambda f: ("wan2_1" in f.lower() or "wan2.1" in f.lower()),
                    lambda f: "14b" in f.lower(),
                    lambda f: "fp8" in f.lower(),
                    lambda f: "i2v" not in f.lower(),
                ],
            )

    text_encoder, _ = find_model_file(
        "text_encoders",
        [lambda f: "umt5" in f.lower()],
    )
    vae, _ = find_model_file(
        "vae",
        [lambda f: "vae" in f.lower()],
    )
    clip_vision, _ = find_model_file(
        "clip_vision",
        [lambda f: "open-clip" in f.lower() or "clip" in f.lower() or "visual" in f.lower()],
    )
    upscale, _ = find_model_file(
        "upscale_models",
        [lambda f: "ultrasharp" in f.lower() or f.endswith(".pth")],
        fallback_ext=(".pth", ".safetensors"),
    )

    if diffusion and dvol:
        print(f"🎯 Auto-detected {'I2V' if prefer_i2v else 'T2V'} model from {dvol}: {diffusion}")

    return {
        "diffusion": diffusion,
        "text_encoder": text_encoder,
        "vae": vae,
        "clip_vision": clip_vision,
        "upscale": upscale,
    }


def patch_common_workflow(workflow, prompt_text, models, use_sage, force_offload):
    """Apply prompt / model / VRAM / attention patches shared by T2V and I2V graphs."""
    for node in workflow.values():
        class_type = node.get("class_type")

        if node.get("_meta", {}).get("title") == "Positive Prompt" or class_type in [
            "WanVideoTextEncode",
            "WanVideoTextEncodeCached",
        ]:
            if "positive_prompt" in node["inputs"]:
                node["inputs"]["positive_prompt"] = prompt_text
            elif "text" in node["inputs"]:
                node["inputs"]["text"] = prompt_text
            if models["text_encoder"] and "model_name" in node["inputs"]:
                node["inputs"]["model_name"] = models["text_encoder"]
            if "quantization" in node["inputs"]:
                node["inputs"]["quantization"] = "disabled"
            node["inputs"]["use_disk_cache"] = True

        if class_type == "WanVideoModelLoader":
            if models["diffusion"]:
                node["inputs"]["model"] = models["diffusion"]
            node["inputs"]["attention_mode"] = "sageattn" if use_sage else "sdpa"
            node["inputs"]["load_device"] = "offload_device" if force_offload else "main_device"

        if class_type in ("WanVideoEmptyEmbeds", "WanVideoImageToVideoEncode") and "num_frames" in node["inputs"]:
            requested = int(node["inputs"]["num_frames"])
            fixed = nearest_valid_frames(requested)
            if fixed != requested:
                print(f"⚠️ num_frames {requested} invalid for Wan VAE; snapping to {fixed} (4k+1)")
            node["inputs"]["num_frames"] = fixed

        if class_type == "WanVideoSampler":
            node["inputs"]["force_offload"] = force_offload

        if class_type == "WanVideoVAELoader" and models["vae"]:
            node["inputs"]["model_name"] = models["vae"]

        if class_type == "CLIPVisionLoader" and models["clip_vision"]:
            node["inputs"]["clip_name"] = models["clip_vision"]

        if class_type == "UpscaleModelLoader" and models["upscale"]:
            node["inputs"]["model_name"] = models["upscale"]

    return workflow


def submit_and_wait(workflow, timeout_s=1200):
    """Queue a ComfyUI prompt and return the first output video filename."""
    try:
        requests.post(f"{COMFY_URL}/refresh_custom_nodes", headers=COMFY_HEADERS, timeout=2)
    except Exception:
        pass

    res_raw = requests.post(
        f"{COMFY_URL}/prompt",
        json={"prompt": workflow},
        headers=COMFY_HEADERS,
        timeout=60,
    )
    if res_raw.status_code != 200:
        raise RuntimeError(f"ComfyUI Validation Error: {res_raw.text}")

    prompt_id = res_raw.json()["prompt_id"]
    start_poll = time.time()
    while True:
        if time.time() - start_poll > timeout_s:
            raise TimeoutError(f"Generation timed out after {timeout_s}s")

        time.sleep(5)
        try:
            hist_res = requests.get(
                f"{COMFY_URL}/history/{prompt_id}",
                headers=COMFY_HEADERS,
                timeout=5,
            )
            history = hist_res.json()
            if prompt_id not in history:
                continue

            status = history[prompt_id].get("status", {})
            for msg in status.get("messages", []):
                if msg[0] == "execution_error":
                    raise RuntimeError(f"ComfyUI Execution Error: {msg[1]}")

            outputs = history[prompt_id].get("outputs", {})
            for node_output in outputs.values():
                for key in ("gifs", "videos", "images"):
                    if key in node_output and node_output[key]:
                        filename = node_output[key][0].get("filename")
                        if filename and filename.lower().endswith((".mp4", ".webm", ".gif")):
                            return filename
        except (TimeoutError, RuntimeError):
            raise
        except Exception as e:
            print(f"⚠️ Polling error: {e}")


def extract_last_frame(video_path, png_path):
    """Grab the last frame of a chunk for I2V continuation."""
    os.makedirs(os.path.dirname(png_path), exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-sseof",
            "-0.1",
            "-i",
            video_path,
            "-frames:v",
            "1",
            "-q:v",
            "2",
            png_path,
        ],
        check=True,
        capture_output=True,
    )
    if not os.path.isfile(png_path):
        raise RuntimeError(f"Failed to extract last frame from {video_path}")


def stitch_continuous_chunks(chunk_paths, output_path, fps=16):
    """Concat chunks, dropping the duplicate first frame of each continuation."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if len(chunk_paths) == 1:
        shutil.copy2(chunk_paths[0], output_path)
        return

    inputs = []
    filter_parts = []
    for i, path in enumerate(chunk_paths):
        inputs.extend(["-i", path])
        if i == 0:
            filter_parts.append(f"[{i}:v]setpts=PTS-STARTPTS[v{i}]")
        else:
            filter_parts.append(f"[{i}:v]select='gte(n\\,1)',setpts=N/{fps}/TB[v{i}]")

    concat_inputs = "".join(f"[v{i}]" for i in range(len(chunk_paths)))
    filter_parts.append(f"{concat_inputs}concat=n={len(chunk_paths)}:v=1:a=0[outv]")
    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg",
        "-y",
        *inputs,
        "-filter_complex",
        filter_complex,
        "-map",
        "[outv]",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "18",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def maybe_scale_to_shorts(src_path, dst_path):
    """Fast lanczos upscale to 1080x1920 for continuous smoke tests (no UltraSharp)."""
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            src_path,
            "-vf",
            "scale=1080:1920:flags=lanczos",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "18",
            dst_path,
        ],
        check=True,
        capture_output=True,
    )


def upload_to_r2(local_file_path, r2_key):
    print(
        f"☁️ Uploading {os.path.basename(local_file_path)} to Cloudflare R2... "
        f"(Size: {os.path.getsize(local_file_path)} bytes)"
    )
    s3.upload_file(local_file_path, os.getenv("R2_BUCKET_NAME"), r2_key)
    return f"{os.getenv('R2_PUBLIC_URL_PREFIX')}/{r2_key}"


def execute_multi_cut(job_id, prompt_text, video_id, shot_index):
    """Original single-clip T2V path with UltraSharp 1080p."""
    with open("/workspace/workflow_api.json", "r") as f:
        workflow = json.load(f)

    models = detect_models(prefer_i2v=False)
    use_sage = sageattn_available()
    vram_gb = detect_vram_gb()
    force_offload = should_force_offload(vram_gb)
    print(
        f"🖥️ VRAM≈{vram_gb:.0f}GB | force_offload={force_offload} | "
        f"attention={'sageattn' if use_sage else 'sdpa'}"
    )

    workflow = patch_common_workflow(workflow, prompt_text, models, use_sage, force_offload)
    output_filename = submit_and_wait(workflow, timeout_s=1200)
    local_file_path = os.path.join(OUTPUT_DIR, output_filename)
    r2_key = f"renders/{video_id}/shot_{shot_index}.mp4"
    r2_public_url = upload_to_r2(local_file_path, r2_key)
    if os.path.exists(local_file_path):
        os.remove(local_file_path)

    jobs[job_id]["status"] = "completed"
    jobs[job_id]["output_r2_url"] = r2_public_url
    jobs[job_id]["shot_mode"] = "multi_cut"


def execute_continuous(job_id, prompt_text, video_id, shot_index, chunks=2, upscale=True):
    """
    Generate a continuous take by chaining T2V -> I2V(last frame) chunks.
    Default chunks=2 ≈ ~10s at 16fps (81 frames each, minus 1-frame overlap).
    """
    chunks = max(1, int(chunks))
    work_dir = os.path.join(WORK_DIR, job_id)
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(INPUT_DIR, exist_ok=True)

    use_sage = sageattn_available()
    vram_gb = detect_vram_gb()
    force_offload = should_force_offload(vram_gb)
    print(
        f"🎬 Continuous mode | chunks={chunks} (~{chunks * 5:.0f}s) | "
        f"VRAM≈{vram_gb:.0f}GB | force_offload={force_offload} | "
        f"attention={'sageattn' if use_sage else 'sdpa'}"
    )

    chunk_paths = []
    for i in range(chunks):
        jobs[job_id]["progress"] = f"chunk_{i + 1}/{chunks}"
        print(f"🎞️ Continuous chunk {i + 1}/{chunks}...")

        if i == 0:
            with open("/workspace/workflow_t2v_chunk.json", "r") as f:
                workflow = json.load(f)
            models = detect_models(prefer_i2v=False)
            workflow = patch_common_workflow(
                workflow, prompt_text, models, use_sage, force_offload
            )
        else:
            with open("/workspace/workflow_i2v_api.json", "r") as f:
                workflow = json.load(f)
            models = detect_models(prefer_i2v=True)
            if not models["diffusion"]:
                raise RuntimeError(
                    "I2V model not found — setup.py should download Wan2_1-I2V-14B-480P FP8"
                )
            if not models["clip_vision"]:
                raise RuntimeError(
                    "CLIP vision model not found — required for I2V continuation"
                )

            start_name = f"cont_{job_id}_chunk{i}.png"
            start_path = os.path.join(INPUT_DIR, start_name)
            extract_last_frame(chunk_paths[-1], start_path)

            workflow = patch_common_workflow(
                workflow, prompt_text, models, use_sage, force_offload
            )
            for node in workflow.values():
                if node.get("class_type") == "LoadImage":
                    node["inputs"]["image"] = start_name

        for node in workflow.values():
            if node.get("class_type") == "WanVideoSampler" and "seed" in node["inputs"]:
                node["inputs"]["seed"] = int(node["inputs"]["seed"]) + i

        output_filename = submit_and_wait(workflow, timeout_s=1500)
        src = os.path.join(OUTPUT_DIR, output_filename)
        dst = os.path.join(work_dir, f"chunk_{i + 1:02d}.mp4")
        shutil.move(src, dst)
        chunk_paths.append(dst)
        print(f"✅ Chunk {i + 1} saved: {dst}")

    stitched = os.path.join(work_dir, "stitched_480p.mp4")
    stitch_continuous_chunks(chunk_paths, stitched)
    print(f"🔗 Stitched continuous clip: {stitched}")

    final_path = stitched
    if upscale:
        scaled = os.path.join(work_dir, "continuous_1080p.mp4")
        maybe_scale_to_shorts(stitched, scaled)
        final_path = scaled
        print(f"⬆️ Scaled continuous clip to 1080x1920: {scaled}")

    r2_key = f"renders/{video_id}/continuous.mp4"
    r2_public_url = upload_to_r2(final_path, r2_key)

    try:
        shutil.rmtree(work_dir, ignore_errors=True)
    except Exception:
        pass

    jobs[job_id]["status"] = "completed"
    jobs[job_id]["output_r2_url"] = r2_public_url
    jobs[job_id]["shot_mode"] = "continuous"
    jobs[job_id]["chunks"] = chunks


def execute_render_async(
    job_id,
    prompt_text,
    video_id,
    shot_index,
    shot_mode="multi_cut",
    chunks=2,
    upscale=True,
):
    try:
        jobs[job_id]["status"] = "processing"
        mode = (shot_mode or "multi_cut").lower().strip()
        if mode in ("continuous", "single_shot", "singleshot"):
            execute_continuous(
                job_id,
                prompt_text,
                video_id,
                shot_index,
                chunks=chunks,
                upscale=upscale,
            )
        else:
            execute_multi_cut(job_id, prompt_text, video_id, shot_index)
    except Exception as e:
        import traceback

        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"💥 Execution Error: {error_msg}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = error_msg


@app.route("/", methods=["GET"])
def index():
    return jsonify({"service": "niche-video-worker", "status": "online"})


@app.route("/health", methods=["GET"])
def health_check():
    diag = {}
    for p in [
        "/local_models",
        "/runpod-volume",
        "/workspace/models",
        "/comfyui/models/diffusion_models",
        "/comfyui/models/upscale_models",
        "/comfyui/models/clip_vision",
    ]:
        if os.path.exists(p):
            diag[p] = {"exists": True, "files": os.listdir(p)[:8]}
        else:
            diag[p] = {"exists": False}

    setup_log = ""
    if os.path.exists("/workspace/setup.log"):
        with open("/workspace/setup.log", "r") as f:
            setup_log = f.read()

    return jsonify(
        {
            "status": "ready",
            "diagnostics": diag,
            "setup_log": setup_log,
            "vram_gb": detect_vram_gb(),
            "force_offload": should_force_offload(),
            "modes": ["multi_cut", "continuous"],
        }
    )


@app.route("/prompt", methods=["POST"])
def handle_prompt():
    data = request.json or {}
    job_id = str(uuid.uuid4())
    shot_mode = data.get("shot_mode", "multi_cut")
    chunks = int(data.get("chunks", 2))
    upscale = bool(data.get("upscale", True))

    jobs[job_id] = {
        "status": "queued",
        "video_id": data.get("video_id"),
        "shot_index": data.get("shot_index"),
        "shot_mode": shot_mode,
        "chunks": chunks,
        "created_at": time.time(),
    }

    thread = threading.Thread(
        target=execute_render_async,
        args=(
            job_id,
            data.get("prompt"),
            data.get("video_id"),
            data.get("shot_index"),
            shot_mode,
            chunks,
            upscale,
        ),
    )
    thread.start()

    return jsonify(
        {"job_id": job_id, "status": "queued", "shot_mode": shot_mode, "chunks": chunks}
    )


@app.route("/status/<job_id>", methods=["GET"])
def get_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


if __name__ == "__main__":
    wait_for_comfyui()
    app.run(host="0.0.0.0", port=8000)
