FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

WORKDIR /workspace

RUN apt-get update && apt-get install -y git python3 python3-pip ffmpeg && rm -rf /var/lib/apt/lists/*

# Install ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /comfyui
RUN pip3 install -r /comfyui/requirements.txt

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY handler.py .
COPY workflow_api.json .

# Start ComfyUI in background, then run the RunPod handler
CMD ["bash", "-c", "python3 /comfyui/main.py --listen 127.0.0.1 --port 8188 & python3 -u handler.py"]
