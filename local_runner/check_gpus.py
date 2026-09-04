import runpod
import os
from dotenv import load_dotenv

load_dotenv()
runpod.api_key = os.getenv("RUNPOD_API_KEY")

try:
    gpus = runpod.get_gpus()
    print("Available GPUs:")
    for gpu in gpus:
        print(f"ID: {gpu['id']}, Name: {gpu['displayName']}")
except Exception as e:
    print(f"Error fetching GPUs: {e}")
