FROM nvidia/cuda:13.3.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /workspace

# System dependencies
RUN apt-get update && apt-get install -y \
    git python3 python3-pip ffmpeg wget curl libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Install ComfyUI Core (needs ≥0.32 for native LTX-2.5 nodes)
RUN git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git /comfyui
RUN pip3 install --no-cache-dir -r /comfyui/requirements.txt

# VideoHelperSuite kept for optional VHS nodes; core SaveVideo/CreateVideo is enough for LTX
RUN git clone --depth 1 https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git /comfyui/custom_nodes/ComfyUI-VideoHelperSuite
RUN pip3 install --no-cache-dir -r /comfyui/custom_nodes/ComfyUI-VideoHelperSuite/requirements.txt

RUN pip3 install --no-cache-dir \
    diffusers accelerate transformers sentencepiece einops tqdm \
    opencv-python-headless triton

# SageAttention for speedup on Blackwell/Ada GPUs
RUN pip3 install --no-cache-dir sageattention

# Force PyTorch nightly cu130 for Blackwell
RUN pip3 install --no-cache-dir --pre --upgrade torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/nightly/cu130

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY handler.py /workspace/handler.py
COPY setup.py /workspace/setup.py
COPY workflow_ltx_t2v.json /workspace/workflow_ltx_t2v.json
COPY extra_model_paths.yaml /comfyui/extra_model_paths.yaml

# Single engine: LTX-2.5
ENV ENGINE=ltx

EXPOSE 8000

# Gemma TE can sit on CPU on 32GB; PRO 6000 keeps it on GPU via LTX_TE_DEVICE=default
CMD ["bash", "-c", "python3 /workspace/setup.py && python3 /comfyui/main.py --listen 0.0.0.0 --port 8188 --dont-upcast-attention --reserve-vram 2 & sleep 5 && python3 -u /workspace/handler.py"]
