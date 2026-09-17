FROM nvidia/cuda:13.3.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /workspace

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git python3 python3-pip ffmpeg wget curl libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Torch nightly cu130 first (Blackwell) — install once to avoid double-download disk spikes
RUN pip3 install --no-cache-dir --pre --upgrade pip \
    && pip3 install --no-cache-dir --pre torch torchvision torchaudio \
        --index-url https://download.pytorch.org/whl/nightly/cu130 \
    && rm -rf /root/.cache/pip

# ComfyUI core (≥0.32 for native LTX-2.5). Skip reinstalling torch from requirements.
RUN git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git /comfyui \
    && grep -viE '^(torch|torchvision|torchaudio)([=<>]|$)' /comfyui/requirements.txt \
        > /tmp/comfy-req.txt \
    && pip3 install --no-cache-dir -r /tmp/comfy-req.txt \
    && pip3 install --no-cache-dir \
        accelerate transformers sentencepiece einops tqdm \
        opencv-python-headless triton sageattention \
    && rm -rf /root/.cache/pip /tmp/comfy-req.txt

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt \
    && rm -rf /root/.cache/pip

COPY handler.py /workspace/handler.py
COPY setup.py /workspace/setup.py
COPY workflow_ltx_t2v.json /workspace/workflow_ltx_t2v.json
COPY extra_model_paths.yaml /comfyui/extra_model_paths.yaml

# Late layer: Triton/Gemma4 TE JIT needs a host C compiler (keeps torch layers cached)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential python3-dev \
    && rm -rf /var/lib/apt/lists/*
ENV CC=gcc CXX=g++

ENV ENGINE=ltx

EXPOSE 8000

CMD ["bash", "-c", "python3 /workspace/setup.py && python3 /comfyui/main.py --listen 0.0.0.0 --port 8188 --dont-upcast-attention --reserve-vram 2 & sleep 5 && python3 -u /workspace/handler.py"]
