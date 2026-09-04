FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /workspace

# System dependencies
RUN apt-get update && apt-get install -y \
    git python3 python3-pip ffmpeg wget curl \
    && rm -rf /var/lib/apt/lists/*

# Install ComfyUI Core
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /comfyui

# Standard PyTorch install (usually cu121 or cu124 but with better driver fallback)
RUN pip3 install --no-cache-dir torch torchvision torchaudio

RUN pip3 install --no-cache-dir -r /comfyui/requirements.txt

# Install VideoHelperSuite (VHS) for MP4 combining
RUN git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git /comfyui/custom_nodes/ComfyUI-VideoHelperSuite
RUN pip3 install --no-cache-dir -r /comfyui/custom_nodes/ComfyUI-VideoHelperSuite/requirements.txt

# Install Wan 2.1 Custom Nodes
RUN git clone https://github.com/kijai/ComfyUI-WanVideo.git /comfyui/custom_nodes/ComfyUI-WanVideo
RUN pip3 install --no-cache-dir -r /comfyui/custom_nodes/ComfyUI-WanVideo/requirements.txt

# Copy repository config & runner code
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY handler.py /workspace/handler.py
COPY workflow_api.json /workspace/workflow_api.json
COPY extra_model_paths.yaml /comfyui/extra_model_paths.yaml

EXPOSE 8000

# Boot internal ComfyUI server, wait 5s for VRAM init, then launch execution Flask worker
CMD ["bash", "-c", "python3 /comfyui/main.py --listen 0.0.0.0 --port 8188 & sleep 5 && python3 -u /workspace/handler.py"]
