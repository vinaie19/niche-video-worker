"""Tiny Runpod REST API v2 client (key from local_runner/.env, never printed)."""
import os
import sys
import json

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
BASE = "https://api.runpod.io"
H = {"Authorization": f"Bearer {os.environ['RUNPOD_API_KEY']}", "Content-Type": "application/json"}


def call(method, path, body=None, params=None):
    r = requests.request(method, BASE + path, headers=H, json=body, params=params, timeout=60)
    try:
        data = r.json()
    except ValueError:
        data = r.text
    return r.status_code, data


if __name__ == "__main__":  # python runpod_v2.py GET /v2/global-volumes ['{"json":"body"}']
    m, p = sys.argv[1], sys.argv[2]
    body = json.loads(sys.argv[3]) if len(sys.argv) > 3 else None
    code, data = call(m, p, body)
    print(code); print(json.dumps(data, indent=1)[:6000])
