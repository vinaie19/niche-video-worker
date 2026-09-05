FROM nvidia/cuda:13.3.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /workspace

# System dependencies
RUN apt-get update && apt-get install -y \
    git python3 python3-pip ffmpeg wget curl libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Install ComfyUI Core
RUN git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git /comfyui
RUN pip3 install --no-cache-dir -r /comfyui/requirements.txt

# Install VideoHelperSuite (VHS) for MP4 combining
RUN git clone --depth 1 https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git /comfyui/custom_nodes/ComfyUI-VideoHelperSuite
RUN pip3 install --no-cache-dir -r /comfyui/custom_nodes/ComfyUI-VideoHelperSuite/requirements.txt

# Install Wan 2.1 Custom Nodes
RUN git clone --depth 1 https://github.com/kijai/ComfyUI-WanVideoWrapper.git /comfyui/custom_nodes/ComfyUI-WanVideoWrapper
RUN pip3 install --no-cache-dir -r /comfyui/custom_nodes/ComfyUI-WanVideoWrapper/requirements.txt

# Explicitly install Wan 2.1 and VHS dependencies
# opencv-python-headless is required for VHS to work in a container without X11
RUN pip3 install --no-cache-dir diffusers accelerate transformers sentencepiece einops tqdm opencv-python-headless triton

# Install SageAttention for 2x-3x speedup on Blackwell/Ada GPUs
RUN pip3 install --no-cache-dir sageattention

# FINAL STEP: Force PyTorch 2.14.0+ with CUDA 13.0 support for Blackwell (RTX 5090)
# We use the nightly cu130 index to ensure torch and torchaudio are perfectly synced on CUDA 13
RUN pip3 install --no-cache-dir --pre --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu130

# Copy repository config & runner code
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY handler.py /workspace/handler.py
COPY setup.py /workspace/setup.py
COPY workflow_api.json /workspace/workflow_api.json
COPY extra_model_paths.yaml /comfyui/extra_model_paths.yaml

EXPOSE 8000

# Boot internal ComfyUI server, wait 5s for VRAM init, then launch execution Flask worker
CMD ["bash", "-c", "python3 /workspace/setup.py && python3 /comfyui/main.py --listen 0.0.0.0 --port 8188 --highvram & sleep 5 && python3 -u /workspace/handler.py"]
